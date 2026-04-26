import json
import logging
from datetime import datetime, timedelta

from app.redis_client import r
from app.meeting_extractor import get_moscow_now

logger = logging.getLogger(__name__)

MAX_EVENTS = 200
TTL_SECONDS = 60 * 60 * 24 * 14


def _journal_key(user_id: str) -> str:
    return f"conversation_journal:{user_id}"


def record_conversation_event(user_id: str, role: str, text: str, now: datetime | None = None):
    if not text:
        return

    now = now or get_moscow_now()
    payload = {
        "role": role,
        "text": text,
        "ts": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M"),
    }

    try:
        key = _journal_key(user_id)
        r.lpush(key, json.dumps(payload, ensure_ascii=False))
        r.ltrim(key, 0, MAX_EVENTS - 1)
        r.expire(key, TTL_SECONDS)
    except Exception as exc:
        logger.warning(f"[ConversationJournal] Redis write failed: {exc}")


def _load_events(user_id: str) -> list[dict]:
    try:
        raw = r.lrange(_journal_key(user_id), 0, MAX_EVENTS - 1)
    except Exception as exc:
        logger.warning(f"[ConversationJournal] Redis read failed: {exc}")
        return []

    events = []
    for item in raw:
        try:
            events.append(json.loads(item))
        except Exception:
            continue
    return list(reversed(events))


def _format_event(event: dict) -> str:
    role = "Пользователь" if event.get("role") == "user" else "Светлана"
    return f"- {event.get('date')} {event.get('time')} {role}: {event.get('text', '')}"


def _slice_day(events: list[dict], target_date: str) -> list[dict]:
    return [event for event in events if event.get("date") == target_date]


def build_temporal_context(user_id: str, user_message: str, now: datetime | None = None) -> str:
    now = now or get_moscow_now()
    today = now.strftime("%Y-%m-%d")
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")

    lines = [
        "📌 ВРЕМЕННОЙ КОНТЕКСТ ПО МСК:",
        f"- Сейчас по Москве: {now.strftime('%Y-%m-%d %H:%M:%S')}",
        f"- Сегодня: {today}",
        f"- Вчера: {yesterday}",
        f"- Завтра: {tomorrow}",
    ]

    text_lower = (user_message or "").lower()
    events = _load_events(user_id)
    if not events:
        return "\n".join(lines)

    if "вчера" in text_lower:
        yesterday_events = _slice_day(events, yesterday)
        if yesterday_events:
            lines.append("📌 ЧАСТЬ ВЧЕРАШНЕГО ДИАЛОГА:")
            lines.extend(_format_event(event) for event in yesterday_events[-8:])
        else:
            lines.append("- Вчерашних сообщений в журнале не найдено.")

    if "сегодня" in text_lower:
        today_events = _slice_day(events, today)
        if today_events:
            lines.append("📌 ЧАСТЬ СЕГОДНЯШНЕГО ДИАЛОГА:")
            lines.extend(_format_event(event) for event in today_events[-8:])

    if any(phrase in text_lower for phrase in ["о чем мы говорили", "о чём мы говорили", "что мы обсуждали", "что было вчера"]):
        recent = events[-10:]
        if recent:
            lines.append("📌 НЕДАВНИЕ РЕАЛЬНЫЕ СООБЩЕНИЯ ИЗ ЖУРНАЛА:")
            lines.extend(_format_event(event) for event in recent)

    lines.append("- Если пользователь спрашивает про вчера/сегодня, опирайся на даты выше и на журнал, а не выдумывай.")
    return "\n".join(lines)
