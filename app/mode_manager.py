from app.db import SessionLocal
from app.models import UserMode
import logging

logger = logging.getLogger(__name__)

CODE_PHRASES = {
    "to_secretary": ["давай поработаем", "давай работать", "режим работы", "режим секретаря"],
    "to_chat": ["давай поболтаем", "давай общаться", "режим общения", "режим чата"]
}

def get_user_mode(user_id: str) -> str:
    """Получает текущий режим пользователя"""
    db = SessionLocal()
    mode_record = db.query(UserMode).filter_by(user_id=user_id).first()
    
    if not mode_record:
        # Создаём запись с режимом по умолчанию
        mode_record = UserMode(user_id=user_id, mode="chat")
        db.add(mode_record)
        db.commit()
        db.refresh(mode_record)
    
    mode = mode_record.mode
    db.close()
    return mode

def set_user_mode(user_id: str, mode: str) -> str:
    """Устанавливает режим пользователя"""
    db = SessionLocal()
    mode_record = db.query(UserMode).filter_by(user_id=user_id).first()
    
    if not mode_record:
        mode_record = UserMode(user_id=user_id, mode=mode)
        db.add(mode_record)
    else:
        mode_record.mode = mode
    
    db.commit()
    db.close()
    logger.info(f"[Mode] Пользователь {user_id} переключился в режим: {mode}")
    return mode

def detect_code_phrase(message: str) -> str:
    """Определяет кодовую фразу для переключения режима"""
    message_lower = message.lower().strip()
    
    # Проверка на переключение в режим секретаря
    for phrase in CODE_PHRASES["to_secretary"]:
        if phrase in message_lower:
            return "secretary"
    
    # Проверка на переключение в режим чата
    for phrase in CODE_PHRASES["to_chat"]:
        if phrase in message_lower:
            return "chat"
    
    return None

def check_and_switch_mode(user_id: str, message: str) -> tuple:
    """
    Проверяет кодовую фразу и переключает режим если нужно.
    Возвращает (new_mode, switched) где switched - True если режим изменился
    """
    detected_mode = detect_code_phrase(message)
    
    if detected_mode:
        current_mode = get_user_mode(user_id)
        if current_mode != detected_mode:
            new_mode = set_user_mode(user_id, detected_mode)
            return (new_mode, True)
    
    current_mode = get_user_mode(user_id)
    return (current_mode, False)
