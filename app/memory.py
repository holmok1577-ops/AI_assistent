import re

from app.db import SessionLocal
from app.models import UserProfile, User

def get_or_create_user(external_id: str):
    db = SessionLocal()
    user = db.query(User).filter_by(external_id=external_id).first()

    if not user:
        user = User(
            external_id=external_id,
            profile={}
        )
        db.add(user)
        db.commit()

    return user

def remember_fact(user_id: str, fact: str):
    db = SessionLocal()
    profile = db.query(UserProfile).filter_by(user_id=user_id).first()

    if not profile:
        profile = UserProfile(user_id=user_id, facts=[])
        db.add(profile)

    facts = profile.facts
    if fact not in facts:
        facts.append(fact)

    profile.facts = facts
    db.commit()


def extract_user_name(message: str) -> str | None:
    text = (message or "").strip()
    patterns = [
        r"(?:меня зовут|я\s+[-—]?\s*)([А-ЯA-ZЁ][а-яa-zё-]{1,30})",
        r"(?:мо[её]\s+имя)\s+([А-ЯA-ZЁ][а-яa-zё-]{1,30})",
        r"^([А-ЯA-ZЁ][а-яa-zё-]{1,30})$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip().capitalize()
    return None


def save_user_name(user_id: str, user_name: str):
    if not user_name:
        return

    db = SessionLocal()
    try:
        profile = db.query(UserProfile).filter_by(user_id=user_id).first()
        if not profile:
            profile = UserProfile(user_id=user_id, facts=[])
            db.add(profile)

        facts = profile.facts or []
        facts = [fact for fact in facts if not fact.startswith("Имя пользователя: ")]
        facts.insert(0, f"Имя пользователя: {user_name}")
        profile.facts = facts[:20]
        db.commit()
    finally:
        db.close()


def get_user_name(user_id: str) -> str | None:
    facts = get_user_facts(user_id)
    for fact in facts:
        if fact.startswith("Имя пользователя: "):
            return fact.split(": ", 1)[1].strip()
    return None


def get_user_facts(user_id: str):
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).filter_by(user_id=user_id).first()
        return profile.facts if profile else []
    finally:
        db.close()
