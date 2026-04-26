import logging
import re

from openai import OpenAI

from app.config import OPENAI_API_KEY, OPENAI_BASE_URL, CHAT_MODEL

logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
    default_headers={"OpenAI-Beta": "assistants=v2"},
)

SELF_REPLACEMENTS = {
    r"\bя понял\b": "я поняла",
    r"\bпонял\b": "поняла",
    r"\bя согласен\b": "я согласна",
    r"\bсогласен\b": "согласна",
    r"\bя уверен\b": "я уверена",
    r"\bуверен\b": "уверена",
    r"\bя готов\b": "я готова",
    r"\bготов\b": "готова",
    r"\bя рад\b": "я рада",
    r"\bрад\b": "рада",
    r"\bя удивлен\b": "я удивлена",
    r"\bудивлен\b": "удивлена",
    r"\bя впечатлен\b": "я впечатлена",
    r"\bвпечатлен\b": "впечатлена",
    r"\bя заинтересован\b": "я заинтересована",
    r"\bзаинтересован\b": "заинтересована",
}

USER_GENDER_PATTERNS = [
    r"\bты понял\b",
    r"\bты устал\b",
    r"\bты сказал\b",
    r"\bты сделал\b",
    r"\bты решил\b",
    r"\bты хотел\b",
    r"\bты думал\b",
    r"\bты работал\b",
    r"\bты был\b",
]

AWKWARD_PATTERNS = [
    r"как тебе тво[её] имя\??",
    r"в чем именно ты хотел\(а\) помощи\??",
    r"как тебе твое имя\??",
]

MEMORY_CHECK_PATTERNS = [
    r"как меня зовут\??",
    r"помнишь мое имя\??",
    r"ты помнишь мое имя\??",
    r"какое у меня имя\??",
]


def _normalize_question(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-zа-яё0-9?\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _extract_questions(text: str) -> list[str]:
    return [
        _normalize_question(part + "?")
        for part in re.findall(r"[^?]+\?", text or "")
        if part.strip()
    ]


def sanitize_reply(reply: str) -> str:
    clean_reply = (reply or "").strip()
    for pattern, replacement in SELF_REPLACEMENTS.items():
        clean_reply = re.sub(pattern, replacement, clean_reply, flags=re.IGNORECASE)

    clean_reply = re.sub(r"[ \t]+\n", "\n", clean_reply)
    clean_reply = re.sub(r"\n{3,}", "\n\n", clean_reply)
    return clean_reply.strip()


def detect_reply_issues(reply: str, history: list, user_message: str) -> list[str]:
    issues = []
    assistant_questions = []
    for item in history[-6:]:
        if item.get("role") == "ai":
            assistant_questions.extend(_extract_questions(item.get("text", "")))

    current_questions = _extract_questions(reply)
    if len(current_questions) > 1:
        issues.append("more_than_one_question")

    if any(question in assistant_questions for question in current_questions if question):
        issues.append("repeated_question")

    if any(re.search(pattern, reply, flags=re.IGNORECASE) for pattern in USER_GENDER_PATTERNS):
        issues.append("assumed_user_gender")

    if any(re.search(pattern, reply, flags=re.IGNORECASE) for pattern in AWKWARD_PATTERNS):
        issues.append("awkward_phrase")

    if len(re.findall(r"[a-zA-Zа-яА-ЯёЁ0-9-]+", user_message or "")) <= 3 and len(current_questions) >= 1:
        issues.append("question_after_minimal_reply")

    if any(re.search(pattern, user_message or "", flags=re.IGNORECASE) for pattern in MEMORY_CHECK_PATTERNS) and len(current_questions) >= 1:
        issues.append("followup_after_memory_check")

    return issues


def refine_reply(reply: str, user_message: str, history: list, mode: str = "chat") -> str:
    clean_reply = sanitize_reply(reply)
    if mode != "chat":
        return clean_reply

    issues = detect_reply_issues(clean_reply, history, user_message)
    if not issues:
        return clean_reply

    logger.info(f"[ReplyGuard] Найдены проблемы в ответе: {issues}")
    history_text = "\n".join(
        f"{item.get('role', 'user')}: {item.get('text', '')}" for item in history[-6:]
    )
    prompt = f"""
Перепиши реплику Светланы так, чтобы она звучала естественно и по-человечески.

Правила:
- Светлана всегда говорит о себе только в женском роде.
- Если пол пользователя не подтверждён, не обращайся к нему в мужском или женском роде.
- Сохрани смысл исходной реплики, но убери неестественность.
- Не повторяй предыдущие вопросы дословно.
- Не задавай больше одного вопроса.
- Если пользователь ответил очень коротко, лучше без нового вопроса или с очень лёгким поворотом темы.
- Ответ короткий, живой, как в мессенджере.
- Верни только готовую реплику.

Проблемы исходной реплики: {", ".join(issues)}

Последние сообщения:
{history_text}

Сообщение пользователя:
{user_message}

Исходная реплика Светланы:
{clean_reply}
""".strip()

    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=120,
        )
        rewritten = response.choices[0].message.content.strip()
        return sanitize_reply(rewritten) or clean_reply
    except Exception as exc:
        logger.warning(f"[ReplyGuard] Не удалось переписать ответ: {exc}")
        return clean_reply
