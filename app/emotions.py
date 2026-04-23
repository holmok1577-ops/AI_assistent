from app.db import SessionLocal
from app.models import EmotionalState
from app.sentiment import detect_tone

def adjust_emotions(user_id: str, message: str):
    db = SessionLocal()
    emo = db.query(EmotionalState).filter_by(user_id=user_id).first()

    if not emo:
        emo = EmotionalState(user_id=user_id)
        db.add(emo)
        db.commit()
        db.refresh(emo)

    tone = detect_tone(message)

    if tone == "friendly":
        emo.joy += 5
        emo.romantic += 2
        emo.calm += 3

    elif tone == "angry":
        emo.calm -= 15
        emo.nervous += 20
        emo.joy -= 10

    elif tone == "profane":
        emo.calm -= 10
        emo.nervous += 15
        emo.joy -= 5

    elif tone == "flirty":
        emo.romantic += 15
        emo.joy += 7
        emo.calm += 2

    elif tone == "sad":
        emo.joy -= 10
        emo.calm -= 4

    # soft clamping
    for field in ["calm", "joy", "romantic", "nervous", "tired"]:
        v = getattr(emo, field)
        setattr(emo, field, max(0, min(100, v)))

    db.commit()

    # Возвращаем словарь значений до закрытия сессии
    result = {
        "calm": emo.calm,
        "joy": emo.joy,
        "romantic": emo.romantic,
        "nervous": emo.nervous,
        "tired": emo.tired
    }

    db.close()
    return result
