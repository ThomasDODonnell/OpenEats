"""
Pydantic schemas for shopping list-related API operations.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.recipe import IngredientItem


class AggregatedIngredient(BaseModel):
    """Schema for aggregated ingredients with quantities."""
    
    name: str
    total_amount: str
    unit: Optional[str] = None
    notes: List[str] = []
    recipe_names: List[str] = []  # Which recipes contributed this ingredient


class ShoppingListBase(BaseModel):
    """Base shopping list schema."""
    
    name: str
    description: Optional[str] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate shopping list name."""
        if len(v.strip()) < 1:
            raise ValueError('Shopping list name cannot be empty')
        if len(v.strip()) > 255:
            raise ValueError('Shopping list name cannot exceed 255 characters')
        return v.strip()
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate description."""
        if v is not None:
            if len(v.strip()) > 500:
                raise ValueError('Description cannot exceed 500 characters')
            return v.strip()
        return v


class ShoppingListCreate(ShoppingListBase):
    """Schema for creating a shopping list."""
    
    recipe_ids: List[int]
    
    @field_validator('recipe_ids')
    @classmethod
    def validate_recipe_ids(cls, v: List[int]) -> List[int]:
        """Validate recipe IDs."""
        if len(v) < 1:
            raise ValueError('Must include at least one recipe')
        if len(v) > 50:
            raise ValueError('Cannot create shopping list from more than 50 recipes')
        # Remove duplicates while preserving order
        seen = set()
        unique_ids = []
        for recipe_id in v:
            if recipe_id not in seen:
                seen.add(recipe_id)
                unique_ids.append(recipe_id)
        return unique_ids


class ShoppingListUpdate(BaseModel):
    """Schema for updating a shopping list."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    ingredients: Optional[List[AggregatedIngredient]] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate shopping list name."""
        if v is not None:
            if len(v.strip()) < 1:
                raise ValueError('Shopping list name cannot be empty')
            if len(v.strip()) > 255:
                raise ValueError('Shopping list name cannot exceed 255 characters')
            return v.strip()
        return v
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate description."""
        if v is not None:
            if len(v.strip()) > 500:
                raise ValueError('Description cannot exceed 500 characters')
            return v.strip()
        return v


class ShoppingListResponse(ShoppingListBase):
    """Schema for shopping list responses."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    recipe_ids: List[int]
    ingredients: List[AggregatedIngredient]
    created_at: datetime
    updated_at: datetime


class ShoppingListSummary(BaseModel):
    """Schema for shopping list summary."""
    
    id: int
    name: str
    description: Optional[str] = None
    recipe_count: int
    ingredient_count: int
    created_at: datetime


class GenerateShoppingListRequest(BaseModel):
    """Schema for generating a shopping list from recipes."""
    
    recipe_ids: List[int]
    list_name: Optional[str] = None
    merge_similar_ingredients: bool = True
    
    @field_validator('recipe_ids')
    @classmethod
    def validate_recipe_ids(cls, v: List[int]) -> List[int]:
        """Validate recipe IDs."""
        if len(v) < 1:
            raise ValueError('Must include at least one recipe')
        if len(v) > 50:
            raise ValueError('Cannot generate shopping list from more than 50 recipes')
        return list(set(v))  # Remove duplicates


class IngredientGrouping(BaseModel):
    """Schema for ingredient grouping suggestions."""
    
    category: str  # produce, meat, dairy, pantry, etc.
    ingredients: List[AggregatedIngredient]


class ShoppingListWithGrouping(ShoppingListResponse):
    """Shopping list with ingredient groupings."""
    
    ingredient_groups: List[IngredientGrouping] = []