from openai import OpenAI
from app.config import OPENAI_API_KEY
import logging

logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY, default_headers={"OpenAI-Beta": "assistants=v2"})

def run_assistant(message: str, system_context: str):
    logger.info(f"[OpenAI] Отправка запроса к GPT-4o-mini")
    logger.info(f"[OpenAI] Длина system_context: {len(system_context)} символов")
    logger.info(f"[OpenAI] Длина message: {len(message)} символов")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_context},
                {"role": "user", "content": message}
            ],
            temperature=1.2,
            top_p=0.9,
            presence_penalty=0.6,
            frequency_penalty=0.6
        )
        reply = response.choices[0].message.content
        logger.info(f"[OpenAI] Ответ получен, длина: {len(reply)} символов")
        return reply
    except Exception as e:
        logger.error(f"[OpenAI] Ошибка: {str(e)}")
        raise
