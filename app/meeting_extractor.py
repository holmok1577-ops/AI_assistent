import re
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

MOSCOW_TZ = timezone(timedelta(hours=3))

def extract_meeting_from_reply(reply: str) -> dict:
    """Извлекает данные о встрече из ответа ассистента"""
    # Ищем блок [MEETING]...[/MEETING]
    pattern = r'\[MEETING\](.*?)\[/MEETING\]'
    match = re.search(pattern, reply, re.DOTALL)
    
    if not match:
        return None
    
    content = match.group(1).strip()
    
    # Извлекаем поля - используем более строгий паттерн чтобы не захватывать следующие поля
    meeting_data = {}
    
    # Сначала разделяем по переносам строк
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if ':' in line:
            # Разделяем по первому двоеточию
            parts = line.split(':', 1)
            if len(parts) == 2:
                key = parts[0].strip().lower()
                value = parts[1].strip()
                
                if key == 'title' and value:
                    meeting_data['title'] = value
                elif key == 'datetime' and value:
                    meeting_data['datetime'] = value
                elif key == 'location':
                    meeting_data['location'] = value
                elif key == 'description':
                    meeting_data['description'] = value
    
    # Проверяем обязательные поля
    if 'title' not in meeting_data or 'datetime' not in meeting_data:
        logger.warning("[MeetingExtractor] Не все обязательные поля заполнены")
        return None
    
    logger.info(f"[MeetingExtractor] Извлечена встреча: {meeting_data}")
    return meeting_data

def get_moscow_now() -> datetime:
    return datetime.now(MOSCOW_TZ).replace(tzinfo=None)


def _extract_time(text: str) -> tuple[int, int] | None:
    match = re.search(r'(?<!\d)(\d{1,2})[:.](\d{2})(?!\d)', text)
    if not match:
        return None

    hour = int(match.group(1))
    minute = int(match.group(2))
    if hour > 23 or minute > 59:
        return None
    return hour, minute


def _apply_time(base_date: datetime, time_value: tuple[int, int] | None) -> datetime:
    hour, minute = time_value if time_value else (9, 0)
    return base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)


def parse_relative_datetime(text: str, now: datetime | None = None) -> str:
    """Парсит относительные даты типа 'сегодня в 16:38' в ISO формат по МСК."""
    text_lower = (text or "").lower().strip()
    now = now or get_moscow_now()

    try:
        return datetime.fromisoformat(text).replace(second=0, microsecond=0).isoformat()
    except Exception:
        pass

    time_value = _extract_time(text_lower)

    if "послезавтра" in text_lower:
        return _apply_time(now + timedelta(days=2), time_value).isoformat()

    if "завтра" in text_lower:
        return _apply_time(now + timedelta(days=1), time_value).isoformat()

    if "сегодня" in text_lower:
        return _apply_time(now, time_value).isoformat()

    date_match = re.search(r'(?<!\d)(\d{1,2})[./-](\d{1,2})(?:[./-](\d{2,4}))?(?!\d)', text_lower)
    if date_match:
        day = int(date_match.group(1))
        month = int(date_match.group(2))
        year_raw = date_match.group(3)
        year = now.year
        if year_raw:
            year = int(year_raw)
            if year < 100:
                year += 2000
        try:
            parsed = datetime(year, month, day)
            return _apply_time(parsed, time_value).isoformat()
        except ValueError:
            logger.warning("[MeetingExtractor] Некорректная дата в тексте: %s", text)

    return text


def resolve_meeting_datetime(user_message: str, assistant_datetime: str) -> str:
    """
    Нормализует дату встречи по сообщению пользователя с приоритетом МСК-относительных дат.
    Не доверяет слепо дате от модели, если пользователь говорил "сегодня/завтра/послезавтра".
    """
    now = get_moscow_now()
    user_text = (user_message or "").lower()

    if any(keyword in user_text for keyword in ["сегодня", "завтра", "послезавтра"]):
        resolved = parse_relative_datetime(user_message, now=now)
        logger.info("[MeetingExtractor] Использована дата из сообщения пользователя: %s -> %s", user_message, resolved)
        return resolved

    normalized_assistant = parse_relative_datetime(assistant_datetime, now=now)
    try:
        parsed = datetime.fromisoformat(normalized_assistant)
        if parsed.year < now.year - 1:
            logger.warning(
                "[MeetingExtractor] Подозрительно старая дата от ассистента: %s. Пробуем извлечь из сообщения пользователя.",
                normalized_assistant,
            )
            fallback = parse_relative_datetime(user_message, now=now)
            return fallback if fallback != user_message else normalized_assistant
    except Exception:
        logger.warning("[MeetingExtractor] Не удалось распарсить assistant datetime: %s", assistant_datetime)

    return normalized_assistant
