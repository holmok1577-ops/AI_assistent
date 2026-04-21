from sqlalchemy import Column, Integer, Float, String, JSON, Text, DateTime, Boolean
from sqlalchemy.sql import func
from app.db import Base

class MemoryShard(Base):
    __tablename__ = "memory_shards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, index=True)
    content = Column(Text)
    embedding = Column(JSON)

class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id = Column(String, primary_key=True)
    facts = Column(JSON, default=list)

class EmotionalState(Base):
    __tablename__ = "emotional_state"

    user_id = Column(String, primary_key=True)
    calm = Column(Float, default=70)
    joy = Column(Float, default=50)
    romantic = Column(Float, default=20)
    nervous = Column(Float, default=10)
    tired = Column(Float, default=20)

class RelationshipState(Base):
    __tablename__ = "relationship_state"

    user_id = Column(String, primary_key=True)
    trust = Column(Float, default=20)
    closeness = Column(Float, default=10)
    sympathy = Column(Float, default=15)
    openness = Column(Float, default=5)

class SvetlanaStory(Base):
    __tablename__ = "svetlana_story"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String)
    story_event = Column(String)

class UserThread(Base):
    __tablename__ = "user_threads"

    user_id = Column(String, primary_key=True)
    thread_id = Column(String)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(String, unique=True)
    name = Column(String)
    profile = Column(JSON, default=dict)

class UserMode(Base):
    __tablename__ = "user_modes"

    user_id = Column(String, primary_key=True)
    mode = Column(String, default="chat")  # "chat" или "secretary"
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, index=True)
    title = Column(String)
    datetime = Column(DateTime)
    location = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    reminder_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, index=True)
    text = Column(Text)
    datetime = Column(DateTime)
    sent = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
