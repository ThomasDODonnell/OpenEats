"""
Vote model for recipe rating system.
"""
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Integer, DateTime, ForeignKey, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.recipe import Recipe


class Vote(Base):
    """Vote model with composite primary key to prevent duplicate votes."""
    
    __tablename__ = "votes"
    
    # Composite primary key to ensure one vote per user per recipe
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), primary_key=True)
    
    # Vote value: 1 for upvote, -1 for downvote
    vote_value: Mapped[int] = mapped_column(
        Integer,
        CheckConstraint("vote_value IN (-1, 1)", name="check_vote_value"),
        nullable=False
    )
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="votes",
        lazy="selectin"
    )
    recipe: Mapped["Recipe"] = relationship(
        "Recipe",
        back_populates="votes",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Vote(user_id={self.user_id}, recipe_id={self.recipe_id}, vote_value={self.vote_value})>"