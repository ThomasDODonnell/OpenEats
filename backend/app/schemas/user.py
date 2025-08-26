"""
Pydantic schemas for user-related API operations.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
import re


class UserBase(BaseModel):
    """Base user schema with common fields."""
    
    email: EmailStr
    first_name: str
    last_name: str
    
    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_names(cls, v: str) -> str:
        """Validate name fields."""
        if len(v.strip()) < 1:
            raise ValueError('Name cannot be empty')
        if len(v.strip()) > 100:
            raise ValueError('Name cannot exceed 100 characters')
        return v.strip().title()


class UserCreate(UserBase):
    """Schema for user creation."""
    
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v


class UserUpdate(BaseModel):
    """Schema for user updates."""
    
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_names(cls, v: Optional[str]) -> Optional[str]:
        """Validate name fields."""
        if v is not None:
            if len(v.strip()) < 1:
                raise ValueError('Name cannot be empty')
            if len(v.strip()) > 100:
                raise ValueError('Name cannot exceed 100 characters')
            return v.strip().title()
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema for user responses."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    created_at: datetime


class UserProfile(UserResponse):
    """Extended user profile with additional information."""
    
    pass  # Can be extended with additional profile fields


class Token(BaseModel):
    """Schema for authentication tokens."""
    
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token data."""
    
    user_id: Optional[int] = None