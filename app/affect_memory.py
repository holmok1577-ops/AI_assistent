import json
import logging

from app.redis_client import r

logger = logging.getLogger(__name__)

MAX_EVENTS = 12
TTL_SECONDS = 60 * 60 * 24 * 7

POSITIVE_TONES = {"friendly", "warm", "flirty"}
HOSTILE_TONES = {"angry", "insult", "profane", "aggressive_profane"}
PLAYFUL_TONES = {"playful"}


def _key(user_id: str) -> str:
    return f"affect_history:{user_id}"


def _safe_lrange(key: str) -> list[str]:
    try:
        return r.lrange(key, 0, MAX_EVENTS - 1)
    except Exception as exc:
        logger.warning(f"[AffectMemory] Redis read failed: {exc}")
        return []


def _safe_write(key: str, payload: str):
    try:
        r.lpush(key, payload)
        r.ltrim(key, 0, MAX_EVENTS - 1)
        r.expire(key, TTL_SECONDS)
    except Exception as exc:
        logger.warning(f"[AffectMemory] Redis write failed: {exc}")


def _event_category(tone: str) -> str:
    if tone in HOSTILE_TONES:
        return "hostile"
    if tone in POSITIVE_TONES:
        return "positive"
    if tone in PLAYFUL_TONES:
        return "playful"
    return "neutral"


def record_and_get_affect_profile(user_id: str, tone: str, message: str) -> dict:
    key = _key(user_id)
    event = {
        "tone": tone,
        "category": _event_category(tone),
        "message_len": len(message or ""),
    }
    _safe_write(key, json.dumps(event, ensure_ascii=False))

    raw_events = _safe_lrange(key)
    events = []
    for item in raw_events:
        try:
            events.append(json.loads(item))
        except Exception:
            continue

    tones = [item.get("tone", "neutral") for item in events]
    hostile_recent = sum(1 for t in tones[:5] if t in HOSTILE_TONES)
    positive_recent = sum(1 for t in tones[:5] if t in POSITIVE_TONES)
    playful_recent = sum(1 for t in tones[:5] if t in PLAYFUL_TONES)

    hostile_streak = 0
    positive_streak = 0
    playful_streak = 0
    for tone_name in tones:
        if tone_name in HOSTILE_TONES:
            hostile_streak += 1
        else:
            break

    for tone_name in tones:
        if tone_name in POSITIVE_TONES:
            positive_streak += 1
        else:
            break

    for tone_name in tones:
        if tone_name in PLAYFUL_TONES:
            playful_streak += 1
        else:
            break

    return {
        "hostile_recent": hostile_recent,
        "positive_recent": positive_recent,
        "playful_recent": playful_recent,
        "hostile_streak": hostile_streak,
        "positive_streak": positive_streak,
        "playful_streak": playful_streak,
        "recent_tones": tones[:6],
    }


def build_affect_guidance(profile: dict) -> str:
    lines = ["📌 ЭМОЦИОНАЛЬНЫЙ ФОН ПОСЛЕДНИХ РЕПЛИК:"]

    if profile.get("hostile_recent", 0) >= 2:
        lines.append("- Пользователь в последних сообщениях повторно грубил или давил. Не обнуляй это, реакция может быть резче и холоднее.")
    if profile.get("hostile_streak", 0) >= 2:
        lines.append("- Это уже не единичный срыв, а серия неприятного тона. Терпение Светланы заметно ниже обычного.")
    if profile.get("positive_recent", 0) >= 2:
        lines.append("- Пользователь уже несколько сообщений подряд тёплый и доброжелательный. Можно быть мягче, живее и теплее.")
    if profile.get("positive_streak", 0) >= 3:
        lines.append("- Между вами сейчас хороший эмоциональный поток, Светлана может чуть охотнее раскрываться.")
    if profile.get("playful_recent", 0) >= 2:
        lines.append("- Пользователь держит шутливый тон. Можно позволить лёгкую игривость, живую реакцию или мягкую подколку.")
    if profile.get("playful_streak", 0) >= 3:
        lines.append("- В разговоре уже есть устоявшийся юмор. Можно отвечать чуть свободнее, но без клоунады.")

    if len(lines) == 1:
        lines.append("- Эмоциональный фон пока ровный, без накопленного перекоса.")

    return "\n".join(lines)
