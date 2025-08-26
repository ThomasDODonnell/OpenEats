"""
Recipe management endpoints with tag filtering and search.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.config.database import get_db
from app.core.exceptions import NotFoundError, AuthorizationError, ValidationError
from app.models.recipe import Recipe
from app.models.tag import Tag, recipe_tags
from app.models.user import User
from app.schemas.recipe import (
    RecipeCreate, RecipeUpdate, RecipeResponse, RecipeDetailResponse,
    RecipeListResponse, RecipeSearchQuery
)
from app.api.deps import get_current_user, get_current_user_optional

router = APIRouter()


@router.post("/", response_model=RecipeDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    recipe_data: RecipeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new recipe.
    
    Args:
        recipe_data: Recipe creation data.
        current_user: Current authenticated user.
        db: Database session.
        
    Returns:
        Created recipe with full details.
        
    Raises:
        ValidationError: If recipe data is invalid.
    """
    try:
        # Convert ingredients to proper format for JSON storage
        ingredients_data = [ingredient.model_dump() for ingredient in recipe_data.ingredients]
        
        # Create new recipe
        new_recipe = Recipe(
            title=recipe_data.title,
            description=recipe_data.description,
            ingredients=ingredients_data,
            instructions=recipe_data.instructions,
            prep_time_minutes=recipe_data.prep_time_minutes,
            cook_time_minutes=recipe_data.cook_time_minutes,
            servings=recipe_data.servings,
            is_public=recipe_data.is_public,
            author_id=current_user.id
        )
        
        db.add(new_recipe)
        await db.flush()  # Get the recipe ID
        
        # Add tags if provided
        if recipe_data.tag_ids:
            # Verify all tags exist
            result = await db.execute(
                select(Tag).where(Tag.id.in_(recipe_data.tag_ids))
            )
            tags = result.scalars().all()
            
            if len(tags) != len(recipe_data.tag_ids):
                raise ValidationError("One or more tags not found")
            
            new_recipe.tags = tags
        
        await db.commit()
        await db.refresh(new_recipe)
        
        # Load relationships
        await db.refresh(new_recipe, ['author', 'tags'])
        
        return new_recipe
    
    except Exception as e:
        await db.rollback()
        if isinstance(e, ValidationError):
            raise
        raise ValidationError(f"Recipe creation failed: {str(e)}")


@router.get("/", response_model=RecipeListResponse)
async def get_recipes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    tags: Optional[List[str]] = Query(None),
    search: Optional[str] = Query(None),
    is_public: Optional[bool] = Query(None),
    author_id: Optional[int] = Query(None),
    min_vote_score: Optional[int] = Query(None),
    max_prep_time: Optional[int] = Query(None),
    max_cook_time: Optional[int] = Query(None),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recipes with filtering and search capabilities.
    
    Args:
        skip: Number of recipes to skip.
        limit: Maximum number of recipes to return.
        tags: List of tag names to filter by.
        search: Search query for title and description.
        is_public: Filter by public/private recipes.
        author_id: Filter by author ID.
        min_vote_score: Minimum vote score filter.
        max_prep_time: Maximum prep time in minutes.
        max_cook_time: Maximum cook time in minutes.
        current_user: Current authenticated user (optional).
        db: Database session.
        
    Returns:
        Paginated list of recipes with metadata.
    """
    # Build base query
    query = select(Recipe).options(
        selectinload(Recipe.author),
        selectinload(Recipe.tags)
    )
    
    # Apply filters
    filters = []
    
    # Public/private filter
    if is_public is not None:
        filters.append(Recipe.is_public == is_public)
    elif not current_user:
        # Non-authenticated users can only see public recipes
        filters.append(Recipe.is_public == True)
    
    # Author filter
    if author_id:
        filters.append(Recipe.author_id == author_id)
    elif current_user and is_public is False:
        # If filtering for private recipes, only show current user's recipes
        filters.append(Recipe.author_id == current_user.id)
    
    # Vote score filter
    if min_vote_score is not None:
        filters.append(Recipe.vote_score >= min_vote_score)
    
    # Time filters
    if max_prep_time is not None:
        filters.append(Recipe.prep_time_minutes <= max_prep_time)
    
    if max_cook_time is not None:
        filters.append(Recipe.cook_time_minutes <= max_cook_time)
    
    # Text search
    if search:
        search_filter = or_(
            Recipe.title.ilike(f"%{search}%"),
            Recipe.description.ilike(f"%{search}%")
        )
        filters.append(search_filter)
    
    # Apply all filters
    if filters:
        query = query.where(and_(*filters))
    
    # Tag filtering (many-to-many)
    if tags:
        # Convert tag names to IDs
        tag_result = await db.execute(
            select(Tag.id).where(Tag.name.in_(tags))
        )
        tag_ids = [row[0] for row in tag_result.fetchall()]
        
        if tag_ids:
            # Join with recipe_tags for filtering
            query = query.join(Recipe.tags).where(Tag.id.in_(tag_ids))
            # Group by recipe to avoid duplicates when multiple tags match
            query = query.group_by(Recipe.id)
    
    # Get total count for pagination
    count_query = select(func.count()).select_from(
        query.subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination and ordering
    query = query.order_by(Recipe.created_at.desc()).offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    recipes = result.scalars().all()
    
    # Calculate pagination metadata
    pages = (total + limit - 1) // limit if total > 0 else 1
    page = (skip // limit) + 1
    
    return RecipeListResponse(
        items=recipes,
        total=total,
        page=page,
        size=limit,
        pages=pages
    )


@router.get("/{recipe_id}", response_model=RecipeDetailResponse)
async def get_recipe(
    recipe_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recipe by ID with full details.
    
    Args:
        recipe_id: Recipe ID to retrieve.
        current_user: Current authenticated user (optional).
        db: Database session.
        
    Returns:
        Recipe with full details including author and tags.
        
    Raises:
        NotFoundError: If recipe is not found or not accessible.
    """
    query = select(Recipe).options(
        selectinload(Recipe.author),
        selectinload(Recipe.tags)
    ).where(Recipe.id == recipe_id)
    
    result = await db.execute(query)
    recipe = result.scalar_one_or_none()
    
    if not recipe:
        raise NotFoundError("Recipe not found")
    
    # Check access permissions
    if not recipe.is_public:
        if not current_user or recipe.author_id != current_user.id:
            raise NotFoundError("Recipe not found")
    
    return recipe


@router.put("/{recipe_id}", response_model=RecipeDetailResponse)
async def update_recipe(
    recipe_id: int,
    recipe_update: RecipeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a recipe.
    
    Args:
        recipe_id: Recipe ID to update.
        recipe_update: Recipe update data.
        current_user: Current authenticated user.
        db: Database session.
        
    Returns:
        Updated recipe with full details.
        
    Raises:
        NotFoundError: If recipe is not found.
        AuthorizationError: If user is not the recipe author.
        ValidationError: If update data is invalid.
    """
    # Get recipe
    result = await db.execute(
        select(Recipe).where(Recipe.id == recipe_id)
    )
    recipe = result.scalar_one_or_none()
    
    if not recipe:
        raise NotFoundError("Recipe not found")
    
    # Check authorization
    if recipe.author_id != current_user.id:
        raise AuthorizationError("Not authorized to update this recipe")
    
    try:
        # Update fields
        if recipe_update.title is not None:
            recipe.title = recipe_update.title
        
        if recipe_update.description is not None:
            recipe.description = recipe_update.description
        
        if recipe_update.ingredients is not None:
            recipe.ingredients = [ingredient.model_dump() for ingredient in recipe_update.ingredients]
        
        if recipe_update.instructions is not None:
            recipe.instructions = recipe_update.instructions
        
        if recipe_update.prep_time_minutes is not None:
            recipe.prep_time_minutes = recipe_update.prep_time_minutes
        
        if recipe_update.cook_time_minutes is not None:
            recipe.cook_time_minutes = recipe_update.cook_time_minutes
        
        if recipe_update.servings is not None:
            recipe.servings = recipe_update.servings
        
        if recipe_update.is_public is not None:
            recipe.is_public = recipe_update.is_public
        
        # Update tags if provided
        if recipe_update.tag_ids is not None:
            if recipe_update.tag_ids:
                # Verify all tags exist
                tag_result = await db.execute(
                    select(Tag).where(Tag.id.in_(recipe_update.tag_ids))
                )
                tags = tag_result.scalars().all()
                
                if len(tags) != len(recipe_update.tag_ids):
                    raise ValidationError("One or more tags not found")
                
                recipe.tags = tags
            else:
                recipe.tags = []
        
        await db.commit()
        await db.refresh(recipe, ['author', 'tags'])
        
        return recipe
    
    except Exception as e:
        await db.rollback()
        if isinstance(e, (ValidationError, AuthorizationError)):
            raise
        raise ValidationError(f"Recipe update failed: {str(e)}")


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(
    recipe_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a recipe.
    
    Args:
        recipe_id: Recipe ID to delete.
        current_user: Current authenticated user.
        db: Database session.
        
    Raises:
        NotFoundError: If recipe is not found.
        AuthorizationError: If user is not the recipe author.
    """
    # Get recipe
    result = await db.execute(
        select(Recipe).where(Recipe.id == recipe_id)
    )
    recipe = result.scalar_one_or_none()
    
    if not recipe:
        raise NotFoundError("Recipe not found")
    
    # Check authorization
    if recipe.author_id != current_user.id:
        raise AuthorizationError("Not authorized to delete this recipe")
    
    try:
        await db.delete(recipe)
        await db.commit()
    
    except Exception as e:
        await db.rollback()
        raise ValidationError(f"Recipe deletion failed: {str(e)}")


@router.get("/user/{user_id}", response_model=RecipeListResponse)
async def get_user_recipes(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recipes by user ID.
    
    Args:
        user_id: User ID whose recipes to retrieve.
        skip: Number of recipes to skip.
        limit: Maximum number of recipes to return.
        current_user: Current authenticated user (optional).
        db: Database session.
        
    Returns:
        Paginated list of user's recipes.
    """
    # Verify user exists
    user_result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise NotFoundError("User not found")
    
    # Build query with privacy filtering
    query = select(Recipe).options(
        selectinload(Recipe.author),
        selectinload(Recipe.tags)
    ).where(Recipe.author_id == user_id)
    
    # Filter by public recipes unless viewing own recipes
    if not current_user or current_user.id != user_id:
        query = query.where(Recipe.is_public == True)
    
    # Get total count
    count_query = select(func.count()).select_from(
        query.subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination and ordering
    query = query.order_by(Recipe.created_at.desc()).offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    recipes = result.scalars().all()
    
    # Calculate pagination metadata
    pages = (total + limit - 1) // limit if total > 0 else 1
    page = (skip // limit) + 1
    
    return RecipeListResponse(
        items=recipes,
        total=total,
        page=page,
        size=limit,
        pages=pages
    )