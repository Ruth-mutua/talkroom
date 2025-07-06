"""
Authentication API endpoints.
"""
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token,
)
from app.models.user import User
from app.schemas.auth import (
    ChangePassword,
    PasswordReset,
    PasswordResetConfirm,
    RefreshToken,
    Token,
    UserLogin,
    UserRegister,
)
from app.schemas.user import UserProfile
from app.utils.dependencies import get_current_active_user
from app.utils.exceptions import (
    InvalidCredentialsException,
    UserAlreadyExistsException,
    UserNotFoundException,
)

router = APIRouter()


@router.post("/register", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user.
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        Created user profile
        
    Raises:
        UserAlreadyExistsException: If user already exists
    """
    # Check if user already exists by email
    if db.query(User).filter(User.email == user_data.email).first():
        raise UserAlreadyExistsException("User with this email already exists")
    
    # Check if username is taken
    if db.query(User).filter(User.username == user_data.username).first():
        raise UserAlreadyExistsException("Username already taken")
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.post("/login", response_model=Token)
def login(
    user_credentials: UserLogin,
    db: Session = Depends(get_db)
) -> Any:
    """
    Login user and return access and refresh tokens.
    
    Args:
        user_credentials: User login credentials
        db: Database session
        
    Returns:
        Access and refresh tokens
        
    Raises:
        InvalidCredentialsException: If credentials are invalid
    """
    # Get user by email
    user = db.query(User).filter(User.email == user_credentials.email).first()
    
    # Verify user exists and password is correct
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise InvalidCredentialsException("Incorrect email or password")
    
    # Check if user is active
    if not user.is_active:
        raise InvalidCredentialsException("User account is inactive")
    
    # Update last seen
    user.last_seen = datetime.utcnow()
    db.commit()
    
    # Create tokens
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/refresh", response_model=Token)
def refresh_token(
    refresh_data: RefreshToken,
    db: Session = Depends(get_db)
) -> Any:
    """
    Refresh access token using refresh token.
    
    Args:
        refresh_data: Refresh token data
        db: Database session
        
    Returns:
        New access and refresh tokens
        
    Raises:
        InvalidCredentialsException: If refresh token is invalid
    """
    # Verify refresh token
    payload = verify_token(refresh_data.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise InvalidCredentialsException("Invalid refresh token")
    
    # Get user
    user_id = payload.get("sub")
    if user_id is None:
        raise InvalidCredentialsException("Invalid refresh token")
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise InvalidCredentialsException("User not found or inactive")
    
    # Create new tokens
    access_token = create_access_token(subject=user.id)
    new_refresh_token = create_refresh_token(subject=user.id)
    
    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )


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


@router.put("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    password_data: ChangePassword,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Change user password.
    
    Args:
        password_data: Password change data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        InvalidCredentialsException: If current password is incorrect
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise InvalidCredentialsException("Current password is incorrect")
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    current_user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Password changed successfully"}


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Logout user (placeholder for token blacklisting).
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    # In a production system, you would blacklist the token here
    # For now, we'll just return a success message
    return {"message": "Logged out successfully"} 