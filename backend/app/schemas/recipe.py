"""
Pydantic schemas for recipe-related API operations.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.schemas.user import UserResponse
from app.schemas.tag import TagResponse


class IngredientItem(BaseModel):
    """Schema for individual recipe ingredients."""
    
    name: str
    amount: str
    unit: Optional[str] = None
    notes: Optional[str] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate ingredient name."""
        if len(v.strip()) < 1:
            raise ValueError('Ingredient name cannot be empty')
        return v.strip().lower()
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: str) -> str:
        """Validate ingredient amount."""
        if len(v.strip()) < 1:
            raise ValueError('Ingredient amount cannot be empty')
        return v.strip()


class RecipeBase(BaseModel):
    """Base recipe schema with common fields."""
    
    title: str
    description: Optional[str] = None
    ingredients: List[IngredientItem]
    instructions: str
    prep_time_minutes: int
    cook_time_minutes: int
    servings: int
    is_public: bool = False
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate recipe title."""
        if len(v.strip()) < 1:
            raise ValueError('Recipe title cannot be empty')
        if len(v.strip()) > 255:
            raise ValueError('Recipe title cannot exceed 255 characters')
        return v.strip()
    
    @field_validator('instructions')
    @classmethod
    def validate_instructions(cls, v: str) -> str:
        """Validate recipe instructions."""
        if len(v.strip()) < 10:
            raise ValueError('Instructions must be at least 10 characters')
        return v.strip()
    
    @field_validator('prep_time_minutes', 'cook_time_minutes', 'servings')
    @classmethod
    def validate_positive_integers(cls, v: int) -> int:
        """Validate positive integer fields."""
        if v < 1:
            raise ValueError('Value must be at least 1')
        if v > 10000:  # Reasonable upper limit
            raise ValueError('Value is too large')
        return v
    
    @field_validator('ingredients')
    @classmethod
    def validate_ingredients(cls, v: List[IngredientItem]) -> List[IngredientItem]:
        """Validate ingredients list."""
        if len(v) < 1:
            raise ValueError('Recipe must have at least one ingredient')
        if len(v) > 100:
            raise ValueError('Recipe cannot have more than 100 ingredients')
        return v


class RecipeCreate(RecipeBase):
    """Schema for recipe creation."""
    
    tag_ids: List[int] = []
    
    @field_validator('tag_ids')
    @classmethod
    def validate_tag_ids(cls, v: List[int]) -> List[int]:
        """Validate tag IDs."""
        if len(v) > 20:
            raise ValueError('Recipe cannot have more than 20 tags')
        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag_id in v:
            if tag_id not in seen:
                seen.add(tag_id)
                unique_tags.append(tag_id)
        return unique_tags


class RecipeUpdate(BaseModel):
    """Schema for recipe updates."""
    
    title: Optional[str] = None
    description: Optional[str] = None
    ingredients: Optional[List[IngredientItem]] = None
    instructions: Optional[str] = None
    prep_time_minutes: Optional[int] = None
    cook_time_minutes: Optional[int] = None
    servings: Optional[int] = None
    is_public: Optional[bool] = None
    tag_ids: Optional[List[int]] = None
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Validate recipe title."""
        if v is not None:
            if len(v.strip()) < 1:
                raise ValueError('Recipe title cannot be empty')
            if len(v.strip()) > 255:
                raise ValueError('Recipe title cannot exceed 255 characters')
            return v.strip()
        return v
    
    @field_validator('instructions')
    @classmethod
    def validate_instructions(cls, v: Optional[str]) -> Optional[str]:
        """Validate recipe instructions."""
        if v is not None:
            if len(v.strip()) < 10:
                raise ValueError('Instructions must be at least 10 characters')
            return v.strip()
        return v
    
    @field_validator('prep_time_minutes', 'cook_time_minutes', 'servings')
    @classmethod
    def validate_positive_integers(cls, v: Optional[int]) -> Optional[int]:
        """Validate positive integer fields."""
        if v is not None:
            if v < 1:
                raise ValueError('Value must be at least 1')
            if v > 10000:
                raise ValueError('Value is too large')
        return v
    
    @field_validator('ingredients')
    @classmethod
    def validate_ingredients(cls, v: Optional[List[IngredientItem]]) -> Optional[List[IngredientItem]]:
        """Validate ingredients list."""
        if v is not None:
            if len(v) < 1:
                raise ValueError('Recipe must have at least one ingredient')
            if len(v) > 100:
                raise ValueError('Recipe cannot have more than 100 ingredients')
        return v
    
    @field_validator('tag_ids')
    @classmethod
    def validate_tag_ids(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        """Validate tag IDs."""
        if v is not None:
            if len(v) > 20:
                raise ValueError('Recipe cannot have more than 20 tags')
            # Remove duplicates while preserving order
            seen = set()
            unique_tags = []
            for tag_id in v:
                if tag_id not in seen:
                    seen.add(tag_id)
                    unique_tags.append(tag_id)
            return unique_tags
        return v


class RecipeResponse(RecipeBase):
    """Schema for recipe responses."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    author_id: int
    created_at: datetime
    upvotes: int = 0
    downvotes: int = 0
    vote_score: int = 0
    
    @property
    def total_time_minutes(self) -> int:
        """Calculate total cooking time."""
        return self.prep_time_minutes + self.cook_time_minutes


class RecipeDetailResponse(RecipeResponse):
    """Detailed recipe response with relationships."""
    
    author: UserResponse
    tags: List[TagResponse] = []


class RecipeListResponse(BaseModel):
    """Schema for paginated recipe lists."""
    
    items: List[RecipeResponse]
    total: int
    page: int
    size: int
    pages: int


class RecipeSearchQuery(BaseModel):
    """Schema for recipe search parameters."""
    
    q: Optional[str] = None  # Search query
    tags: Optional[List[str]] = None  # Tag names to filter by
    author_id: Optional[int] = None
    is_public: Optional[bool] = None
    min_vote_score: Optional[int] = None
    max_prep_time: Optional[int] = None
    max_cook_time: Optional[int] = None
    page: int = 1
    size: int = 20
    
    @field_validator('size')
    @classmethod
    def validate_size(cls, v: int) -> int:
        """Validate page size."""
        if v < 1 or v > 100:
            raise ValueError('Page size must be between 1 and 100')
        return v
    
    @field_validator('page')
    @classmethod
    def validate_page(cls, v: int) -> int:
        """Validate page number."""
        if v < 1:
            raise ValueError('Page number must be at least 1')
        return v