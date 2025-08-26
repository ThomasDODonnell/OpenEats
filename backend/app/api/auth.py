"""
Authentication endpoints for user registration and login.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.config.database import get_db
from app.core.security import create_access_token, verify_password, get_password_hash
from app.core.exceptions import AuthenticationError, ConflictError, ValidationError
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.
    
    Args:
        user_data: User registration data.
        db: Database session.
        
    Returns:
        Created user information.
        
    Raises:
        ConflictError: If email is already registered.
        ValidationError: If user data is invalid.
    """
    try:
        # Check if user already exists
        result = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise ConflictError("Email already registered")
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        
        new_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            is_active=True
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        return new_user
    
    except IntegrityError:
        await db.rollback()
        raise ConflictError("Email already registered")
    
    except Exception as e:
        await db.rollback()
        raise ValidationError(f"User registration failed: {str(e)}")


@router.post("/login", response_model=Token)
async def login_user(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return access token.
    
    Args:
        login_data: User login credentials.
        db: Database session.
        
    Returns:
        JWT access token.
        
    Raises:
        AuthenticationError: If credentials are invalid.
    """
    # Get user from database
    result = await db.execute(
        select(User).where(User.email == login_data.email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise AuthenticationError("Invalid email or password")
    
    if not user.is_active:
        raise AuthenticationError("Account is deactivated")
    
    # Verify password
    if not verify_password(login_data.password, user.hashed_password):
        raise AuthenticationError("Invalid email or password")
    
    # Create access token
    token_data = {"sub": str(user.id)}
    access_token = create_access_token(token_data)
    
    return Token(access_token=access_token, token_type="bearer")


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_user)
):
    """
    Refresh user's access token.
    
    Args:
        current_user: Current authenticated user.
        
    Returns:
        New JWT access token.
    """
    # Create new access token
    token_data = {"sub": str(current_user.id)}
    access_token = create_access_token(token_data)
    
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information.
    
    Args:
        current_user: Current authenticated user.
        
    Returns:
        Current user information.
    """
    return current_user


