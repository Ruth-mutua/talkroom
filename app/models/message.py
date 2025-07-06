"""
Message model for talkroom messages.
"""
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class MessageType(str, Enum):
    """Message type enumeration."""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"


class Message(Base):
    """Message model for talkroom messages."""
    
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    talkroom_id = Column(Integer, ForeignKey("talkrooms.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(SQLEnum(MessageType), default=MessageType.TEXT)
    file_url = Column(String(500), nullable=True)  # For file/image messages
    file_name = Column(String(255), nullable=True)  # Original file name
    file_size = Column(Integer, nullable=True)  # File size in bytes
    is_edited = Column(Boolean, default=False)
    edited_at = Column(DateTime, nullable=True)
    reply_to_id = Column(Integer, ForeignKey("messages.id"), nullable=True)  # For replies
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    talkroom = relationship("Talkroom", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    reply_to = relationship("Message", remote_side=[id])
    
    def __repr__(self) -> str:
        return f"<Message(id={self.id}, talkroom_id={self.talkroom_id}, sender_id={self.sender_id})>"
    
    def to_dict(self) -> dict:
        """Convert message to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "talkroom_id": self.talkroom_id,
            "sender_id": self.sender_id,
            "content": self.content,
            "message_type": self.message_type.value,
            "file_url": self.file_url,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "is_edited": self.is_edited,
            "edited_at": self.edited_at.isoformat() if self.edited_at else None,
            "reply_to_id": self.reply_to_id,
            "is_deleted": self.is_deleted,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        } 