"""
Dependency injection for FastAPI routes.
"""
from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config.database import get_db
from app.core.security import verify_token
from app.core.exceptions import AuthenticationError, NotFoundError
from app.models.user import User
from app.schemas.user import TokenData

# Security scheme for JWT bearer tokens
security = HTTPBearer()


async def get_current_user_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    Validate JWT token and extract user information.
    
    Args:
        credentials: HTTP authorization credentials.
        
    Returns:
        Token data with user ID.
        
    Raises:
        AuthenticationError: If token is invalid or expired.
    """
    try:
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise AuthenticationError("Invalid token: no user ID")
        
        return TokenData(user_id=int(user_id))
    
    except Exception as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(get_current_user_token)
) -> User:
    """
    Get current authenticated user from database.
    
    Args:
        db: Database session.
        token_data: Validated token data.
        
    Returns:
        Current authenticated user.
        
    Raises:
        NotFoundError: If user is not found.
        AuthenticationError: If user is inactive.
    """
    result = await db.execute(
        select(User).where(User.id == token_data.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise NotFoundError("User not found")
    
    if not user.is_active:
        raise AuthenticationError("Inactive user")
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (alias for backward compatibility).
    
    Args:
        current_user: Current authenticated user.
        
    Returns:
        Current active user.
    """
    return current_user


# Optional authentication dependency
async def get_current_user_optional(
    db: AsyncSession = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[User]:
    """
    Get current user if token is provided, otherwise return None.
    
    Args:
        db: Database session.
        credentials: Optional HTTP authorization credentials.
        
    Returns:
        Current user if authenticated, None otherwise.
    """
    if not credentials:
        return None
    
    try:
        token_data = await get_current_user_token(credentials)
        user = await get_current_user(db, token_data)
        return user
    except (AuthenticationError, NotFoundError):
        return None