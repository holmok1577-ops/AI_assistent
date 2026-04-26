from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import logging
import re
from app.db import Base, engine
from app.models import EmotionalState, RelationshipState

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.memory import extract_user_name, get_user_facts, get_user_name, remember_fact, save_user_name
from app.long_memory import save_memory, search_memory
from app.sentiment import detect_tone
from app.thread_manager import get_or_create_thread, run_assistant_with_thread, get_or_create_assistant
from app.update_vector import update_vector_store
from app.mode_manager import check_and_switch_mode
from app.meeting_manager import create_meeting, get_user_meetings, delete_meeting
from app.scheduler import start_scheduler, stop_scheduler
from app.meeting_extractor import extract_meeting_from_reply, resolve_meeting_datetime

from app.scoring import score_response
from app.persona_manager import inject_persona_context
from app.emotions import adjust_emotions
from app.relationship import update_relationship
from app.story_engine import generate_story_event, save_story, get_story_context
from app.conversation_manager import get_conversation_state, increment_message_count, mark_introduced, update_topic_state
from app.dialogue_policy import build_dialogue_guidance
from app.response_guard import refine_reply
from app.affect_memory import build_affect_guidance, record_and_get_affect_profile
from app.conversation_journal import build_temporal_context, record_conversation_event
from app.meeting_extractor import get_moscow_now

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
    history: list = Field(default_factory=list)  # История последних сообщений

@app.post("/chat")
def chat(req: ChatRequest):
    logger.info(f"=== Новый запрос от user_id={req.user_id} ===")
    logger.info(f"Сообщение: {req.message}")

    try:
        now_msk = get_moscow_now()

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
        # 0.5 Определение тона и накопленного эмоционального фона
        logger.info("Шаг 0.5: Определение тона и эмоционального фона...")
        tone = detect_tone(req.message)
        affect_profile = record_and_get_affect_profile(req.user_id, tone, req.message)
        affect_guidance = build_affect_guidance(affect_profile)
        logger.info(
            "Тон=%s hostile_recent=%s positive_recent=%s playful_recent=%s",
            tone,
            affect_profile.get("hostile_recent", 0),
            affect_profile.get("positive_recent", 0),
            affect_profile.get("playful_recent", 0),
        )

        # 1. Обработать эмоции
        logger.info("Шаг 1: Обработка эмоций...")
        emo_dict = adjust_emotions(req.user_id, req.message, tone=tone, affect_profile=affect_profile)
        logger.info(f"Эмоции получены: calm={emo_dict['calm']}, joy={emo_dict['joy']}")

        # 2. Обновить отношения
        logger.info("Шаг 2: Обновление отношений...")
        rel_dict = update_relationship(req.user_id, req.message, tone=tone, affect_profile=affect_profile)
        logger.info(f"Отношения обновлены: trust={rel_dict['trust']}, closeness={rel_dict['closeness']}")

        # 2.1. Проверка на блокировку
        logger.info("Шаг 2.1: Проверка блокировки...")
        from app.db import SessionLocal
        from app.models import EmotionalState
        db = SessionLocal()
        emo_check = db.query(EmotionalState).filter_by(user_id=req.user_id).first()
        is_blocked = emo_check.is_blocked if emo_check else False
        first_extreme = emo_check.first_extreme_response if emo_check else False
        logger.info(f"Статус блокировки: {is_blocked}, Первый грубый ответ: {first_extreme}")

        # Если заблокирован - не отвечаем
        if is_blocked:
            db.close()
            logger.info("=== Пользователь заблокирован, ответ не генерируется ===")
            return {
                "reply": "",  # Пустой ответ
                "is_blocked": True,
                "status": "offline",
                "emotion": emo_dict,
                "relationship": rel_dict,
                "mode": current_mode
            }

        # Если это первый грубый ответ - меняем статус на offline после ответа
        should_go_offline = first_extreme and not is_blocked
        
        # Если параметры восстановились (не extreme) - сбрасываем флаг
        if not first_extreme and emo_check and emo_check.first_extreme_response:
            emo_check.first_extreme_response = False
            db.commit()
            logger.info(f"[STATUS] Параметры восстановлены, статус online")
        
        db.close()

        # 2.5. Управление состоянием диалога
        logger.info("Шаг 2.5: Управление состоянием диалога...")
        conv_state = get_conversation_state(req.user_id)
        message_count = increment_message_count(req.user_id)
        logger.info(f"Счётчик сообщений: {message_count}, Знакомство: {conv_state.introduced}")
        
        # Если это первые сообщения и ещё не познакомились - отмечаем знакомство
        if message_count <= 3 and not conv_state.introduced:
            mark_introduced(req.user_id)
            logger.info("Знакомство отмечено")

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
        detected_name = extract_user_name(req.message)
        if detected_name:
            save_user_name(req.user_id, detected_name)
            logger.info(f"Определено имя пользователя: {detected_name}")
        save_memory(req.user_id, req.message)
        memory_hits = search_memory(req.user_id, req.message)
        facts = get_user_facts(req.user_id)
        user_name = get_user_name(req.user_id) or ""
        temporal_context = build_temporal_context(req.user_id, req.message, now=now_msk)
        logger.info(f"Найдено {len(memory_hits)} воспоминаний, {len(facts)} фактов")

        logger.info("Шаг 6: Анализ динамики диалога...")
        dialogue_plan = build_dialogue_guidance(
            user_message=req.message,
            history=req.history,
            message_count=message_count,
            introduced=conv_state.introduced
        )
        update_topic_state(req.user_id, dialogue_plan["current_topic"])
        logger.info(
            "План диалога: topic=%s depth=%s change_topic=%s",
            dialogue_plan["current_topic"],
            dialogue_plan["user_depth"],
            dialogue_plan["should_change_topic"]
        )

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
            mode=current_mode,
            message_count=message_count,
            introduced=conv_state.introduced,
            dialogue_guidance=dialogue_plan["guidance_text"],
            affect_guidance=affect_guidance,
            affect_profile=affect_profile,
            user_name=user_name,
            temporal_context=temporal_context
        )

        # 8. Генерация ответа через Thread API
        logger.info("Шаг 8: Генерация ответа через Thread API...")
        record_conversation_event(req.user_id, "user", req.message, now=now_msk)
        thread_id = get_or_create_thread(req.user_id)
        reply = run_assistant_with_thread(req.message, system_context, thread_id, mode=current_mode)
        reply = refine_reply(reply, req.message, req.history, mode=current_mode)
        record_conversation_event(req.user_id, "ai", reply, now=get_moscow_now())
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
                        resolve_meeting_datetime(req.message, meeting_data['datetime']),
                        meeting_data.get('location', ''),
                        meeting_data.get('description', '')
                    )
                    meeting_created = created_meeting
                    logger.info(f"[Meeting] Встреча создана из ответа: {created_meeting['title']}")
                    
                    # Получаем объект встречи из базы для datetime
                    from app.db import SessionLocal
                    from app.models import Meeting
                    db = SessionLocal()
                    meeting_obj = db.query(Meeting).filter_by(id=created_meeting['id']).first()
                    db.close()
                    
                    # Отправляем уведомление о создании встречи (в try-except чтобы не прерывать логику)
                    try:
                        from app.telegram_bot import send_meeting_created
                        datetime_str = meeting_obj.datetime.strftime("%Y-%m-%d %H:%M") if meeting_obj else meeting_data['datetime']
                        send_meeting_created(
                            created_meeting['title'],
                            datetime_str,
                            meeting_obj.location if meeting_obj else meeting_data.get('location', '')
                        )
                        logger.info(f"[Meeting] Уведомление о создании отправлено")
                    except Exception as e:
                        logger.error(f"[Meeting] Ошибка отправки уведомления: {e}")
                    
                    # Убираем блок [MEETING] из ответа для пользователя
                    reply = re.sub(r'\[MEETING\].*?\[/MEETING\]', '', reply, flags=re.DOTALL).strip()
                    reply += "\n\n✅ Встреча записана в календарь!"
                except Exception as e:
                    logger.error(f"[Meeting] Ошибка создания встречи: {e}")
                    import traceback
                    logger.error(traceback.format_exc())

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
            "meeting_created": meeting_created,
            "is_blocked": False,
            "status": "offline" if should_go_offline else "online"
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

@app.get("/stats/{user_id}")
def get_user_stats(user_id: str):
    """Возвращает статистику пользователя: эмоции, отношения, состояние диалога"""
    logger.info("=== Получение статистики для {} ===".format(user_id))
    from app.db import SessionLocal
    from app.models import EmotionalState, RelationshipState, ConversationState
    
    db = SessionLocal()
    try:
        # Эмоции
        emo = db.query(EmotionalState).filter_by(user_id=user_id).first()
        emotions = {
            "calm": emo.calm if emo else 70,
            "joy": emo.joy if emo else 50,
            "romantic": emo.romantic if emo else 20,
            "nervous": emo.nervous if emo else 10,
            "tired": emo.tired if emo else 20
        }
        
        # Отношения
        rel = db.query(RelationshipState).filter_by(user_id=user_id).first()
        relationships = {
            "trust": rel.trust if rel else 20,
            "closeness": rel.closeness if rel else 10,
            "sympathy": rel.sympathy if rel else 15,
            "openness": rel.openness if rel else 5
        }
        
        # Состояние диалога
        conv = db.query(ConversationState).filter_by(user_id=user_id).first()
        conversation = {
            "message_count": conv.message_count if conv else 0,
            "introduced": conv.introduced if conv else False,
            "current_topic": conv.current_topic if conv else ""
        }
        
        return {
            "emotions": emotions,
            "relationships": relationships,
            "conversation": conversation
        }
    finally:
        db.close()

