# -*- coding: utf-8 -*-
"""
Миграция для добавления таблицы conversation_state
"""
from app.db import engine, Base
from app.models import ConversationState
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    """Создаёт таблицу conversation_state если её нет"""
    try:
        ConversationState.__table__.create(engine, checkfirst=True)
        logger.info("Таблица conversation_state успешно создана")
    except Exception as e:
        logger.error("Ошибка при создании таблицы: {}".format(e))
        raise

if __name__ == "__main__":
    migrate()
