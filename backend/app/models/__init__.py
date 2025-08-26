"""
Database models for the GoodEats application.

This module imports all models to ensure they are registered with SQLAlchemy.
"""
from app.models.user import User
from app.models.tag import Tag, recipe_tags
from app.models.recipe import Recipe
from app.models.vote import Vote
from app.models.shopping_list import ShoppingList

__all__ = [
    "User",
    "Tag",
    "Recipe",
    "Vote", 
    "ShoppingList",
    "recipe_tags",
]