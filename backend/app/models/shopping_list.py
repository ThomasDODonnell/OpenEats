"""
Shopping list model for ingredient aggregation from multiple recipes.
"""
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, DateTime, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class ShoppingList(Base):
    """Shopping list model for aggregated ingredients from multiple recipes."""
    
    __tablename__ = "shopping_lists"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # List metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Owner
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Recipe IDs that contributed to this shopping list
    recipe_ids: Mapped[List[int]] = mapped_column(JSON, nullable=False)
    
    # Aggregated ingredients with quantities
    ingredients: Mapped[List[dict]] = mapped_column(JSON, nullable=False)
    
    # Custom ingredients added manually by user
    custom_ingredients: Mapped[List[dict]] = mapped_column(JSON, nullable=False, default=list)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<ShoppingList(id={self.id}, name='{self.name}', user_id={self.user_id})>"