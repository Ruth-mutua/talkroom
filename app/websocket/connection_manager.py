"""
WebSocket connection manager for real-time talkroom functionality.
"""
import asyncio
import json
import logging
from typing import Dict, List, Optional, Set

from fastapi import WebSocket
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.talkroom import TalkroomParticipant
from app.models.user import User

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time talkroom."""
    
    def __init__(self):
        # Store active connections: user_id -> WebSocket
        self.active_connections: Dict[int, WebSocket] = {}
        
        # Store user's talkroom memberships: user_id -> Set[talkroom_id]
        self.user_talkrooms: Dict[int, Set[int]] = {}
        
        # Store talkroom participants: talkroom_id -> Set[user_id]
        self.talkroom_participants: Dict[int, Set[int]] = {}
        
        # Store user online status: user_id -> bool
        self.user_online_status: Dict[int, bool] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """
        Connect a user to WebSocket.
        
        Args:
            websocket: WebSocket connection
            user_id: User ID
        """
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_online_status[user_id] = True
        
        # Load user's talkroom memberships
        await self._load_user_talkrooms(user_id)
        
        logger.info(f"User {user_id} connected")
    
    def disconnect(self, user_id: int):
        """
        Disconnect a user from WebSocket.
        
        Args:
            user_id: User ID
        """
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        
        # Remove user from talkroom participants
        if user_id in self.user_talkrooms:
            for talkroom_id in self.user_talkrooms[user_id]:
                if talkroom_id in self.talkroom_participants:
                    self.talkroom_participants[talkroom_id].discard(user_id)
                    if not self.talkroom_participants[talkroom_id]:
                        del self.talkroom_participants[talkroom_id]
        
            del self.user_talkrooms[user_id]
        
        self.user_online_status[user_id] = False
        
        logger.info(f"User {user_id} disconnected")
    
    async def send_personal_message(self, message: str, user_id: int):
        """
        Send a personal message to a specific user.
        
        Args:
            message: Message to send
            user_id: User ID
        """
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error sending personal message to user {user_id}: {e}")
                self.disconnect(user_id)
    
    async def broadcast_to_talkroom(self, message: str, talkroom_id: int, exclude_user_id: Optional[int] = None):
        """
        Broadcast a message to all participants in a talkroom.
        
        Args:
            message: Message to broadcast
            talkroom_id: Talkroom ID
            exclude_user_id: User ID to exclude from broadcast
        """
        if talkroom_id not in self.talkroom_participants:
            return
        
        participants = self.talkroom_participants[talkroom_id].copy()
        if exclude_user_id:
            participants.discard(exclude_user_id)
        
        # Send message to all participants
        for user_id in participants:
            if user_id in self.active_connections:
                websocket = self.active_connections[user_id]
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to user {user_id}: {e}")
                    self.disconnect(user_id)
    
    async def send_typing_notification(self, talkroom_id: int, user_id: int, is_typing: bool):
        """
        Send typing notification to talkroom participants.
        
        Args:
            talkroom_id: Talkroom ID
            user_id: User ID who is typing
            is_typing: Whether user is typing
        """
        if talkroom_id not in self.talkroom_participants:
            return
        
        typing_message = json.dumps({
            "type": "typing",
            "data": {
                "user_id": user_id,
                "talkroom_id": talkroom_id,
                "is_typing": is_typing
            }
        })
        
        await self.broadcast_to_talkroom(typing_message, talkroom_id, exclude_user_id=user_id)
    
    async def send_user_status(self, user_id: int, is_online: bool):
        """
        Send user online/offline status to their talkrooms.
        
        Args:
            user_id: User ID
            is_online: Whether user is online
        """
        if user_id not in self.user_talkrooms:
            return
        
        status_message = json.dumps({
            "type": "user_status",
            "data": {
                "user_id": user_id,
                "is_online": is_online
            }
        })
        
        # Send to all talkrooms user is part of
        for talkroom_id in self.user_talkrooms[user_id]:
            await self.broadcast_to_talkroom(status_message, talkroom_id, exclude_user_id=user_id)
    
    def get_talkroom_online_users(self, talkroom_id: int) -> List[int]:
        """
        Get list of online users in a talkroom.
        
        Args:
            talkroom_id: Talkroom ID
            
        Returns:
            List of online user IDs
        """
        if talkroom_id not in self.talkroom_participants:
            return []
        
        online_users = []
        for user_id in self.talkroom_participants[talkroom_id]:
            if self.user_online_status.get(user_id, False):
                online_users.append(user_id)
        
        return online_users
    
    def is_user_online(self, user_id: int) -> bool:
        """
        Check if a user is online.
        
        Args:
            user_id: User ID
            
        Returns:
            True if user is online, False otherwise
        """
        return self.user_online_status.get(user_id, False)
    
    async def _load_user_talkrooms(self, user_id: int):
        """
        Load user's talkroom memberships from database.
        
        Args:
            user_id: User ID
        """
        try:
            db = next(get_db())
            
            # Get user's talkroom participations
            participations = db.query(TalkroomParticipant).filter(
                TalkroomParticipant.user_id == user_id,
                TalkroomParticipant.left_at.is_(None)
            ).all()
            
            # Update user's talkroom memberships
            self.user_talkrooms[user_id] = set()
            for participation in participations:
                talkroom_id = participation.talkroom_id
                self.user_talkrooms[user_id].add(talkroom_id)
                
                # Add to talkroom participants
                if talkroom_id not in self.talkroom_participants:
                    self.talkroom_participants[talkroom_id] = set()
                self.talkroom_participants[talkroom_id].add(user_id)
            
            db.close()
            
        except Exception as e:
            logger.error(f"Error loading user talkrooms: {e}")
    
    async def broadcast_to_all(self, message: str):
        """
        Broadcast a message to all connected users.
        
        Args:
            message: Message to broadcast
        """
        for user_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {e}")
                self.disconnect(user_id)
    
    def get_connected_users(self) -> List[int]:
        """
        Get list of all connected user IDs.
        
        Returns:
            List of connected user IDs
        """
        return list(self.active_connections.keys())
    
    def get_connection_count(self) -> int:
        """
        Get total number of active connections.
        
        Returns:
            Number of active connections
        """
        return len(self.active_connections)


# Global connection manager instance
connection_manager = ConnectionManager() 