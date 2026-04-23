# -*- coding: utf-8 -*-
"""
Скрипт для очистки ВСЕХ данных из базы данных.
Используется только для тестирования - удаляет данные всех пользователей.
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

def clear_all_data():
    """Удаляет все данные из базы данных"""
    db = SessionLocal()
    try:
        logger.info("=== Начинаю очистку ВСЕХ данных ===")
        
        # Получаем количество записей до удаления
        meetings_count = db.query(Meeting).count()
        reminders_count = db.query(Reminder).count()
        stories_count = db.query(SvetlanaStory).count()
        memory_count = db.query(MemoryShard).count()
        conv_count = db.query(ConversationState).count()
        thread_count = db.query(UserThread).count()
        mode_count = db.query(UserMode).count()
        emo_count = db.query(EmotionalState).count()
        rel_count = db.query(RelationshipState).count()
        profile_count = db.query(UserProfile).count()
        
        logger.info(f"Встреч: {meetings_count}")
        logger.info(f"Напоминаний: {reminders_count}")
        logger.info(f"Историй: {stories_count}")
        logger.info(f"Фрагментов памяти: {memory_count}")
        logger.info(f"Состояний диалога: {conv_count}")
        logger.info(f"Thread ID: {thread_count}")
        logger.info(f"Режимов: {mode_count}")
        logger.info(f"Эмоциональных состояний: {emo_count}")
        logger.info(f"Состояний отношений: {rel_count}")
        logger.info(f"Профилей: {profile_count}")
        
        # Удаляем все записи
        db.query(Meeting).delete()
        db.query(Reminder).delete()
        db.query(SvetlanaStory).delete()
        db.query(MemoryShard).delete()
        db.query(ConversationState).delete()
        db.query(UserThread).delete()
        db.query(UserMode).delete()
        db.query(EmotionalState).delete()
        db.query(RelationshipState).delete()
        db.query(UserProfile).delete()
        
        db.commit()
        logger.info("=== ВСЕ данные успешно очищены ===")
        
    except Exception as e:
        logger.error("Ошибка при очистке данных: {}".format(e))
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("ВНИМАНИЕ! Это удалит ВСЕ данные из базы данных.")
    print("Включая всех пользователей, встречи, напоминания, память, эмоции, отношения и т.д.")
    print("Это действие НЕОБРАТИМО!")
    
    confirm = input("Вы уверены? (yes/no): ")
    if confirm.lower() == "yes":
        clear_all_data()
    else:
        print("Отменено")
