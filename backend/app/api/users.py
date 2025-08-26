"""
User management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.config.database import get_db
from app.core.exceptions import NotFoundError, ConflictError, ValidationError, AuthorizationError
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, UserProfile
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user profile.
    
    Args:
        current_user: Current authenticated user.
        
    Returns:
        Current user profile information.
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user profile.
    
    Args:
        user_update: User update data.
        current_user: Current authenticated user.
        db: Database session.
        
    Returns:
        Updated user information.
        
    Raises:
        ValidationError: If update data is invalid.
    """
    try:
        # Update user fields
        if user_update.first_name is not None:
            current_user.first_name = user_update.first_name
        
        if user_update.last_name is not None:
            current_user.last_name = user_update.last_name
        
        await db.commit()
        await db.refresh(current_user)
        
        return current_user
    
    except Exception as e:
        await db.rollback()
        raise ValidationError(f"User update failed: {str(e)}")


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_current_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Deactivate current user account.
    
    Args:
        current_user: Current authenticated user.
        db: Database session.
        
    Note:
        This performs a soft delete by setting is_active to False.
        The user data is preserved for data integrity.
    """
    try:
        current_user.is_active = False
        await db.commit()
    
    except Exception as e:
        await db.rollback()
        raise ValidationError(f"User deactivation failed: {str(e)}")


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get user by ID (public profile).
    
    Args:
        user_id: User ID to retrieve.
        db: Database session.
        
    Returns:
        User profile information.
        
    Raises:
        NotFoundError: If user is not found.
    """
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise NotFoundError("User not found")
    
    return user


@router.get("/", response_model=list[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of users (public profiles only).
    
    Args:
        skip: Number of users to skip.
        limit: Maximum number of users to return.
        db: Database session.
        
    Returns:
        List of user profiles.
    """
    # Validate pagination parameters
    if skip < 0:
        skip = 0
    if limit < 1 or limit > 100:
        limit = 20
    
    result = await db.execute(
        select(User)
        .where(User.is_active == True)
        .offset(skip)
        .limit(limit)
        .order_by(User.created_at.desc())
    )
    
    users = result.scalars().all()
    return users