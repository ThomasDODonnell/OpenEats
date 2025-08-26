"""
Tag management endpoints with categories and popularity tracking.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.exc import IntegrityError

from app.config.database import get_db
from app.core.exceptions import NotFoundError, ConflictError, ValidationError, AuthorizationError
from app.models.tag import Tag, recipe_tags
from app.models.recipe import Recipe
from app.models.user import User
from app.schemas.tag import (
    TagCreate, TagUpdate, TagResponse, TagWithCount,
    PopularTagsResponse, TagCategory
)
from app.api.deps import get_current_user, get_current_user_optional

router = APIRouter()


@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: TagCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new tag.
    
    Args:
        tag_data: Tag creation data.
        current_user: Current authenticated user.
        db: Database session.
        
    Returns:
        Created tag information.
        
    Raises:
        ConflictError: If tag name already exists.
        ValidationError: If tag data is invalid.
    """
    try:
        # Check if tag already exists
        result = await db.execute(
            select(Tag).where(Tag.name == tag_data.name)
        )
        existing_tag = result.scalar_one_or_none()
        
        if existing_tag:
            raise ConflictError(f"Tag '{tag_data.name}' already exists")
        
        # Create new tag
        new_tag = Tag(
            name=tag_data.name,
            category=tag_data.category.value
        )
        
        db.add(new_tag)
        await db.commit()
        await db.refresh(new_tag)
        
        return new_tag
    
    except IntegrityError:
        await db.rollback()
        raise ConflictError(f"Tag '{tag_data.name}' already exists")
    
    except Exception as e:
        await db.rollback()
        if isinstance(e, ConflictError):
            raise
        raise ValidationError(f"Tag creation failed: {str(e)}")


@router.get("/", response_model=List[TagResponse])
async def get_tags(
    category: Optional[TagCategory] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all tags, optionally filtered by category.
    
    Args:
        category: Optional category filter.
        limit: Maximum number of tags to return.
        db: Database session.
        
    Returns:
        List of tags.
    """
    query = select(Tag).order_by(Tag.name)
    
    if category:
        query = query.where(Tag.category == category.value)
    
    query = query.limit(limit)
    
    result = await db.execute(query)
    tags = result.scalars().all()
    
    return tags


@router.get("/popular", response_model=PopularTagsResponse)
async def get_popular_tags(
    limit_per_category: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    Get popular tags grouped by category.
    
    Args:
        limit_per_category: Maximum number of tags per category.
        db: Database session.
        
    Returns:
        Popular tags grouped by category with recipe counts.
    """
    # Query to get tag usage counts
    tag_counts_query = (
        select(
            Tag.id,
            Tag.name,
            Tag.category,
            func.count(recipe_tags.c.recipe_id).label('recipe_count')
        )
        .select_from(Tag)
        .outerjoin(recipe_tags)
        .outerjoin(Recipe)
        .where(Recipe.is_public == True)  # Only count public recipes
        .group_by(Tag.id, Tag.name, Tag.category)
        .having(func.count(recipe_tags.c.recipe_id) > 0)  # Only tags with recipes
        .order_by(desc('recipe_count'))
    )
    
    result = await db.execute(tag_counts_query)
    tag_data = result.fetchall()
    
    # Group by category
    categories = {category.value: [] for category in TagCategory}
    
    for tag_row in tag_data:
        tag_id, name, category, count = tag_row
        if category in categories and len(categories[category]) < limit_per_category:
            categories[category].append(TagWithCount(
                id=tag_id,
                name=name,
                category=category,
                recipe_count=count
            ))
    
    return PopularTagsResponse(
        dietary=categories.get('dietary', []),
        protein=categories.get('protein', []),
        meal_type=categories.get('meal_type', []),
        cuisine=categories.get('cuisine', []),
        cooking_method=categories.get('cooking_method', []),
        difficulty=categories.get('difficulty', []),
        time=categories.get('time', []),
        occasion=categories.get('occasion', []),
        lifestyle=categories.get('lifestyle', [])
    )


@router.get("/search", response_model=List[TagResponse])
async def search_tags(
    q: str = Query(..., min_length=1),
    category: Optional[TagCategory] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Search for tags by name.
    
    Args:
        q: Search query.
        category: Optional category filter.
        limit: Maximum number of results.
        db: Database session.
        
    Returns:
        List of matching tags.
    """
    query = select(Tag).where(
        Tag.name.ilike(f"%{q}%")
    ).order_by(Tag.name).limit(limit)
    
    if category:
        query = query.where(Tag.category == category.value)
    
    result = await db.execute(query)
    tags = result.scalars().all()
    
    return tags


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get tag by ID.
    
    Args:
        tag_id: Tag ID to retrieve.
        db: Database session.
        
    Returns:
        Tag information.
        
    Raises:
        NotFoundError: If tag is not found.
    """
    result = await db.execute(
        select(Tag).where(Tag.id == tag_id)
    )
    tag = result.scalar_one_or_none()
    
    if not tag:
        raise NotFoundError("Tag not found")
    
    return tag


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: int,
    tag_update: TagUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a tag.
    
    Args:
        tag_id: Tag ID to update.
        tag_update: Tag update data.
        current_user: Current authenticated user.
        db: Database session.
        
    Returns:
        Updated tag information.
        
    Raises:
        NotFoundError: If tag is not found.
        ConflictError: If updated name conflicts with existing tag.
        ValidationError: If update data is invalid.
    """
    # Get tag
    result = await db.execute(
        select(Tag).where(Tag.id == tag_id)
    )
    tag = result.scalar_one_or_none()
    
    if not tag:
        raise NotFoundError("Tag not found")
    
    try:
        # Check for name conflicts if name is being updated
        if tag_update.name is not None and tag_update.name != tag.name:
            existing_result = await db.execute(
                select(Tag).where(Tag.name == tag_update.name)
            )
            existing_tag = existing_result.scalar_one_or_none()
            
            if existing_tag:
                raise ConflictError(f"Tag '{tag_update.name}' already exists")
            
            tag.name = tag_update.name
        
        # Update category if provided
        if tag_update.category is not None:
            tag.category = tag_update.category.value
        
        await db.commit()
        await db.refresh(tag)
        
        return tag
    
    except Exception as e:
        await db.rollback()
        if isinstance(e, ConflictError):
            raise
        raise ValidationError(f"Tag update failed: {str(e)}")


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a tag.
    
    Note: This will remove the tag from all recipes that use it.
    
    Args:
        tag_id: Tag ID to delete.
        current_user: Current authenticated user.
        db: Database session.
        
    Raises:
        NotFoundError: If tag is not found.
    """
    # Get tag
    result = await db.execute(
        select(Tag).where(Tag.id == tag_id)
    )
    tag = result.scalar_one_or_none()
    
    if not tag:
        raise NotFoundError("Tag not found")
    
    try:
        await db.delete(tag)
        await db.commit()
    
    except Exception as e:
        await db.rollback()
        raise ValidationError(f"Tag deletion failed: {str(e)}")