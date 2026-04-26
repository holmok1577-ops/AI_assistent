from app.db import SessionLocal
from app.models import RelationshipState
from app.sentiment import detect_tone

def update_relationship(user_id: str, message: str, tone: str = None, affect_profile: dict | None = None):
    db = SessionLocal()
    rel = db.query(RelationshipState).filter_by(user_id=user_id).first()

    if not rel:
        rel = RelationshipState(user_id=user_id)
        db.add(rel)
        db.commit()
        db.refresh(rel)

    tone = tone or detect_tone(message)
    affect_profile = affect_profile or {}

    if tone == "friendly":
        rel.trust += 3
        rel.closeness += 2
        rel.sympathy += 4

    elif tone == "warm":
        rel.trust += 5
        rel.closeness += 5
        rel.sympathy += 7
        rel.openness += 2

    elif tone == "playful":
        rel.closeness += 4
        rel.sympathy += 4
        rel.openness += 2

    elif tone == "flirty":
        rel.sympathy += 10
        rel.closeness += 8
        rel.openness += 4

    elif tone == "angry":
        rel.trust -= 5
        rel.closeness -= 4

    elif tone == "insult":
        rel.sympathy -= 12
        rel.trust -= 9
        rel.closeness -= 6
        rel.openness -= 2

    elif tone == "profane":
        rel.sympathy -= 10
        rel.trust -= 4
        rel.closeness -= 3

    elif tone == "aggressive_profane":
        rel.sympathy -= 18
        rel.trust -= 8
        rel.closeness -= 5
        rel.openness -= 2

    elif tone == "sad":
        rel.trust += 3
        rel.sympathy += 2

    elif tone == "apologetic":
        rel.sympathy += 15  # Быстрое восстановление симпатии
        rel.trust += 10
        rel.closeness += 5

    elif tone == "robot_question":
        rel.sympathy -= 2  # Небольшое снижение симпатии
        rel.trust -= 1

    if affect_profile.get("hostile_recent", 0) >= 2:
        rel.sympathy -= 4
        rel.trust -= 3

    if affect_profile.get("hostile_streak", 0) >= 3:
        rel.closeness -= 3
        rel.openness -= 2

    if affect_profile.get("positive_recent", 0) >= 2:
        rel.sympathy += 3
        rel.trust += 2

    if affect_profile.get("positive_streak", 0) >= 3:
        rel.closeness += 3
        rel.openness += 2

    if affect_profile.get("playful_recent", 0) >= 2:
        rel.closeness += 2
        rel.sympathy += 2

    # clamp values
    for field in ["trust", "closeness", "sympathy", "openness"]:
        v = getattr(rel, field)
        setattr(rel, field, max(0, min(100, v)))

    db.commit()

    # Возвращаем словарь значений до закрытия сессии
    result = {
        "trust": rel.trust,
        "closeness": rel.closeness,
        "sympathy": rel.sympathy,
        "openness": rel.openness
    }

    db.close()
    return result

def get_relationship_values(user_id: str) -> dict:
    """Получает текущие значения отношений без изменений"""
    db = SessionLocal()
    rel = db.query(RelationshipState).filter_by(user_id=user_id).first()
    
    if not rel:
        db.close()
        return {
            "trust": 20,
            "closeness": 10,
            "sympathy": 40,
            "openness": 5
        }
    
    result = {
        "trust": rel.trust,
        "closeness": rel.closeness,
        "sympathy": rel.sympathy,
        "openness": rel.openness
    }
    db.close()
    return result
