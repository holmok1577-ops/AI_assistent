import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import PROXYAPI_KEY, PROXYAPI_BASE_URL
from dotenv import load_dotenv
from app.persona_instructions import ASSISTANT_INSTRUCTIONS

load_dotenv()

client = OpenAI(
    api_key=PROXYAPI_KEY,
    base_url=PROXYAPI_BASE_URL,
    default_headers={"OpenAI-Beta": "assistants=v2"}
)

print("=== Создание Vector Store ===")
vector_store = client.beta.vector_stores.create(name="svetlana_persona")
print(f"Vector Store создан: {vector_store.id}")

print("\n=== Загрузка файлов ===")
files = []
for filename in os.listdir("persona"):
    if filename.endswith('.txt'):
        path = os.path.join("persona", filename)
        files.append(open(path, "rb"))
        print(f"Добавлен: {filename}")

file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
    vector_store_id=vector_store.id,
    files=files
)
print(f"\nЗагружено файлов: {file_batch.file_counts.total_files}")

print("\n=== Создание Assistant ===")
assistant = client.beta.assistants.create(
    name="Светлана",
    instructions=ASSISTANT_INSTRUCTIONS,
    model="gpt-4o-mini",
    temperature=0.8,
    tools=[{"type": "file_search"}],
    tool_resources={
        "file_search": {
            "vector_store_ids": [vector_store.id]
        }
    }
)
print(f"Assistant создан: {assistant.id}")

print("\n=== Обновление .env ===")
with open(".env", "a") as f:
    f.write(f"\nASSISTANT_ID={assistant.id}")
    f.write(f"\nVECTOR_STORE_ID={vector_store.id}")

print("\n=== ГОТОВО ===")
print(f"Добавь в .env:")
print(f"ASSISTANT_ID={assistant.id}")
print(f"VECTOR_STORE_ID={vector_store.id}")
