"""
Talkroom API endpoints for talkroom management and message operations.
"""
from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.talkroom import Talkroom, TalkroomParticipant, TalkroomType
from app.models.message import Message
from app.models.user import User
from app.schemas.message import MessageCreate, MessageListResponse, MessageResponse, MessageUpdate
from app.utils.dependencies import get_current_active_user
from app.utils.exceptions import (
    TalkroomNotFoundException,
    MessageNotFoundException,
    UnauthorizedAccessException,
    UserNotFoundException,
)

router = APIRouter()


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_talkroom(
    other_user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new direct talkroom with another user.
    
    Args:
        other_user_id: ID of the other user
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created talkroom information
        
    Raises:
        UserNotFoundException: If other user not found
    """
    # Check if other user exists
    other_user = db.query(User).filter(User.id == other_user_id).first()
    if not other_user:
        raise UserNotFoundException("Other user not found")
    
    # Check if talkroom already exists between these users
    existing_talkroom = db.query(Talkroom).join(TalkroomParticipant).filter(
        Talkroom.talkroom_type == TalkroomType.DIRECT,
        TalkroomParticipant.user_id.in_([current_user.id, other_user_id])
    ).group_by(Talkroom.id).having(
        db.func.count(TalkroomParticipant.id) == 2
    ).first()
    
    if existing_talkroom:
        # Check if current user is participant
        participant = db.query(TalkroomParticipant).filter(
            TalkroomParticipant.talkroom_id == existing_talkroom.id,
            TalkroomParticipant.user_id == current_user.id
        ).first()
        
        if participant:
            return {
                "id": existing_talkroom.id,
                "message": "Talkroom already exists",
                "exists": True
            }
    
    # Create new talkroom
    talkroom = Talkroom(
        talkroom_type=TalkroomType.DIRECT,
        created_by=current_user.id,
        is_active=True
    )
    
    db.add(talkroom)
    db.commit()
    db.refresh(talkroom)
    
    # Add participants
    participant1 = TalkroomParticipant(
        talkroom_id=talkroom.id,
        user_id=current_user.id
    )
    participant2 = TalkroomParticipant(
        talkroom_id=talkroom.id,
        user_id=other_user_id
    )
    
    db.add_all([participant1, participant2])
    db.commit()
    
    return {
        "id": talkroom.id,
        "message": "Talkroom created successfully",
        "exists": False
    }


@router.get("/", response_model=List[dict])
def get_user_talkrooms(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all talkrooms for the current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of user's talkrooms
    """
    # Get user's talkroom participations
    participations = db.query(TalkroomParticipant).filter(
        TalkroomParticipant.user_id == current_user.id,
        TalkroomParticipant.left_at.is_(None)
    ).all()
    
    talkrooms = []
    for participation in participations:
        talkroom = participation.talkroom
        
        # Get other participants for direct talkrooms
        other_participants = db.query(TalkroomParticipant).join(User).filter(
            TalkroomParticipant.talkroom_id == talkroom.id,
            TalkroomParticipant.user_id != current_user.id
        ).all()
        
        # Get latest message
        latest_message = db.query(Message).filter(
            Message.talkroom_id == talkroom.id,
            Message.is_deleted == False
        ).order_by(Message.created_at.desc()).first()
        
        talkroom_data = {
            "id": talkroom.id,
            "name": talkroom.name,
            "talkroom_type": talkroom.talkroom_type.value,
            "is_active": talkroom.is_active,
            "created_at": talkroom.created_at.isoformat(),
            "updated_at": talkroom.updated_at.isoformat(),
            "other_participants": [
                {
                    "id": p.user.id,
                    "username": p.user.username,
                    "full_name": p.user.full_name,
                    "avatar_url": p.user.avatar_url,
                    "last_seen": p.user.last_seen.isoformat() if p.user.last_seen else None
                }
                for p in other_participants
            ],
            "latest_message": {
                "id": latest_message.id,
                "content": latest_message.content,
                "sender_id": latest_message.sender_id,
                "created_at": latest_message.created_at.isoformat(),
                "message_type": latest_message.message_type.value
            } if latest_message else None
        }
        
        talkrooms.append(talkroom_data)
    
    return talkrooms


@router.get("/{talkroom_id}/messages", response_model=MessageListResponse)
def get_talkroom_messages(
    talkroom_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Messages per page"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get messages for a specific talkroom.
    
    Args:
        talkroom_id: Talkroom ID
        page: Page number
        per_page: Messages per page
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Paginated list of messages
        
    Raises:
        TalkroomNotFoundException: If talkroom not found
        UnauthorizedAccessException: If user not in talkroom
    """
    # Check if talkroom exists
    talkroom = db.query(Talkroom).filter(Talkroom.id == talkroom_id).first()
    if not talkroom:
        raise TalkroomNotFoundException("Talkroom not found")
    
    # Check if user is participant
    participant = db.query(TalkroomParticipant).filter(
        TalkroomParticipant.talkroom_id == talkroom_id,
        TalkroomParticipant.user_id == current_user.id
    ).first()
    
    if not participant:
        raise UnauthorizedAccessException("You are not a participant in this talkroom")
    
    # Get messages with pagination
    offset = (page - 1) * per_page
    
    messages_query = db.query(Message).filter(
        Message.talkroom_id == talkroom_id,
        Message.is_deleted == False
    ).order_by(Message.created_at.desc())
    
    total = messages_query.count()
    messages = messages_query.offset(offset).limit(per_page).all()
    
    # Convert to response format
    message_responses = []
    for message in messages:
        message_data = MessageResponse(
            id=message.id,
            talkroom_id=message.talkroom_id,
            sender_id=message.sender_id,
            content=message.content,
            message_type=message.message_type,
            file_url=message.file_url,
            file_name=message.file_name,
            file_size=message.file_size,
            is_edited=message.is_edited,
            edited_at=message.edited_at,
            reply_to_id=message.reply_to_id,
            is_deleted=message.is_deleted,
            deleted_at=message.deleted_at,
            created_at=message.created_at,
            updated_at=message.updated_at,
            sender={
                "id": message.sender.id,
                "username": message.sender.username,
                "full_name": message.sender.full_name,
                "avatar_url": message.sender.avatar_url
            }
        )
        message_responses.append(message_data)
    
    return MessageListResponse(
        messages=message_responses,
        total=total,
        page=page,
        per_page=per_page,
        has_next=total > page * per_page,
        has_prev=page > 1
    )


@router.post("/{talkroom_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(
    talkroom_id: int,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new message in a talkroom.
    
    Args:
        talkroom_id: Talkroom ID
        message_data: Message data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created message
        
    Raises:
        TalkroomNotFoundException: If talkroom not found
        UnauthorizedAccessException: If user not in talkroom
    """
    # Check if talkroom exists
    talkroom = db.query(Talkroom).filter(Talkroom.id == talkroom_id).first()
    if not talkroom:
        raise TalkroomNotFoundException("Talkroom not found")
    
    # Check if user is participant
    participant = db.query(TalkroomParticipant).filter(
        TalkroomParticipant.talkroom_id == talkroom_id,
        TalkroomParticipant.user_id == current_user.id
    ).first()
    
    if not participant:
        raise UnauthorizedAccessException("You are not a participant in this talkroom")
    
    # Create message
    message = Message(
        talkroom_id=talkroom_id,
        sender_id=current_user.id,
        content=message_data.content,
        message_type=message_data.message_type,
        reply_to_id=message_data.reply_to_id
    )
    
    db.add(message)
    db.commit()
    db.refresh(message)
    
    # Return message with sender info
    return MessageResponse(
        id=message.id,
        talkroom_id=message.talkroom_id,
        sender_id=message.sender_id,
        content=message.content,
        message_type=message.message_type,
        file_url=message.file_url,
        file_name=message.file_name,
        file_size=message.file_size,
        is_edited=message.is_edited,
        edited_at=message.edited_at,
        reply_to_id=message.reply_to_id,
        is_deleted=message.is_deleted,
        deleted_at=message.deleted_at,
        created_at=message.created_at,
        updated_at=message.updated_at,
        sender={
            "id": current_user.id,
            "username": current_user.username,
            "full_name": current_user.full_name,
            "avatar_url": current_user.avatar_url
        }
    )


@router.put("/{talkroom_id}/messages/{message_id}", response_model=MessageResponse)
def update_message(
    talkroom_id: int,
    message_id: int,
    message_data: MessageUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update a message.
    
    Args:
        talkroom_id: Talkroom ID
        message_id: Message ID
        message_data: Updated message data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated message
        
    Raises:
        MessageNotFoundException: If message not found
        UnauthorizedAccessException: If user not message sender
    """
    # Get message
    message = db.query(Message).filter(
        Message.id == message_id,
        Message.talkroom_id == talkroom_id,
        Message.is_deleted == False
    ).first()
    
    if not message:
        raise MessageNotFoundException("Message not found")
    
    # Check if user is the sender
    if message.sender_id != current_user.id:
        raise UnauthorizedAccessException("You can only edit your own messages")
    
    # Update message
    message.content = message_data.content
    message.is_edited = True
    message.edited_at = datetime.utcnow()
    message.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(message)
    
    return MessageResponse(
        id=message.id,
        talkroom_id=message.talkroom_id,
        sender_id=message.sender_id,
        content=message.content,
        message_type=message.message_type,
        file_url=message.file_url,
        file_name=message.file_name,
        file_size=message.file_size,
        is_edited=message.is_edited,
        edited_at=message.edited_at,
        reply_to_id=message.reply_to_id,
        is_deleted=message.is_deleted,
        deleted_at=message.deleted_at,
        created_at=message.created_at,
        updated_at=message.updated_at,
        sender={
            "id": current_user.id,
            "username": current_user.username,
            "full_name": current_user.full_name,
            "avatar_url": current_user.avatar_url
        }
    )


@router.delete("/{talkroom_id}/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(
    talkroom_id: int,
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Delete a message.
    
    Args:
        talkroom_id: Talkroom ID
        message_id: Message ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        No content
        
    Raises:
        MessageNotFoundException: If message not found
        UnauthorizedAccessException: If user not message sender
    """
    # Get message
    message = db.query(Message).filter(
        Message.id == message_id,
        Message.talkroom_id == talkroom_id,
        Message.is_deleted == False
    ).first()
    
    if not message:
        raise MessageNotFoundException("Message not found")
    
    # Check if user is the sender
    if message.sender_id != current_user.id:
        raise UnauthorizedAccessException("You can only delete your own messages")
    
    # Soft delete message
    message.is_deleted = True
    message.deleted_at = datetime.utcnow()
    message.updated_at = datetime.utcnow()
    
    db.commit()
    
    return None 