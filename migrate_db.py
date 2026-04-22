"""Миграция базы данных для добавления новых полей напоминаний"""
from app.db import engine
from sqlalchemy import text, inspect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    """Добавляет новые поля в таблицу meetings"""
    try:
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('meetings')]
        
        logger.info(f"Текущие колонки: {columns}")
        
        with engine.connect() as conn:
            if 'reminder_24h_sent' not in columns:
                logger.info("Добавляем колонку reminder_24h_sent")
                conn.execute(text("ALTER TABLE meetings ADD COLUMN reminder_24h_sent BOOLEAN DEFAULT FALSE"))
                conn.commit()
            
            if 'reminder_30m_sent' not in columns:
                logger.info("Добавляем колонку reminder_30m_sent")
                conn.execute(text("ALTER TABLE meetings ADD COLUMN reminder_30m_sent BOOLEAN DEFAULT FALSE"))
                conn.commit()
            
            if 'reminder_10m_sent' not in columns:
                logger.info("Добавляем колонку reminder_10m_sent")
                conn.execute(text("ALTER TABLE meetings ADD COLUMN reminder_10m_sent BOOLEAN DEFAULT FALSE"))
                conn.commit()
            
            # Удаляем старую колонку если она есть
            if 'reminder_sent' in columns:
                logger.info("Удаляем старую колонку reminder_sent")
                conn.execute(text("ALTER TABLE meetings DROP COLUMN reminder_sent"))
                conn.commit()
            
            logger.info("Миграция завершена успешно")
    except Exception as e:
        logger.error(f"Ошибка миграции: {e}")
        raise

if __name__ == "__main__":
    migrate()
