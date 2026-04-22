from openai import OpenAI
from app.config import PROXYAPI_KEY, PROXYAPI_BASE_URL
from app.db import SessionLocal
from app.models import UserThread
from app.persona_instructions import ASSISTANT_INSTRUCTIONS
from app.secretary_instructions import SECRETARY_INSTRUCTIONS
import logging

logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=PROXYAPI_KEY,
    base_url=PROXYAPI_BASE_URL,
    default_headers={"OpenAI-Beta": "assistants=v2"}
)

# Глобальные ID ассистентов для разных режимов
ASSISTANT_IDS = {
    "chat": None,
    "secretary": None
}

def get_or_create_assistant(mode: str = "chat", force_recreate: bool = False) -> str:
    """Создаёт или возвращает существующий ассистент для указанного режима"""
    global ASSISTANT_IDS
    
    # Выбор инструкции в зависимости от режима
    instructions = SECRETARY_INSTRUCTIONS if mode == "secretary" else ASSISTANT_INSTRUCTIONS
    
    # Если нужно принудительно пересоздать или ассистент ещё не создан
    if force_recreate or not ASSISTANT_IDS.get(mode):
        # Если есть старый ассистент - удаляем его
        if ASSISTANT_IDS.get(mode) and force_recreate:
            try:
                logger.info(f"[Thread] Удаляем старого ассистента режима {mode}: {ASSISTANT_IDS[mode]}")
                client.beta.assistants.delete(ASSISTANT_IDS[mode])
            except Exception as e:
                logger.warning(f"[Thread] Не удалось удалить старого ассистента: {e}")
        
        logger.info(f"[Thread] Создаём ассистент Светлана для режима: {mode}")
        assistant = client.beta.assistants.create(
            name=f"Светлана ({mode})",
            instructions=instructions,
            model="gpt-4o-mini",
            temperature=0.8
        )
        ASSISTANT_IDS[mode] = assistant.id
        logger.info(f"[Thread] Ассистент создан для режима {mode}: {ASSISTANT_IDS[mode]}")
    
    return ASSISTANT_IDS[mode]

def get_or_create_thread(user_id: str) -> str:
    """Получает существующий thread или создаёт новый для пользователя"""
    db = SessionLocal()
    thread_record = db.query(UserThread).filter_by(user_id=user_id).first()

    if thread_record:
        logger.info(f"[Thread] Используем существующий thread: {thread_record.thread_id}")
        db.close()
        return thread_record.thread_id

    # Создаём новый thread
    logger.info(f"[Thread] Создаём новый thread для пользователя {user_id}")
    thread = client.beta.threads.create()
    thread_record = UserThread(user_id=user_id, thread_id=thread.id)
    db.add(thread_record)
    db.commit()
    db.close()
    logger.info(f"[Thread] Thread создан: {thread.id}")
    return thread.id

def add_message_to_thread(thread_id: str, role: str, content: str):
    """Добавляет сообщение в thread"""
    logger.info(f"[Thread] Добавляем сообщение в thread {thread_id}: {role} - {content[:50]}...")
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role=role,
        content=content
    )

def run_assistant_with_thread(message: str, system_context: str, thread_id: str, mode: str = "chat") -> str:
    """Запускает ассистента с thread для генерации ответа"""
    logger.info(f"[Thread] Запуск ассистента с thread {thread_id} в режиме {mode}")

    # Получаем или создаём ассистент для указанного режима
    assistant_id = get_or_create_assistant(mode=mode)

    # Добавляем сообщение пользователя
    add_message_to_thread(thread_id, "user", message)

    # Создаём run с дополнительными инструкциями
    run_params = {
        "thread_id": thread_id,
        "assistant_id": assistant_id
    }
    
    # Добавляем system_context как additional_instructions
    if system_context:
        logger.info(f"[Thread] Используем additional_instructions (первые 100 символов): {system_context[:100]}...")
        # Обрезаем слишком длинный контекст (лимит 20000 символов)
        additional_instructions = system_context[:18000] if len(system_context) > 18000 else system_context
        run_params["additional_instructions"] = additional_instructions

    run = client.beta.threads.runs.create(**run_params)
    logger.info(f"[Thread] Run создан: {run.id}")

    # Ждём завершения
    import time
    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
        logger.info(f"[Thread] Статус run: {run_status.status}")
        if run_status.status in ["completed", "failed", "cancelled"]:
            break
        time.sleep(1)

    if run_status.status != "completed":
        logger.error(f"[Thread] Run завершился с ошибкой: {run_status.status}")
        raise Exception(f"Run failed: {run_status.status}")

    # Получаем сообщения
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    # Последнее сообщение - ответ ассистента
    reply = messages.data[0].content[0].text.value
    logger.info(f"[Thread] Ответ получен: {reply[:100]}...")

    return reply
