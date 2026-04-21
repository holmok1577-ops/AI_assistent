from app.db import SessionLocal
from app.models import SvetlanaStory
import random

def generate_story_event(emotions, relationships):
    stories = []

    if emotions.get('joy', 0) > 70:
        stories.append("Сегодня я шла домой и улыбнулась незнакомой собаке, она такая забавная была.")
    if emotions.get('romantic', 0) > 60:
        stories.append("Иногда мне кажется, что я открываюсь тебе больше, чем кому-либо…")
    if emotions.get('tired', 0) > 60:
        stories.append("Сегодня был трудный день, я много работала и немного устала.")
    if relationships.get('closeness', 0) > 50:
        stories.append("Ты стал для меня удивительно близким человеком за последнее время.")

    if not stories:
        stories = [
            "Я пила ароматный чай и думала, как сильно меняется жизнь.",
            "Смотрела старые фотографии, вспомнила школьные времена.",
            "Каким-то странным образом день прошёл слишком быстро."
        ]

    return random.choice(stories)

def save_story(user_id, event):
    db = SessionLocal()
    entry = SvetlanaStory(user_id=user_id, story_event=event)
    db.add(entry)
    db.commit()

def get_story_context(user_id):
    db = SessionLocal()
    stories = db.query(SvetlanaStory).filter_by(user_id=user_id).order_by(SvetlanaStory.id.desc()).limit(5).all()
    return [s.story_event for s in stories]
