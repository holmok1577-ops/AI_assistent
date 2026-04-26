from app.db import SessionLocal
from app.models import ConversationState
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def get_conversation_state(user_id: str) -> ConversationState:
    """Получает или создаёт состояние диалога пользователя"""
    db = SessionLocal()
    try:
        state = db.query(ConversationState).filter_by(user_id=user_id).first()
        if not state:
            state = ConversationState(user_id=user_id)
            db.add(state)
            db.commit()
            db.refresh(state)
        return state
    finally:
        db.close()

def increment_message_count(user_id: str) -> int:
    """Увеличивает счётчик сообщений и возвращает новое значение"""
    db = SessionLocal()
    try:
        state = db.query(ConversationState).filter_by(user_id=user_id).first()
        if not state:
            state = ConversationState(user_id=user_id)
            db.add(state)
        
        state.message_count += 1
        db.commit()
        db.refresh(state)
        return state.message_count
    finally:
        db.close()

def mark_introduced(user_id: str):
    """Отмечает, что знакомство произошло"""
    db = SessionLocal()
    try:
        state = db.query(ConversationState).filter_by(user_id=user_id).first()
        if not state:
            state = ConversationState(user_id=user_id)
            db.add(state)
        
        state.introduced = True
        db.commit()
        logger.info(f"[Conversation] Пользователь {user_id} познакомился")
    finally:
        db.close()

def should_change_topic(user_id: str, current_topic: str) -> bool:
    """
    Определяет, нужно ли сменить тему.
    Смена темы происходит каждые 5-7 сообщений на одной теме.
    """
    db = SessionLocal()
    try:
        state = db.query(ConversationState).filter_by(user_id=user_id).first()
        if not state:
            return False
        
        # Если тема изменилась
        if state.current_topic != current_topic:
            state.current_topic = current_topic
            state.topic_changes += 1
            state.last_topic_change = datetime.now()
            db.commit()
            return False
        
        # Если на одной теме уже более 6 сообщений - пора сменить
        if state.message_count > 0 and state.message_count % 6 == 0:
            return True
        
        return False
    finally:
        db.close()


def update_topic_state(user_id: str, current_topic: str):
    """Обновляет текущую тему разговора для статистики и мягкого контроля диалога."""
    db = SessionLocal()
    try:
        state = db.query(ConversationState).filter_by(user_id=user_id).first()
        if not state:
            state = ConversationState(user_id=user_id)
            db.add(state)

        if state.current_topic != current_topic:
            state.current_topic = current_topic
            state.topic_changes += 1
            state.last_topic_change = datetime.now()
            db.commit()
    finally:
        db.close()

def reset_conversation(user_id: str):
    """Сбрасывает состояние диалога (для начала нового разговора)"""
    db = SessionLocal()
    try:
        state = db.query(ConversationState).filter_by(user_id=user_id).first()
        if state:
            state.message_count = 0
            state.current_topic = ""
            state.topic_changes = 0
            state.last_topic_change = None
            db.commit()
            logger.info(f"[Conversation] Диалог с {user_id} сброшен")
    finally:
        db.close()
