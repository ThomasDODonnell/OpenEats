"""
Pydantic schemas for tag-related API operations.
"""
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, field_validator
from enum import Enum


class TagCategory(str, Enum):
    """Available tag categories."""
    
    DIETARY = "dietary"  # vegetarian, vegan, gluten-free, etc.
    PROTEIN = "protein"  # chicken, beef, fish, tofu, etc.
    MEAL_TYPE = "meal_type"  # breakfast, lunch, dinner, snack
    CUISINE = "cuisine"  # italian, mexican, asian, etc.
    COOKING_METHOD = "cooking_method"  # grilled, baked, fried, etc.
    DIFFICULTY = "difficulty"  # easy, medium, hard
    TIME = "time"  # quick, slow-cooker, meal-prep
    OCCASION = "occasion"  # party, holiday, weeknight
    LIFESTYLE = "lifestyle"  # keto, paleo, low-carb, etc.


class TagBase(BaseModel):
    """Base tag schema with common fields."""
    
    name: str
    category: TagCategory
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate tag name."""
        if len(v.strip()) < 1:
            raise ValueError('Tag name cannot be empty')
        if len(v.strip()) > 50:
            raise ValueError('Tag name cannot exceed 50 characters')
        # Convert to lowercase and replace spaces with hyphens
        return v.strip().lower().replace(' ', '-')


class TagCreate(TagBase):
    """Schema for tag creation."""
    pass


class TagUpdate(BaseModel):
    """Schema for tag updates."""
    
    name: Optional[str] = None
    category: Optional[TagCategory] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate tag name."""
        if v is not None:
            if len(v.strip()) < 1:
                raise ValueError('Tag name cannot be empty')
            if len(v.strip()) > 50:
                raise ValueError('Tag name cannot exceed 50 characters')
            return v.strip().lower().replace(' ', '-')
        return v


class TagResponse(TagBase):
    """Schema for tag responses."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int


class TagWithCount(TagResponse):
    """Tag response with recipe count."""
    
    recipe_count: int = 0


class PopularTagsResponse(BaseModel):
    """Schema for popular tags grouped by category."""
    
    dietary: List[TagWithCount] = []
    protein: List[TagWithCount] = []
    meal_type: List[TagWithCount] = []
    cuisine: List[TagWithCount] = []
    cooking_method: List[TagWithCount] = []
    difficulty: List[TagWithCount] = []
    time: List[TagWithCount] = []
    occasion: List[TagWithCount] = []
    lifestyle: List[TagWithCount] = []