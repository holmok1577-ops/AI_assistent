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
        emo.calm -= 25  # Усилено с 10 до 25
        emo.nervous += 30  # Усилено с 15 до 30
        emo.joy -= 15  # Усилено с 5 до 15

    elif tone == "flirty":
        emo.romantic += 15
        emo.joy += 7
        emo.calm += 2

    elif tone == "sad":
        emo.joy -= 10
        emo.calm -= 4

    elif tone == "apologetic":
        emo.calm += 20  # Быстрое восстановление спокойствия
        emo.nervous -= 25  # Быстрое снижение нервозности
        emo.joy += 5

    # soft clamping
    for field in ["calm", "joy", "romantic", "nervous", "tired"]:
        v = getattr(emo, field)
        setattr(emo, field, max(0, min(100, v)))

    # Проверка на блокировку (симпатия 0, нервозность 100, спокойствие 0)
    from app.relationship import get_relationship_values
    rel = get_relationship_values(user_id)
    if rel['sympathy'] <= 0 and emo.nervous >= 100 and emo.calm <= 0:
        # Если это первый раз - ставим флаг для грубого ответа
        if not emo.first_extreme_response:
            emo.first_extreme_response = True
            logger.info(f"[EXTREME] Первый раз в крайней ярости - будет грубый ответ")
        else:
            # После первого грубого ответа - блокируем
            emo.is_blocked = True
            logger.info(f"[BLOCK] Пользователь {user_id} заблокирован (крайняя ярость)")
    # Проверка на разблокировку (симпатия > 10, нервозность < 90, спокойствие > 10)
    elif rel['sympathy'] > 10 and emo.nervous < 90 and emo.calm > 10:
        if emo.is_blocked:
            emo.is_blocked = False
            emo.first_extreme_response = False  # Сбрасываем флаг
            logger.info(f"[UNBLOCK] Пользователь {user_id} разблокирован")

    db.commit()

    # Возвращаем словарь значений до закрытия сессии
    result = {
        "calm": emo.calm,
        "joy": emo.joy,
        "romantic": emo.romantic,
        "nervous": emo.nervous,
        "tired": emo.tired,
        "is_blocked": emo.is_blocked
    }

    db.close()
    return result
