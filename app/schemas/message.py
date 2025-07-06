"""
Message schemas for talkroom messages and message operations.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.message import MessageType


class MessageBase(BaseModel):
    """Base message schema."""
    content: str = Field(..., min_length=1, max_length=10000, description="Message content")
    message_type: MessageType = Field(default=MessageType.TEXT, description="Message type")
    reply_to_id: Optional[int] = Field(None, description="ID of message being replied to")


class MessageCreate(MessageBase):
    """Message creation schema."""
    talkroom_id: int = Field(..., description="Talkroom ID")


class MessageUpdate(BaseModel):
    """Message update schema."""
    content: str = Field(..., min_length=1, max_length=10000, description="Updated message content")


class MessageFile(BaseModel):
    """File message schema."""
    file_url: str = Field(..., description="File URL")
    file_name: str = Field(..., description="Original file name")
    file_size: int = Field(..., description="File size in bytes")
    message_type: MessageType = Field(..., description="Message type")


class MessageResponse(BaseModel):
    """Message response schema."""
    id: int = Field(..., description="Message ID")
    talkroom_id: int = Field(..., description="Talkroom ID")
    sender_id: int = Field(..., description="Sender user ID")
    content: str = Field(..., description="Message content")
    message_type: MessageType = Field(..., description="Message type")
    file_url: Optional[str] = Field(None, description="File URL")
    file_name: Optional[str] = Field(None, description="Original file name")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    is_edited: bool = Field(..., description="Whether message was edited")
    edited_at: Optional[datetime] = Field(None, description="Edit timestamp")
    reply_to_id: Optional[int] = Field(None, description="ID of message being replied to")
    is_deleted: bool = Field(..., description="Whether message was deleted")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")
    created_at: datetime = Field(..., description="Message creation timestamp")
    updated_at: datetime = Field(..., description="Message update timestamp")
    
    # Sender information
    sender: Optional[dict] = Field(None, description="Sender user information")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class MessageListResponse(BaseModel):
    """Message list response schema."""
    messages: list[MessageResponse] = Field(..., description="List of messages")
    total: int = Field(..., description="Total number of messages")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Messages per page")
    has_next: bool = Field(..., description="Whether there are more messages")
    has_prev: bool = Field(..., description="Whether there are previous messages")


class MessageWebSocket(BaseModel):
    """WebSocket message schema."""
    type: str = Field(..., description="Message type (message, typing, join, leave)")
    talkroom_id: int = Field(..., description="Talkroom ID")
    data: dict = Field(..., description="Message data")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True 