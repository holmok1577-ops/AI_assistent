from openai import OpenAI
from sqlalchemy.orm import Session
from app.models import MemoryShard
from app.db import SessionLocal
from app.config import OPENAI_API_KEY, OPENAI_BASE_URL
import numpy as np

client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL, default_headers={"OpenAI-Beta": "assistants=v2"})

def embed(text: str):
    r = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return r.data[0].embedding

def save_memory(user_id: str, text: str):
    db = SessionLocal()
    vec = embed(text)

    shard = MemoryShard(user_id=user_id, content=text, embedding=vec)
    db.add(shard)
    db.commit()

def search_memory(user_id: str, query: str, limit=5):
    db = SessionLocal()
    q_vec = embed(query)

    memories = db.query(MemoryShard).filter_by(user_id=user_id).all()

    def cosine(a, b):
        a, b = np.array(a), np.array(b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    scored = [
        (cosine(q_vec, m.embedding), m.content)
        for m in memories
    ]

    scored.sort(key=lambda x: x[0], reverse=True)
    return [m[1] for m in scored[:limit]]
