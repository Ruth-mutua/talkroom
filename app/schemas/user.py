"""
User schemas for profile management and user data.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    full_name: Optional[str] = Field(None, max_length=255, description="User's full name")
    bio: Optional[str] = Field(None, max_length=500, description="User biography")
    avatar_url: Optional[str] = Field(None, description="User avatar URL")


class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(..., min_length=8, description="User password")


class UserUpdate(BaseModel):
    """User update schema."""
    full_name: Optional[str] = Field(None, max_length=255, description="User's full name")
    bio: Optional[str] = Field(None, max_length=500, description="User biography")
    avatar_url: Optional[str] = Field(None, description="User avatar URL")


class UserProfile(BaseModel):
    """User profile response schema."""
    id: int = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., description="Username")
    full_name: Optional[str] = Field(None, description="User's full name")
    bio: Optional[str] = Field(None, description="User biography")
    avatar_url: Optional[str] = Field(None, description="User avatar URL")
    is_active: bool = Field(..., description="User account status")
    is_verified: bool = Field(..., description="Email verification status")
    last_seen: Optional[datetime] = Field(None, description="Last seen timestamp")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last profile update timestamp")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class UserPublic(BaseModel):
    """Public user information schema."""
    id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    full_name: Optional[str] = Field(None, description="User's full name")
    avatar_url: Optional[str] = Field(None, description="User avatar URL")
    last_seen: Optional[datetime] = Field(None, description="Last seen timestamp")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class UserSearch(BaseModel):
    """User search response schema."""
    id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    full_name: Optional[str] = Field(None, description="User's full name")
    avatar_url: Optional[str] = Field(None, description="User avatar URL")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True 