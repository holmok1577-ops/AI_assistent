from app.db import SessionLocal
from app.models import RelationshipState
from app.sentiment import detect_tone

def update_relationship(user_id: str, message: str):
    db = SessionLocal()
    rel = db.query(RelationshipState).filter_by(user_id=user_id).first()

    if not rel:
        rel = RelationshipState(user_id=user_id)
        db.add(rel)
        db.commit()
        db.refresh(rel)

    tone = detect_tone(message)

    if tone == "friendly":
        rel.trust += 4
        rel.closeness += 3
        rel.sympathy += 5

    elif tone == "flirty":
        rel.sympathy += 10
        rel.closeness += 8
        rel.openness += 4

    elif tone == "angry":
        rel.trust -= 8
        rel.closeness -= 6

    elif tone == "profane":
        rel.sympathy -= 15
        rel.trust -= 5
        rel.closeness -= 3

    elif tone == "sad":
        rel.trust += 3
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
