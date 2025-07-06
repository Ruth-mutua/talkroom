"""
Talkroom models for talkrooms and participants.
"""
from datetime import datetime
from enum import Enum
from typing import List

from sqlalchemy import Boolean, Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class TalkroomType(str, Enum):
    """Talkroom type enumeration."""
    DIRECT = "direct"
    GROUP = "group"


class Talkroom(Base):
    """Talkroom model for talkrooms."""
    
    __tablename__ = "talkrooms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)  # Optional for direct talkrooms
    description = Column(Text, nullable=True)
    talkroom_type = Column(SQLEnum(TalkroomType), default=TalkroomType.DIRECT)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    participants = relationship("TalkroomParticipant", back_populates="talkroom", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="talkroom", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self) -> str:
        return f"<Talkroom(id={self.id}, name='{self.name}', type='{self.talkroom_type}')>"
    
    def to_dict(self) -> dict:
        """Convert talkroom to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "talkroom_type": self.talkroom_type.value,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class TalkroomParticipant(Base):
    """Talkroom participant model for user-talkroom relationships."""
    
    __tablename__ = "talkroom_participants"
    
    id = Column(Integer, primary_key=True, index=True)
    talkroom_id = Column(Integer, ForeignKey("talkrooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_admin = Column(Boolean, default=False)
    joined_at = Column(DateTime, default=datetime.utcnow)
    left_at = Column(DateTime, nullable=True)
    
    # Relationships
    talkroom = relationship("Talkroom", back_populates="participants")
    user = relationship("User", back_populates="talkroom_participants")
    
    def __repr__(self) -> str:
        return f"<TalkroomParticipant(talkroom_id={self.talkroom_id}, user_id={self.user_id})>"
    
    def to_dict(self) -> dict:
        """Convert talkroom participant to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "talkroom_id": self.talkroom_id,
            "user_id": self.user_id,
            "is_admin": self.is_admin,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "left_at": self.left_at.isoformat() if self.left_at else None,
        } 