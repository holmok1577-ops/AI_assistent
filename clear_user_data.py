# -*- coding: utf-8 -*-
"""
Скрипт для очистки данных пользователя из базы данных.
Используется только для тестирования.
"""
from app.db import SessionLocal
from app.models import (
    UserProfile, EmotionalState, RelationshipState,
    ConversationState, UserThread, UserMode,
    MemoryShard, SvetlanaStory, Meeting, Reminder
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_user_data(user_id: str):
    """Удаляет все данные пользователя из базы данных"""
    db = SessionLocal()
    try:
        logger.info("=== Начинаю очистку данных пользователя: {} ===".format(user_id))
        
        # Удаляем встречи
        meetings = db.query(Meeting).filter_by(user_id=user_id).all()
        if meetings:
            logger.info("Удаляю {} встреч".format(len(meetings)))
            for meeting in meetings:
                db.delete(meeting)
        
        # Удаляем напоминания
        reminders = db.query(Reminder).filter_by(user_id=user_id).all()
        if reminders:
            logger.info("Удаляю {} напоминаний".format(len(reminders)))
            for reminder in reminders:
                db.delete(reminder)
        
        # Удаляем историю Светланы
        stories = db.query(SvetlanaStory).filter_by(user_id=user_id).all()
        if stories:
            logger.info("Удаляю {} историй".format(len(stories)))
            for story in stories:
                db.delete(story)
        
        # Удаляем эмбеддинги памяти
        memory_shards = db.query(MemoryShard).filter_by(user_id=user_id).all()
        if memory_shards:
            logger.info("Удаляю {} фрагментов памяти".format(len(memory_shards)))
            for shard in memory_shards:
                db.delete(shard)
        
        # Удаляем состояние диалога
        conv_state = db.query(ConversationState).filter_by(user_id=user_id).first()
        if conv_state:
            logger.info("Удаляю состояние диалога")
            db.delete(conv_state)
        
        # Удаляем thread
        user_thread = db.query(UserThread).filter_by(user_id=user_id).first()
        if user_thread:
            logger.info("Удаляю thread ID")
            db.delete(user_thread)
        
        # Удаляем режим
        user_mode = db.query(UserMode).filter_by(user_id=user_id).first()
        if user_mode:
            logger.info("Удаляю режим пользователя")
            db.delete(user_mode)
        
        # Удаляем эмоциональное состояние
        emo_state = db.query(EmotionalState).filter_by(user_id=user_id).first()
        if emo_state:
            logger.info("Удаляю эмоциональное состояние")
            db.delete(emo_state)
        
        # Удаляем состояние отношений
        rel_state = db.query(RelationshipState).filter_by(user_id=user_id).first()
        if rel_state:
            logger.info("Удаляю состояние отношений")
            db.delete(rel_state)
        
        # Удаляем профиль пользователя
        user_profile = db.query(UserProfile).filter_by(user_id=user_id).first()
        if user_profile:
            logger.info("Удаляю профиль пользователя")
            db.delete(user_profile)
        
        db.commit()
        logger.info("=== Данные пользователя {} успешно очищены ===".format(user_id))
        
    except Exception as e:
        logger.error("Ошибка при очистке данных: {}".format(e))
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Использование: python clear_user_data.py <user_id>")
        print("Пример: python clear_user_data.py user123")
        sys.exit(1)
    
    user_id = sys.argv[1]
    print("Внимание! Это удалит ВСЕ данные пользователя: {}".format(user_id))
    print("Включая встречи, напоминания, память, эмоции, отношения и т.д.")
    
    confirm = input("Вы уверены? (yes/no): ")
    if confirm.lower() == "yes":
        clear_user_data(user_id)
    else:
        print("Отменено")
