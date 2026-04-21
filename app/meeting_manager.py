from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Meeting, Reminder
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def create_meeting(user_id, title, datetime_str, location="", description=""):
    db = SessionLocal()
    try:
        meeting_datetime = datetime.fromisoformat(datetime_str)
        meeting = Meeting(user_id=user_id, title=title, datetime=meeting_datetime, location=location, description=description)
        db.add(meeting)
        db.commit()
        return {"id": meeting.id, "title": title}
    except Exception as e:
        logger.error(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def get_user_meetings(user_id):
    db = SessionLocal()
    try:
        meetings = db.query(Meeting).filter_by(user_id=user_id).all()
        return [{"id": m.id, "title": m.title, "datetime": m.datetime.isoformat()} for m in meetings]
    finally:
        db.close()

def delete_meeting(meeting_id):
    db = SessionLocal()
    try:
        meeting = db.query(Meeting).filter_by(id=meeting_id).first()
        if meeting:
            db.delete(meeting)
            db.commit()
            return True
        return False
    finally:
        db.close()
