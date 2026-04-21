import re
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def extract_meeting_from_reply(reply: str) -> dict:
    """Извлекает данные о встрече из ответа ассистента"""
    # Ищем блок [MEETING]...[/MEETING]
    pattern = r'\[MEETING\](.*?)\[/MEETING\]'
    match = re.search(pattern, reply, re.DOTALL)
    
    if not match:
        return None
    
    content = match.group(1).strip()
    
    # Извлекаем поля
    meeting_data = {}
    
    title_match = re.search(r'title:\s*(.+)', content, re.IGNORECASE)
    if title_match:
        meeting_data['title'] = title_match.group(1).strip()
    
    datetime_match = re.search(r'datetime:\s*(.+)', content, re.IGNORECASE)
    if datetime_match:
        meeting_data['datetime'] = datetime_match.group(1).strip()
    
    location_match = re.search(r'location:\s*(.+)', content, re.IGNORECASE)
    if location_match:
        meeting_data['location'] = location_match.group(1).strip()
    
    description_match = re.search(r'description:\s*(.+)', content, re.IGNORECASE)
    if description_match:
        meeting_data['description'] = description_match.group(1).strip()
    
    # Проверяем обязательные поля
    if 'title' not in meeting_data or 'datetime' not in meeting_data:
        logger.warning("[MeetingExtractor] Не все обязательные поля заполнены")
        return None
    
    logger.info(f"[MeetingExtractor] Извлечена встреча: {meeting_data}")
    return meeting_data

def parse_relative_datetime(text: str) -> str:
    """Парсит относительные даты типа 'завтра в 14:00' в ISO формат"""
    text_lower = text.lower().strip()
    now = datetime.now()
    
    try:
        # Пробуем парсить как ISO
        return datetime.fromisoformat(text).isoformat()
    except:
        pass
    
    # Парсим относительные выражения
    if 'завтра' in text_lower:
        target_date = now + timedelta(days=1)
        # Извлекаем время
        time_match = re.search(r'(\d{1,2}):(\d{2})', text)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            target_date = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        else:
            # Если время не указано, используем 9:00
            target_date = target_date.replace(hour=9, minute=0, second=0, microsecond=0)
        return target_date.isoformat()
    
    if 'сегодня' in text_lower:
        time_match = re.search(r'(\d{1,2}):(\d{2})', text)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            target_date = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        else:
            target_date = now.replace(hour=9, minute=0, second=0, microsecond=0)
        return target_date.isoformat()
    
    # Если не распознали, возвращаем как есть
    return text
