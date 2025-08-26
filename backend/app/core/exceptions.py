"""
Custom exception handlers for the application.
"""
from typing import Dict, Any
from fastapi import HTTPException, status


class AuthenticationError(HTTPException):
    """Authentication related errors."""
    
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(HTTPException):
    """Authorization related errors."""
    
    def __init__(self, detail: str = "Not authorized to perform this action"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class NotFoundError(HTTPException):
    """Resource not found errors."""
    
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class ValidationError(HTTPException):
    """Validation related errors."""
    
    def __init__(self, detail: str = "Validation failed"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class ConflictError(HTTPException):
    """Resource conflict errors."""
    
    def __init__(self, detail: str = "Resource conflict"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class RateLimitError(HTTPException):
    """Rate limit exceeded errors."""
    
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail
        )


def create_error_response(status_code: int, message: str, details: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        status_code: HTTP status code.
        message: Error message.
        details: Additional error details.
        
    Returns:
        Standardized error response dictionary.
    """
    error_response = {
        "error": True,
        "status_code": status_code,
        "message": message,
    }
    
    if details:
        error_response["details"] = details
    
    return error_response