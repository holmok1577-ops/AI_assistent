from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from app.db import SessionLocal
from app.models import Meeting, Reminder
from app.telegram_bot import send_meeting_reminder, send_reminder
import logging

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def check_meeting_reminders():
    """Проверяет и отправляет напоминания о встречах"""
    db = SessionLocal()
    try:
        now = datetime.now()
        # Встречи в ближайшие 24 часа, которым ещё не отправлено напоминание
        upcoming = db.query(Meeting).filter(
            Meeting.datetime >= now,
            Meeting.datetime <= now + timedelta(hours=24),
            Meeting.reminder_sent == False
        ).all()
        
        for meeting in upcoming:
            try:
                datetime_str = meeting.datetime.strftime("%Y-%m-%d %H:%M")
                success = send_meeting_reminder(meeting.title, datetime_str, meeting.location)
                if success:
                    meeting.reminder_sent = True
                    db.commit()
                    logger.info(f"[Scheduler] Напоминание отправлено для встречи {meeting.id}")
            except Exception as e:
                logger.error(f"[Scheduler] Ошибка отправки напоминания: {e}")
    finally:
        db.close()

def check_reminders():
    """Проверяет и отправляет простые напоминания"""
    db = SessionLocal()
    try:
        now = datetime.now()
        # Напоминания в ближайшие 24 часа, которым ещё не отправлено
        upcoming = db.query(Reminder).filter(
            Reminder.datetime >= now,
            Reminder.datetime <= now + timedelta(hours=24),
            Reminder.sent == False
        ).all()
        
        for reminder in upcoming:
            try:
                datetime_str = reminder.datetime.strftime("%Y-%m-%d %H:%M")
                success = send_reminder(reminder.text, datetime_str)
                if success:
                    reminder.sent = True
                    db.commit()
                    logger.info(f"[Scheduler] Напоминание отправлено для reminder {reminder.id}")
            except Exception as e:
                logger.error(f"[Scheduler] Ошибка отправки напоминания: {e}")
    finally:
        db.close()

def start_scheduler():
    """Запускает планировщик"""
    scheduler.add_job(
        check_meeting_reminders,
        trigger=IntervalTrigger(minutes=10),
        id='check_meetings',
        name='Check meeting reminders',
        replace_existing=True
    )
    
    scheduler.add_job(
        check_reminders,
        trigger=IntervalTrigger(minutes=10),
        id='check_reminders',
        name='Check reminders',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("[Scheduler] Планировщик запущен")

def stop_scheduler():
    """Останавливает планировщик"""
    scheduler.shutdown()
    logger.info("[Scheduler] Планировщик остановлен")
