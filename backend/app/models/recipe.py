"""
Recipe model with tag relationships and voting support.
"""
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, DateTime, Text, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base
from app.models.tag import recipe_tags

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.tag import Tag
    from app.models.vote import Vote


class Recipe(Base):
    """Recipe model with ingredients, tags, and voting support."""
    
    __tablename__ = "recipes"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Basic recipe fields
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Recipe content (JSON for shopping list grouping)
    ingredients: Mapped[List[dict]] = mapped_column(JSON, nullable=False)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Time and serving info
    prep_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    cook_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    servings: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Visibility
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Author relationship
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    
    # Voting fields (denormalized for performance)
    upvotes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    downvotes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    vote_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    
    # Relationships
    author: Mapped["User"] = relationship(
        "User",
        back_populates="recipes",
        lazy="selectin"
    )
    tags: Mapped[List["Tag"]] = relationship(
        "Tag",
        secondary=recipe_tags,
        back_populates="recipes",
        lazy="selectin"
    )
    votes: Mapped[List["Vote"]] = relationship(
        "Vote",
        back_populates="recipe",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    @property
    def total_time_minutes(self) -> int:
        """Calculate total time for recipe."""
        return self.prep_time_minutes + self.cook_time_minutes
    
    def __repr__(self) -> str:
        return f"<Recipe(id={self.id}, title='{self.title}', author_id={self.author_id})>"