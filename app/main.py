from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import logging
import re
from app.db import Base, engine
from app.models import EmotionalState, RelationshipState

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.memory import remember_fact, get_user_facts
from app.long_memory import save_memory, search_memory
from app.sentiment import detect_tone
from app.thread_manager import get_or_create_thread, run_assistant_with_thread, get_or_create_assistant
from app.update_vector import update_vector_store
from app.mode_manager import check_and_switch_mode
from app.meeting_manager import create_meeting, get_user_meetings, delete_meeting
from app.scheduler import start_scheduler, stop_scheduler
from app.meeting_extractor import extract_meeting_from_reply

from app.scoring import score_response
from app.persona_manager import inject_persona_context
from app.emotions import adjust_emotions
from app.relationship import update_relationship
from app.story_engine import generate_story_event, save_story, get_story_context

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Запуск планировщика при старте
@app.on_event("startup")
def startup_event():
    logger.info("=== Запуск приложения ===")
    start_scheduler()

# Остановка планировщика при завершении
@app.on_event("shutdown")
def shutdown_event():
    logger.info("=== Остановка приложения ===")
    stop_scheduler()


# Mount static files
app.mount("/static", StaticFiles(directory="web"), name="static")

@app.get("/")
async def read_root():
    return FileResponse("web/index.html")

class ChatRequest(BaseModel):
    user_id: str
    message: str
    history: list = []  # История последних сообщений

@app.post("/chat")
def chat(req: ChatRequest):
    logger.info(f"=== Новый запрос от user_id={req.user_id} ===")
    logger.info(f"Сообщение: {req.message}")

    try:
        # 0. Проверка кодовой фразы для переключения режима
        logger.info("Шаг 0: Проверка режима...")
        current_mode, mode_switched = check_and_switch_mode(req.user_id, req.message)
        logger.info(f"Текущий режим: {current_mode}, Переключение: {mode_switched}")
        
        if mode_switched:
            mode_name = "секретаря" if current_mode == "secretary" else "общения"
            return {
                "reply": f"Хорошо, переключаюсь в режим {mode_name}.",
                "mode": current_mode,
                "mode_switched": True
            }
        # 1. Обработать эмоции
        logger.info("Шаг 1: Обработка эмоций...")
        emo_dict = adjust_emotions(req.user_id, req.message)
        logger.info(f"Эмоции получены: calm={emo_dict['calm']}, joy={emo_dict['joy']}")

        # 2. Обновить отношения
        logger.info("Шаг 2: Обновление отношений...")
        rel_dict = update_relationship(req.user_id, req.message)
        logger.info(f"Отношения обновлены: trust={rel_dict['trust']}, closeness={rel_dict['closeness']}")

        # 3. Сгенерировать историю Светланы (редко, только иногда)
        import random
        story = None
        if random.random() < 0.2:  # 20% шанс генерации истории
            logger.info("Шаг 3: Генерация истории...")
            story = generate_story_event(emo_dict, rel_dict)
            logger.info(f"История сгенерирована: {story}")
            save_story(req.user_id, story)
        else:
            logger.info("Шаг 3: История не генерируется (редкий случай)")

        # 4. Вытянуть события истории
        logger.info("Шаг 4: Загрузка истории...")
        stories = get_story_context(req.user_id)
        logger.info(f"Загружено {len(stories)} историй")

        # 5. Память и остальные компоненты
        logger.info("Шаг 5: Работа с памятью...")
        save_memory(req.user_id, req.message)
        memory_hits = search_memory(req.user_id, req.message)
        facts = get_user_facts(req.user_id)
        logger.info(f"Найдено {len(memory_hits)} воспоминаний, {len(facts)} фактов")

        # 6. Определение тона
        logger.info("Шаг 6: Определение тона...")
        tone = detect_tone(req.message)
        logger.info(f"Тон: {tone}")

        # 7. Формирование контекста с историей сообщений
        logger.info("Шаг 7: Формирование контекста...")
        logger.info(f"Полученная история: {req.history}")
        history_context = ""
        if req.history:
            last_messages = req.history[-6:]  # Последние 6 сообщений
            history_context = "\nПоследние сообщения:\n" + "\n".join([f"- {msg.get('role', 'user')}: {msg.get('text', '')}" for msg in last_messages])
            logger.info(f"Сформирован контекст истории: {history_context}")
        else:
            logger.info("История пустая")

        system_context = inject_persona_context(
            tone=tone,
            memories=memory_hits,
            facts=facts,
            emotions=emo_dict,
            relationships=rel_dict,
            stories=stories,
            history=history_context,
            mode=current_mode
        )

        # 8. Генерация ответа через Thread API
        logger.info("Шаг 8: Генерация ответа через Thread API...")
        thread_id = get_or_create_thread(req.user_id)
        reply = run_assistant_with_thread(req.message, system_context, thread_id, mode=current_mode)
        logger.info(f"Ответ получен: {reply[:100]}...")

        # 8.5. Проверка на создание встречи (только в режиме секретаря)
        meeting_created = None
        if current_mode == "secretary":
            logger.info("Шаг 8.5: Проверка на создание встречи...")
            meeting_data = extract_meeting_from_reply(reply)
            if meeting_data:
                try:
                    created_meeting = create_meeting(
                        req.user_id,
                        meeting_data['title'],
                        meeting_data['datetime'],
                        meeting_data.get('location', ''),
                        meeting_data.get('description', '')
                    )
                    meeting_created = created_meeting
                    logger.info(f"[Meeting] Встреча создана из ответа: {created_meeting['title']}")
                    
                    # Убираем блок [MEETING] из ответа для пользователя
                    reply = re.sub(r'\[MEETING\].*?\[/MEETING\]', '', reply, flags=re.DOTALL).strip()
                    reply += "\n\n✅ Встреча записана в календарь!"
                except Exception as e:
                    logger.error(f"[Meeting] Ошибка создания встречи: {e}")

        # 9. Оценка ответа
        logger.info("Шаг 9: Оценка ответа...")
        score = score_response(req.message, reply)
        logger.info(f"Оценка: {score}")

        if score > 7:
            remember_fact(req.user_id, f"Пользователь любит такой стиль: {reply[:50]}")

        logger.info("=== Запрос успешно обработан ===")
        return {
            "reply": reply,
            "score": score,
            "emotion": emo_dict,
            "relationship": rel_dict,
            "story": story,
            "mode": current_mode,
            "meeting_created": meeting_created
        }
    except Exception as e:
        logger.error(f"!!! ОШИБКА в обработке запроса: {str(e)}")
        logger.error(f"Тип ошибки: {type(e).__name__}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "reply": "Извините, произошла ошибка при обработке вашего сообщения.",
            "error": str(e)
        }

@app.post("/update-vector")
def update_vector():
    """Ручное обновление vector store"""
    logger.info("=== Запрос на обновление vector store ===")
    result = update_vector_store()
    return result

@app.post("/recreate-assistant")
def recreate_assistant():
    """Принудительное пересоздание ассистента с новой инструкцией"""
    logger.info("=== Принудительное пересоздание ассистента ===")
    assistant_id = get_or_create_assistant(force_recreate=True)
    return {"status": "success", "assistant_id": assistant_id}

class MeetingRequest(BaseModel):
    user_id: str
    title: str
    datetime: str
    location: str = ""
    description: str = ""

@app.post("/meetings")
def create_meeting_endpoint(req: MeetingRequest):
    """Создаёт встречу"""
    logger.info(f"=== Создание встречи: {req.title} ===")
    try:
        meeting = create_meeting(req.user_id, req.title, req.datetime, req.location, req.description)
        return {"status": "success", "meeting": meeting}
    except Exception as e:
        logger.error(f"Ошибка создания встречи: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/meetings/{user_id}")
def get_meetings(user_id: str):
    """Получает встречи пользователя"""
    logger.info(f"=== Получение встреч для {user_id} ===")
    meetings = get_user_meetings(user_id)
    return {"meetings": meetings}

@app.delete("/meetings/{meeting_id}")
def delete_meeting_endpoint(meeting_id: int):
    """Удаляет встречу"""
    logger.info(f"=== Удаление встречи {meeting_id} ===")
    success = delete_meeting(meeting_id)
    return {"status": "success" if success else "error"}

@app.post("/test-telegram")
def test_telegram():
    """Тестирует отправку сообщения в Telegram"""
    from app.telegram_bot import send_meeting_reminder
    logger.info("=== Тест отправки в Telegram ===")
    success = send_meeting_reminder("Test Meeting", "2026-04-23 14:00", "Office")
    return {"status": "success" if success else "error"}

@app.post("/recreate-secretary")
def recreate_secretary():
    """Пересоздаёт ассистента для режима секретаря с новой инструкцией"""
    logger.info("=== Пересоздание ассистента секретаря ===")
    assistant_id = get_or_create_assistant(mode="secretary", force_recreate=True)
    return {"status": "success", "assistant_id": assistant_id}

