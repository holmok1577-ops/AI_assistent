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

def get_user_facts(user_id: str):
    db = SessionLocal()
    profile = db.query(UserProfile).filter_by(user_id=user_id).first()
    return profile.facts if profile else []
