"""
WebSocket talkroom handler for real-time message processing.
"""
import json
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_token
from app.models.talkroom import Talkroom, TalkroomParticipant
from app.models.message import Message, MessageType
from app.models.user import User
from app.websocket.connection_manager import connection_manager

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_current_user_ws(websocket: WebSocket, token: str, db: Session) -> Optional[User]:
    """
    Get current user from WebSocket token.
    
    Args:
        websocket: WebSocket connection
        token: JWT token
        db: Database session
        
    Returns:
        User object if valid, None otherwise
    """
    try:
        # Verify token
        payload = verify_token(token)
        if payload is None or payload.get("type") != "access":
            return None
        
        # Get user ID from token
        user_id = payload.get("sub")
        if user_id is None:
            return None
        
        # Get user from database
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user or not user.is_active:
            return None
        
        return user
    except Exception as e:
        logger.error(f"Error getting user from WebSocket token: {e}")
        return None


async def verify_talkroom_access(user_id: int, talkroom_id: int, db: Session) -> bool:
    """
    Verify if user has access to a talkroom.
    
    Args:
        user_id: User ID
        talkroom_id: Talkroom ID
        db: Database session
        
    Returns:
        True if user has access, False otherwise
    """
    try:
        participant = db.query(TalkroomParticipant).filter(
            TalkroomParticipant.talkroom_id == talkroom_id,
            TalkroomParticipant.user_id == user_id,
            TalkroomParticipant.left_at.is_(None)
        ).first()
        
        return participant is not None
    except Exception as e:
        logger.error(f"Error verifying talkroom access: {e}")
        return False


@router.websocket("/talkroom/{token}")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time talkroom.
    
    Args:
        websocket: WebSocket connection
        token: JWT token for authentication
        db: Database session
    """
    # Authenticate user
    user = await get_current_user_ws(websocket, token, db)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Connect user
    await connection_manager.connect(websocket, user.id)
    
    # Send online status to user's talkrooms
    await connection_manager.send_user_status(user.id, is_online=True)
    
    try:
        while True:
            # Receive message from WebSocket
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from user {user.id}")
                continue
            
            # Handle different message types
            message_type = message_data.get("type")
            
            if message_type == "message":
                await handle_talkroom_message(user, message_data, db)
            elif message_type == "typing":
                await handle_typing_notification(user, message_data, db)
            elif message_type == "join_talkroom":
                await handle_join_talkroom(user, message_data, db)
            elif message_type == "leave_talkroom":
                await handle_leave_talkroom(user, message_data, db)
            elif message_type == "ping":
                await handle_ping(user, websocket)
            else:
                logger.warning(f"Unknown message type: {message_type}")
    
    except WebSocketDisconnect:
        # User disconnected
        connection_manager.disconnect(user.id)
        
        # Send offline status to user's talkrooms
        await connection_manager.send_user_status(user.id, is_online=False)
        
        logger.info(f"User {user.id} disconnected")
    
    except Exception as e:
        logger.error(f"WebSocket error for user {user.id}: {e}")
        connection_manager.disconnect(user.id)
        await connection_manager.send_user_status(user.id, is_online=False)


async def handle_talkroom_message(user: User, message_data: Dict[str, Any], db: Session):
    """
    Handle incoming talkroom message.
    
    Args:
        user: Sender user
        message_data: Message data
        db: Database session
    """
    try:
        talkroom_id = message_data.get("talkroom_id")
        content = message_data.get("content")
        reply_to_id = message_data.get("reply_to_id")
        
        if not talkroom_id or not content:
            return
        
        # Verify user has access to talkroom
        if not await verify_talkroom_access(user.id, talkroom_id, db):
            logger.warning(f"User {user.id} attempted to send message to unauthorized talkroom {talkroom_id}")
            return
        
        # Create message in database
        message = Message(
            talkroom_id=talkroom_id,
            sender_id=user.id,
            content=content,
            message_type=MessageType.TEXT,
            reply_to_id=reply_to_id
        )
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        # Prepare message for broadcast
        broadcast_message = json.dumps({
            "type": "message",
            "message": {
                "id": message.id,
                "talkroom_id": message.talkroom_id,
                "sender_id": message.sender_id,
                "content": message.content,
                "message_type": message.message_type.value,
                "reply_to_id": message.reply_to_id,
                "created_at": message.created_at.isoformat(),
                "sender": {
                    "id": user.id,
                    "username": user.username,
                    "full_name": user.full_name,
                    "avatar_url": user.avatar_url
                }
            }
        })
        
        # Broadcast message to all talkroom participants
        await connection_manager.broadcast_to_talkroom(broadcast_message, talkroom_id)
        
        logger.info(f"User {user.id} sent message to talkroom {talkroom_id}")
    
    except Exception as e:
        logger.error(f"Error handling talkroom message: {e}")


async def handle_typing_notification(user: User, message_data: Dict[str, Any], db: Session):
    """
    Handle typing notification.
    
    Args:
        user: User who is typing
        message_data: Message data
        db: Database session
    """
    try:
        talkroom_id = message_data.get("talkroom_id")
        is_typing = message_data.get("is_typing", False)
        
        if not talkroom_id:
            return
        
        # Verify user has access to talkroom
        if not await verify_talkroom_access(user.id, talkroom_id, db):
            return
        
        # Send typing notification to talkroom participants
        await connection_manager.send_typing_notification(talkroom_id, user.id, is_typing)
        
    except Exception as e:
        logger.error(f"Error handling typing notification: {e}")


async def handle_join_talkroom(user: User, message_data: Dict[str, Any], db: Session):
    """
    Handle user joining a talkroom.
    
    Args:
        user: User joining
        message_data: Message data
        db: Database session
    """
    try:
        talkroom_id = message_data.get("talkroom_id")
        
        if not talkroom_id:
            return
        
        # Verify user has access to talkroom
        if not await verify_talkroom_access(user.id, talkroom_id, db):
            return
        
        # Notify other participants that user joined
        notification = json.dumps({
            "type": "user_joined",
            "data": {
                "user_id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "talkroom_id": talkroom_id
            }
        })
        
        await connection_manager.broadcast_to_talkroom(notification, talkroom_id, exclude_user_id=user.id)
        
        logger.info(f"User {user.id} joined talkroom {talkroom_id}")
    
    except Exception as e:
        logger.error(f"Error handling join talkroom: {e}")


async def handle_leave_talkroom(user: User, message_data: Dict[str, Any], db: Session):
    """
    Handle user leaving a talkroom.
    
    Args:
        user: User leaving
        message_data: Message data
        db: Database session
    """
    try:
        talkroom_id = message_data.get("talkroom_id")
        
        if not talkroom_id:
            return
        
        # Notify other participants that user left
        notification = json.dumps({
            "type": "user_left",
            "data": {
                "user_id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "talkroom_id": talkroom_id
            }
        })
        
        await connection_manager.broadcast_to_talkroom(notification, talkroom_id, exclude_user_id=user.id)
        
        logger.info(f"User {user.id} left talkroom {talkroom_id}")
    
    except Exception as e:
        logger.error(f"Error handling leave talkroom: {e}")


async def handle_ping(user: User, websocket: WebSocket):
    """
    Handle ping message.
    
    Args:
        user: User sending ping
        websocket: WebSocket connection
    """
    try:
        pong_message = json.dumps({
            "type": "pong",
            "timestamp": logger.time()
        })
        
        await websocket.send_text(pong_message)
        
    except Exception as e:
        logger.error(f"Error handling ping: {e}") 