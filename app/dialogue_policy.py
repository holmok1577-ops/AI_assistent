import re


TOPIC_KEYWORDS = {
    "work": [
        "работ",
        "офис",
        "клиент",
        "проект",
        "коллег",
        "заказ",
        "началь",
        "созвон",
        "дедлайн",
    ],
    "study": [
        "учеб",
        "универ",
        "школ",
        "экзам",
        "урок",
        "курс",
        "домашк",
        "студент",
    ],
    "relationships": [
        "девушк",
        "парен",
        "отношен",
        "любл",
        "свидан",
        "семь",
        "жен",
        "муж",
    ],
    "feelings": [
        "чувств",
        "настроен",
        "груст",
        "тоск",
        "рад",
        "устал",
        "пережива",
        "нерв",
        "одинок",
    ],
    "hobby": [
        "хобби",
        "игра",
        "спорт",
        "музык",
        "книг",
        "сериал",
        "фильм",
        "рисова",
        "гуля",
    ],
    "plans": [
        "план",
        "завтра",
        "сегодня",
        "выходн",
        "поездк",
        "встреч",
        "потом",
        "скоро",
    ],
}


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _extract_words(text: str) -> list[str]:
    return re.findall(r"[a-zA-Zа-яА-ЯёЁ0-9-]+", text or "")


def detect_topic(text: str) -> str:
    normalized = _normalize_text(text)
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return topic
    return "general"


def classify_user_depth(message: str) -> str:
    words = _extract_words(message)
    if len(words) <= 3:
        return "minimal"
    if len(words) <= 12:
        return "brief"
    return "detailed"


def _extract_recent_messages(history: list, role: str) -> list[str]:
    return [
        item.get("text", "")
        for item in history[-8:]
        if item.get("role") == role and item.get("text")
    ]


def _count_trailing_questions(history: list) -> int:
    count = 0
    for item in reversed(history[-6:]):
        if item.get("role") != "ai":
            break
        text = item.get("text", "").strip()
        if "?" in text:
            count += 1
        else:
            break
    return count


def _same_topic_streak(current_topic: str, recent_user_messages: list[str]) -> int:
    streak = 1
    for text in reversed(recent_user_messages):
        if detect_topic(text) == current_topic:
            streak += 1
        else:
            break
    return streak


def build_dialogue_guidance(
    user_message: str,
    history: list,
    message_count: int,
    introduced: bool,
) -> dict:
    user_depth = classify_user_depth(user_message)
    current_topic = detect_topic(user_message)
    recent_user_messages = _extract_recent_messages(history[:-1], "user") if history else []
    assistant_question_streak = _count_trailing_questions(history)
    same_topic_streak = _same_topic_streak(current_topic, recent_user_messages)
    user_asked_question = "?" in (user_message or "")

    should_change_topic = (
        same_topic_streak >= 3 and user_depth in {"minimal", "brief"}
    ) or (assistant_question_streak >= 2 and user_depth != "detailed")

    if user_depth == "minimal":
        follow_up_style = "не копай глубже; лучше коротко отреагируй и либо мягко смени тему, либо обойдись без вопроса"
    elif user_depth == "brief":
        follow_up_style = "можно задать один лёгкий вопрос, но без допроса и без глубокого копания"
    else:
        follow_up_style = "можно немного углубиться, но всё равно держи ответ компактным и живым"

    if user_asked_question:
        primary_goal = "сначала прямо ответь на вопрос пользователя"
    elif not introduced and message_count <= 3:
        primary_goal = "сохраняй лёгкое знакомство без резкого углубления"
    else:
        primary_goal = "поддержи естественный ход разговора без давления"

    topic_instruction = (
        "пора мягко сменить тему или оставить реплику без вопроса"
        if should_change_topic
        else "текущую тему можно ещё немного поддержать"
    )

    guidance_text = f"""
📌 ДИНАМИКА ЭТОЙ РЕПЛИКИ:
- Главная цель: {primary_goal}.
- Текущая тема: {current_topic}.
- Глубина ответа пользователя: {user_depth}.
- Серия одной темы подряд: {same_topic_streak}.
- Серия вопросов Светланы подряд: {assistant_question_streak}.
- По этой реплике: {follow_up_style}.
- По теме: {topic_instruction}.
- Если задаёшь вопрос, то только один.
- Если пользователь сам не раскрылся, не вытягивай из него детали насильно.
- Иногда нормальная живая реакция вообще без вопроса.
""".strip()

    return {
        "current_topic": current_topic,
        "user_depth": user_depth,
        "should_change_topic": should_change_topic,
        "user_asked_question": user_asked_question,
        "guidance_text": guidance_text,
    }
