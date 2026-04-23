"""
Миграция для добавления полей is_blocked и first_extreme_response в таблицу emotional_state
"""
from app.db import SessionLocal, engine
from sqlalchemy import text, inspect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    """Добавляет поля is_blocked и first_extreme_response в таблицу emotional_state"""
    db = SessionLocal()
    try:
        # Проверяем, существуют ли колонки
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('emotional_state')]
        
        # Добавляем is_blocked если нет
        if 'is_blocked' not in columns:
            logger.info("Добавление колонки is_blocked...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE emotional_state ADD COLUMN is_blocked BOOLEAN DEFAULT FALSE"))
                conn.commit()
        else:
            logger.info("Колонка is_blocked уже существует")
        
        # Добавляем first_extreme_response если нет
        if 'first_extreme_response' not in columns:
            logger.info("Добавление колонки first_extreme_response...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE emotional_state ADD COLUMN first_extreme_response BOOLEAN DEFAULT FALSE"))
                conn.commit()
        else:
            logger.info("Колонка first_extreme_response уже существует")
        
        logger.info("Миграция успешно выполнена")
    except Exception as e:
        logger.error(f"Ошибка миграции: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
