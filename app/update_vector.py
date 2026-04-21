import os
from openai import OpenAI
from app.config import OPENAI_API_KEY, VECTOR_STORE_ID
import logging

logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY, default_headers={"OpenAI-Beta": "assistants=v2"})

def update_vector_store(vector_store_id: str = None):
    """Обновляет vector store файлами из папки persona"""
    if vector_store_id is None:
        vector_store_id = VECTOR_STORE_ID

    if not vector_store_id:
        logger.error("[Vector Store] VECTOR_STORE_ID не установлен")
        return {"error": "VECTOR_STORE_ID не установлен"}

    persona_dir = "persona"
    if not os.path.exists(persona_dir):
        logger.warning(f"[Vector Store] Папка {persona_dir} не существует")
        return {"error": f"Папка {persona_dir} не существует"}

    files = []
    for filename in os.listdir(persona_dir):
        if filename.endswith('.txt'):
            path = os.path.join(persona_dir, filename)
            files.append(open(path, "rb"))
            logger.info(f"[Vector Store] Добавлен файл: {filename}")

    if not files:
        logger.warning("[Vector Store] Нет .txt файлов в папке persona")
        return {"error": "Нет .txt файлов"}

    try:
        file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store_id,
            files=files
        )
        logger.info(f"[Vector Store] Загружено: {file_batch.file_counts}")
        return {
            "status": "success",
            "file_counts": file_batch.file_counts,
            "message": f"Загружено {file_batch.file_counts.total_files} файлов"
        }
    except Exception as e:
        logger.error(f"[Vector Store] Ошибка: {str(e)}")
        return {"error": str(e)}
