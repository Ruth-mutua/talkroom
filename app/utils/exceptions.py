"""
Custom exceptions for SecureTalkroom application.
"""
from fastapi import HTTPException, status


class TalkroomException(HTTPException):
    """Base exception for talkroom-related errors."""
    
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class UserNotFoundException(TalkroomException):
    """Exception raised when user is not found."""
    
    def __init__(self, detail: str = "User not found"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class UserAlreadyExistsException(TalkroomException):
    """Exception raised when user already exists."""
    
    def __init__(self, detail: str = "User already exists"):
        super().__init__(detail=detail, status_code=status.HTTP_409_CONFLICT)


class InvalidCredentialsException(TalkroomException):
    """Exception raised when credentials are invalid."""
    
    def __init__(self, detail: str = "Invalid credentials"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class TalkroomNotFoundException(TalkroomException):
    """Exception raised when talkroom is not found."""
    
    def __init__(self, detail: str = "Talkroom not found"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class MessageNotFoundException(TalkroomException):
    """Exception raised when message is not found."""
    
    def __init__(self, detail: str = "Message not found"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class UnauthorizedAccessException(TalkroomException):
    """Exception raised when user doesn't have permission."""
    
    def __init__(self, detail: str = "Unauthorized access"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


class ValidationException(TalkroomException):
    """Exception raised for validation errors."""
    
    def __init__(self, detail: str = "Validation error"):
        super().__init__(detail=detail, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class RateLimitException(TalkroomException):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(detail=detail, status_code=status.HTTP_429_TOO_MANY_REQUESTS)


class FileUploadException(TalkroomException):
    """Exception raised for file upload errors."""
    
    def __init__(self, detail: str = "File upload error"):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class DatabaseException(TalkroomException):
    """Exception raised for database errors."""
    
    def __init__(self, detail: str = "Database error"):
        super().__init__(detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) 