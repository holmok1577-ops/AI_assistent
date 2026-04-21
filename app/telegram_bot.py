import logging
from telegram import Bot
from app.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None

async def send_telegram_message(message: str, chat_id: str = None) -> bool:
    """Отправляет сообщение в Telegram"""
    if not bot:
        logger.warning("[Telegram] Бот не инициализирован (нет токена)")
        return False
    
    target_chat_id = chat_id or TELEGRAM_CHAT_ID
    if not target_chat_id:
        logger.warning("[Telegram] Не указан chat_id")
        return False
    
    try:
        await bot.send_message(chat_id=target_chat_id, text=message)
        logger.info(f"[Telegram] Сообщение отправлено в {target_chat_id}: {message[:50]}...")
        return True
    except Exception as e:
        logger.error(f"[Telegram] Ошибка отправки сообщения: {e}")
        return False

def send_meeting_reminder(title: str, datetime_str: str, location: str = "") -> bool:
    """Отправляет напоминание о встрече (синхронная обёртка)"""
    import asyncio
    
    location_text = f"\n📍 Место: {location}" if location else ""
    message = f"🔔 Напоминание о встрече!\n\n📅 {title}\n🕒 {datetime_str}{location_text}"
    
    try:
        return asyncio.run(send_telegram_message(message))
    except Exception as e:
        logger.error(f"[Telegram] Ошибка при отправке напоминания: {e}")
        return False

def send_reminder(text: str, datetime_str: str) -> bool:
    """Отправляет простое напоминание"""
    import asyncio
    
    message = f"🔔 Напоминание!\n\n{text}\n🕒 {datetime_str}"
    
    try:
        return asyncio.run(send_telegram_message(message))
    except Exception as e:
        logger.error(f"[Telegram] Ошибка при отправке напоминания: {e}")
        return False
