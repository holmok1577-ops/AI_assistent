from openai import OpenAI
from app.config import CHAT_MODEL, OPENAI_API_KEY, OPENAI_BASE_URL

client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL, default_headers={"OpenAI-Beta": "assistants=v2"})

def score_response(user_msg: str, assistant_msg: str):
    prompt = f"""
Оцени, насколько ответ ассистента был тёплым, человечным, эмоциональным.
Сообщение пользователя: {user_msg}
Ответ ассистента: {assistant_msg}

Выведи число от 1 до 10.
"""

    r = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=5
    )

    try:
        score = int(r.choices[0].message.content.strip())
        return max(1, min(score, 10))
    except:
        return 5
