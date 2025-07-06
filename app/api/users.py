"""
User management API endpoints.
"""
from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserProfile, UserPublic, UserSearch, UserUpdate
from app.utils.dependencies import get_current_active_user
from app.utils.exceptions import UserNotFoundException

router = APIRouter()


@router.get("/me", response_model=UserProfile)
def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get current user profile.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user profile
    """
    return current_user


@router.put("/me", response_model=UserProfile)
def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update current user profile.
    
    Args:
        user_update: User update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated user profile
    """
    # Update user fields if provided
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    
    if user_update.bio is not None:
        current_user.bio = user_update.bio
    
    if user_update.avatar_url is not None:
        current_user.avatar_url = user_update.avatar_url
    
    # Update timestamp
    current_user.updated_at = datetime.utcnow()
    
    # Save changes
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.get("/{user_id}", response_model=UserPublic)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get user by ID.
    
    Args:
        user_id: User ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        User public profile
        
    Raises:
        UserNotFoundException: If user not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserNotFoundException("User not found")
    
    return user


@router.get("/username/{username}", response_model=UserPublic)
def get_user_by_username(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get user by username.
    
    Args:
        username: Username
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        User public profile
        
    Raises:
        UserNotFoundException: If user not found
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise UserNotFoundException("User not found")
    
    return user


@router.get("/search/", response_model=List[UserSearch])
def search_users(
    q: str = Query(..., min_length=1, max_length=50, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Number of results to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Search users by username or full name.
    
    Args:
        q: Search query
        limit: Number of results to return
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of matching users
    """
    # Search by username or full name
    users = db.query(User).filter(
        (User.username.ilike(f"%{q}%")) | 
        (User.full_name.ilike(f"%{q}%"))
    ).filter(
        User.is_active == True,
        User.id != current_user.id  # Exclude current user
    ).limit(limit).all()
    
    return users


@router.put("/me/last-seen")
def update_last_seen(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update user's last seen timestamp.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    current_user.last_seen = datetime.utcnow()
    db.commit()
    
    return {"message": "Last seen updated successfully"}


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_current_user(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Delete current user account.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        No content
    """
    # In a production system, you might want to soft delete or archive user data
    # For now, we'll just deactivate the account
    current_user.is_active = False
    current_user.updated_at = datetime.utcnow()
    db.commit()
    
    return None 