import logging
from app.db import SessionLocal
from app.models import EmotionalState
from app.sentiment import detect_tone

logger = logging.getLogger(__name__)

def adjust_emotions(user_id: str, message: str, tone: str = None, affect_profile: dict | None = None):
    db = SessionLocal()
    emo = db.query(EmotionalState).filter_by(user_id=user_id).first()

    if not emo:
        emo = EmotionalState(user_id=user_id)
        db.add(emo)
        db.commit()
        db.refresh(emo)

    tone = tone or detect_tone(message)
    affect_profile = affect_profile or {}

    if tone == "friendly":
        emo.joy += 4
        emo.romantic += 2
        emo.calm += 3
        emo.nervous -= 2

    elif tone == "warm":
        emo.joy += 7
        emo.romantic += 4
        emo.calm += 6
        emo.nervous -= 4

    elif tone == "playful":
        emo.joy += 6
        emo.calm += 3
        emo.nervous -= 2

    elif tone == "angry":
        emo.calm -= 8
        emo.nervous += 10
        emo.joy -= 6

    elif tone == "profane":
        emo.calm -= 16
        emo.nervous += 20
        emo.joy -= 10

    elif tone == "aggressive_profane":
        emo.calm -= 26
        emo.nervous += 32
        emo.joy -= 16

    elif tone == "insult":
        emo.calm -= 18
        emo.nervous += 24
        emo.joy -= 12

    elif tone == "flirty":
        emo.romantic += 15
        emo.joy += 7
        emo.calm += 2

    elif tone == "sad":
        emo.joy -= 10
        emo.calm -= 4

    elif tone == "apologetic":
        if affect_profile.get("hostile_recent", 0) >= 2:
            emo.calm += 10
            emo.nervous -= 12
            emo.joy += 2
        else:
            emo.calm += 20  # Быстрое восстановление спокойствия
            emo.nervous -= 25  # Быстрое снижение нервозности
            emo.joy += 5

    elif tone == "robot_question":
        emo.calm -= 2  # Небольшое снижение спокойствия
        emo.nervous += 3  # Небольшое повышение нервозности
        emo.joy -= 2

    elif tone == "neutral":
        # Естественный дрейф назад к базовому спокойному состоянию
        if emo.nervous > 12:
            emo.nervous -= 2
        if emo.calm < 70:
            emo.calm += 1
        if emo.joy < 50:
            emo.joy += 1

    if affect_profile.get("hostile_recent", 0) >= 2:
        emo.calm -= 4
        emo.nervous += 6
        emo.joy -= 3

    if affect_profile.get("hostile_streak", 0) >= 3:
        emo.calm -= 5
        emo.nervous += 8

    if affect_profile.get("positive_recent", 0) >= 2:
        emo.calm += 3
        emo.joy += 4
        emo.nervous -= 2

    if affect_profile.get("positive_streak", 0) >= 3:
        emo.calm += 4
        emo.joy += 5
        emo.romantic += 2

    if affect_profile.get("playful_recent", 0) >= 2:
        emo.joy += 3
        emo.calm += 2

    if affect_profile.get("playful_streak", 0) >= 3:
        emo.joy += 4
        emo.romantic += 1

    # soft clamping
    for field in ["calm", "joy", "romantic", "nervous", "tired"]:
        v = getattr(emo, field)
        setattr(emo, field, max(0, min(100, v)))

    # Проверка на блокировку (симпатия < 1, нервозность > 99, спокойствие < 1)
    from app.relationship import get_relationship_values
    rel = get_relationship_values(user_id)
    if rel['sympathy'] < 1 and emo.nervous > 99 and emo.calm < 1:
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
