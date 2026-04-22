import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/svetlana")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
PROXYAPI_KEY = os.getenv("PROXYAPI_KEY")
PROXYAPI_BASE_URL = "https://api.proxyapi.ru/openai/v1"
ASSISTANT_ID = os.getenv("ASSISTANT_ID")
VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
