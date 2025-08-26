"""
Tag model for recipe categorization and filtering.
"""
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Table, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base

if TYPE_CHECKING:
    from app.models.recipe import Recipe

# Many-to-many association table for recipes and tags
recipe_tags = Table(
    "recipe_tags",
    Base.metadata,
    mapped_column("recipe_id", ForeignKey("recipes.id"), primary_key=True),
    mapped_column("tag_id", ForeignKey("tags.id"), primary_key=True),
)


class Tag(Base):
    """Tag model for recipe categorization and filtering."""
    
    __tablename__ = "tags"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Tag fields
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    
    # Relationships
    recipes: Mapped[List["Recipe"]] = relationship(
        "Recipe",
        secondary=recipe_tags,
        back_populates="tags",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name='{self.name}', category='{self.category}')>"