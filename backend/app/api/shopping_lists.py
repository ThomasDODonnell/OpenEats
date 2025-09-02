"""
Shopping list endpoints with ingredient aggregation and smart merging.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional

from app.config.database import get_db
from app.core.exceptions import NotFoundError, ValidationError, AuthorizationError
from app.models.shopping_list import ShoppingList
from app.models.recipe import Recipe
from app.models.user import User
from app.schemas.shopping_list import (
    ShoppingListCreate,
    ShoppingListUpdate,
    ShoppingListResponse,
    ShoppingListSummary,
    GenerateShoppingListRequest,
    IngredientGrouping,
    ShoppingListWithGrouping,
    AggregatedIngredient
)
from app.api.deps import get_current_user
from app.utils.ingredients import aggregate_recipe_ingredients, group_ingredients_by_category

router = APIRouter()


@router.post("/", response_model=ShoppingListResponse)
async def create_shopping_list(
    shopping_list_data: ShoppingListCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new shopping list from recipe ingredients.
    
    Args:
        shopping_list_data: Shopping list creation data with recipe IDs.
        current_user: Current authenticated user.
        db: Database session.
        
    Returns:
        Created shopping list with aggregated ingredients.
        
    Raises:
        NotFoundError: If any recipe is not found.
        ValidationError: If shopping list creation fails.
    """
    try:
        # Fetch recipes for the given IDs
        recipe_result = await db.execute(
            select(Recipe).where(
                and_(
                    Recipe.id.in_(shopping_list_data.recipe_ids),
                    Recipe.is_public == True  # Only allow public recipes or user's own
                )
            )
        )
        recipes = recipe_result.scalars().all()
        
        # Also fetch user's own recipes (including private ones)
        if current_user:
            user_recipe_result = await db.execute(
                select(Recipe).where(
                    and_(
                        Recipe.id.in_(shopping_list_data.recipe_ids),
                        Recipe.author_id == current_user.id
                    )
                )
            )
            user_recipes = user_recipe_result.scalars().all()
            
            # Combine and deduplicate
            recipe_dict = {r.id: r for r in recipes}
            for recipe in user_recipes:
                recipe_dict[recipe.id] = recipe
            recipes = list(recipe_dict.values())
        
        found_recipe_ids = [r.id for r in recipes]
        missing_recipe_ids = [rid for rid in shopping_list_data.recipe_ids if rid not in found_recipe_ids]
        
        if missing_recipe_ids:
            raise NotFoundError(f"Recipes not found: {missing_recipe_ids}")
        
        # Convert recipes to dicts for ingredient aggregation
        recipe_dicts = []
        for recipe in recipes:
            recipe_dicts.append({
                'id': recipe.id,
                'title': recipe.title,
                'name': recipe.title,
                'ingredients': recipe.ingredients
            })
        
        # Aggregate ingredients from all recipes
        aggregated_ingredients = aggregate_recipe_ingredients(recipe_dicts)
        
        # Convert to schema format
        ingredient_schemas = []
        for ingredient in aggregated_ingredients:
            ingredient_schemas.append(AggregatedIngredient(
                name=ingredient['name'],
                total_amount=ingredient['total_amount'],
                unit=ingredient.get('unit'),
                notes=ingredient.get('notes', []),
                recipe_names=ingredient.get('recipe_names', [])
            ))
        
        # Create shopping list record
        shopping_list = ShoppingList(
            name=shopping_list_data.name,
            description=shopping_list_data.description,
            user_id=current_user.id,
            recipe_ids=shopping_list_data.recipe_ids,
            ingredients=[ingredient.model_dump() for ingredient in ingredient_schemas]
        )
        
        db.add(shopping_list)
        await db.commit()
        await db.refresh(shopping_list)
        
        return ShoppingListResponse(
            id=shopping_list.id,
            name=shopping_list.name,
            description=shopping_list.description,
            user_id=shopping_list.user_id,
            recipe_ids=shopping_list.recipe_ids,
            ingredients=ingredient_schemas,
            created_at=shopping_list.created_at,
            updated_at=shopping_list.updated_at
        )
        
    except Exception as e:
        await db.rollback()
        if isinstance(e, (NotFoundError, ValidationError)):
            raise
        raise ValidationError(f"Shopping list creation failed: {str(e)}")


@router.post("/generate", response_model=ShoppingListWithGrouping)
async def generate_shopping_list_preview(
    request: GenerateShoppingListRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a shopping list preview without saving, with ingredient grouping.
    
    Args:
        request: Shopping list generation request.
        current_user: Current authenticated user.
        db: Database session.
        
    Returns:
        Generated shopping list with ingredient groupings.
        
    Raises:
        NotFoundError: If any recipe is not found.
    """
    # Fetch recipes (same logic as create_shopping_list)
    recipe_result = await db.execute(
        select(Recipe).where(
            and_(
                Recipe.id.in_(request.recipe_ids),
                Recipe.is_public == True
            )
        )
    )
    recipes = recipe_result.scalars().all()
    
    # Also fetch user's own recipes
    if current_user:
        user_recipe_result = await db.execute(
            select(Recipe).where(
                and_(
                    Recipe.id.in_(request.recipe_ids),
                    Recipe.user_id == current_user.id
                )
            )
        )
        user_recipes = user_recipe_result.scalars().all()
        
        recipe_dict = {r.id: r for r in recipes}
        for recipe in user_recipes:
            recipe_dict[recipe.id] = recipe
        recipes = list(recipe_dict.values())
    
    found_recipe_ids = [r.id for r in recipes]
    missing_recipe_ids = [rid for rid in request.recipe_ids if rid not in found_recipe_ids]
    
    if missing_recipe_ids:
        raise NotFoundError(f"Recipes not found: {missing_recipe_ids}")
    
    # Convert recipes to dicts
    recipe_dicts = []
    for recipe in recipes:
        recipe_dicts.append({
            'id': recipe.id,
            'title': recipe.title,
            'name': recipe.title,
            'ingredients': recipe.ingredients
        })
    
    # Aggregate ingredients
    if request.merge_similar_ingredients:
        aggregated_ingredients = aggregate_recipe_ingredients(recipe_dicts)
    else:
        # No merging, just collect all ingredients
        all_ingredients = []
        for recipe_dict in recipe_dicts:
            for ingredient in recipe_dict['ingredients']:
                if isinstance(ingredient, dict):
                    all_ingredients.append({
                        'name': ingredient.get('name', ingredient.get('ingredient', 'Unknown')),
                        'total_amount': ingredient.get('amount', '1'),
                        'unit': ingredient.get('unit'),
                        'notes': [ingredient.get('notes', '')] if ingredient.get('notes') else [],
                        'recipe_names': [recipe_dict['title']]
                    })
                else:
                    all_ingredients.append({
                        'name': str(ingredient),
                        'total_amount': '1',
                        'unit': None,
                        'notes': [],
                        'recipe_names': [recipe_dict['title']]
                    })
        aggregated_ingredients = all_ingredients
    
    # Convert to schema format
    ingredient_schemas = []
    for ingredient in aggregated_ingredients:
        ingredient_schemas.append(AggregatedIngredient(
            name=ingredient['name'],
            total_amount=ingredient['total_amount'],
            unit=ingredient.get('unit'),
            notes=ingredient.get('notes', []),
            recipe_names=ingredient.get('recipe_names', [])
        ))
    
    # Group by category
    ingredient_groups_dict = group_ingredients_by_category(aggregated_ingredients)
    ingredient_groups = []
    
    for category, ingredients in ingredient_groups_dict.items():
        category_ingredients = [
            AggregatedIngredient(
                name=ing['name'],
                total_amount=ing['total_amount'],
                unit=ing.get('unit'),
                notes=ing.get('notes', []),
                recipe_names=ing.get('recipe_names', [])
            )
            for ing in ingredients
        ]
        
        ingredient_groups.append(IngredientGrouping(
            category=category.replace('_', ' ').title(),
            ingredients=category_ingredients
        ))
    
    # Create preview response
    list_name = request.list_name or f"Shopping List ({', '.join([r.title[:20] for r in recipes[:3]])}{'...' if len(recipes) > 3 else ''})"
    
    return ShoppingListWithGrouping(
        id=0,  # Preview, no ID
        name=list_name,
        description=f"Generated from {len(recipes)} recipe{'s' if len(recipes) > 1 else ''}",
        user_id=current_user.id,
        recipe_ids=request.recipe_ids,
        ingredients=ingredient_schemas,
        ingredient_groups=ingredient_groups,
        created_at=None,  # Preview
        updated_at=None   # Preview
    )


@router.get("/", response_model=List[ShoppingListSummary])
async def get_user_shopping_lists(
    skip: int = Query(0, ge=0, description="Number of shopping lists to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of shopping lists to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's shopping lists with pagination.
    
    Args:
        skip: Number of records to skip for pagination.
        limit: Maximum number of records to return.
        current_user: Current authenticated user.
        db: Database session.
        
    Returns:
        List of shopping list summaries.
    """
    result = await db.execute(
        select(ShoppingList)
        .where(ShoppingList.user_id == current_user.id)
        .order_by(ShoppingList.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    shopping_lists = result.scalars().all()
    
    summaries = []
    for shopping_list in shopping_lists:
        summaries.append(ShoppingListSummary(
            id=shopping_list.id,
            name=shopping_list.name,
            description=shopping_list.description,
            recipe_count=len(shopping_list.recipe_ids),
            ingredient_count=len(shopping_list.ingredients),
            created_at=shopping_list.created_at
        ))
    
    return summaries


@router.get("/{shopping_list_id}", response_model=ShoppingListWithGrouping)
async def get_shopping_list(
    shopping_list_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific shopping list with ingredient grouping.
    
    Args:
        shopping_list_id: Shopping list ID.
        current_user: Current authenticated user.
        db: Database session.
        
    Returns:
        Shopping list with ingredient grouping.
        
    Raises:
        NotFoundError: If shopping list is not found.
        AuthorizationError: If user doesn't own the shopping list.
    """
    result = await db.execute(
        select(ShoppingList).where(ShoppingList.id == shopping_list_id)
    )
    shopping_list = result.scalar_one_or_none()
    
    if not shopping_list:
        raise NotFoundError("Shopping list not found")
    
    if shopping_list.user_id != current_user.id:
        raise AuthorizationError("You can only access your own shopping lists")
    
    # Convert stored ingredients to schema format
    ingredient_schemas = []
    for ingredient_data in shopping_list.ingredients:
        ingredient_schemas.append(AggregatedIngredient(
            name=ingredient_data.get('name', ''),
            total_amount=ingredient_data.get('total_amount', '1'),
            unit=ingredient_data.get('unit'),
            notes=ingredient_data.get('notes', []),
            recipe_names=ingredient_data.get('recipe_names', [])
        ))
    
    # Group by category
    ingredient_groups_dict = group_ingredients_by_category(shopping_list.ingredients)
    ingredient_groups = []
    
    for category, ingredients in ingredient_groups_dict.items():
        category_ingredients = [
            AggregatedIngredient(
                name=ing['name'],
                total_amount=ing['total_amount'],
                unit=ing.get('unit'),
                notes=ing.get('notes', []),
                recipe_names=ing.get('recipe_names', [])
            )
            for ing in ingredients
        ]
        
        ingredient_groups.append(IngredientGrouping(
            category=category.replace('_', ' ').title(),
            ingredients=category_ingredients
        ))
    
    return ShoppingListWithGrouping(
        id=shopping_list.id,
        name=shopping_list.name,
        description=shopping_list.description,
        user_id=shopping_list.user_id,
        recipe_ids=shopping_list.recipe_ids,
        ingredients=ingredient_schemas,
        ingredient_groups=ingredient_groups,
        created_at=shopping_list.created_at,
        updated_at=shopping_list.updated_at
    )


@router.put("/{shopping_list_id}", response_model=ShoppingListResponse)
async def update_shopping_list(
    shopping_list_id: int,
    update_data: ShoppingListUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a shopping list.
    
    Args:
        shopping_list_id: Shopping list ID to update.
        update_data: Updated shopping list data.
        current_user: Current authenticated user.
        db: Database session.
        
    Returns:
        Updated shopping list.
        
    Raises:
        NotFoundError: If shopping list is not found.
        AuthorizationError: If user doesn't own the shopping list.
        ValidationError: If update fails.
    """
    try:
        result = await db.execute(
            select(ShoppingList).where(ShoppingList.id == shopping_list_id)
        )
        shopping_list = result.scalar_one_or_none()
        
        if not shopping_list:
            raise NotFoundError("Shopping list not found")
        
        if shopping_list.user_id != current_user.id:
            raise AuthorizationError("You can only update your own shopping lists")
        
        # Update fields
        if update_data.name is not None:
            shopping_list.name = update_data.name
        
        if update_data.description is not None:
            shopping_list.description = update_data.description
        
        if update_data.ingredients is not None:
            # Convert schema to dict format for storage
            ingredients_data = []
            for ingredient in update_data.ingredients:
                ingredients_data.append(ingredient.model_dump())
            shopping_list.ingredients = ingredients_data
        
        await db.commit()
        await db.refresh(shopping_list)
        
        # Convert back to schema format for response
        ingredient_schemas = []
        for ingredient_data in shopping_list.ingredients:
            ingredient_schemas.append(AggregatedIngredient(
                name=ingredient_data.get('name', ''),
                total_amount=ingredient_data.get('total_amount', '1'),
                unit=ingredient_data.get('unit'),
                notes=ingredient_data.get('notes', []),
                recipe_names=ingredient_data.get('recipe_names', [])
            ))
        
        return ShoppingListResponse(
            id=shopping_list.id,
            name=shopping_list.name,
            description=shopping_list.description,
            user_id=shopping_list.user_id,
            recipe_ids=shopping_list.recipe_ids,
            ingredients=ingredient_schemas,
            created_at=shopping_list.created_at,
            updated_at=shopping_list.updated_at
        )
        
    except Exception as e:
        await db.rollback()
        if isinstance(e, (NotFoundError, AuthorizationError)):
            raise
        raise ValidationError(f"Shopping list update failed: {str(e)}")


@router.delete("/{shopping_list_id}")
async def delete_shopping_list(
    shopping_list_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a shopping list.
    
    Args:
        shopping_list_id: Shopping list ID to delete.
        current_user: Current authenticated user.
        db: Database session.
        
    Returns:
        Deletion confirmation.
        
    Raises:
        NotFoundError: If shopping list is not found.
        AuthorizationError: If user doesn't own the shopping list.
    """
    result = await db.execute(
        select(ShoppingList).where(ShoppingList.id == shopping_list_id)
    )
    shopping_list = result.scalar_one_or_none()
    
    if not shopping_list:
        raise NotFoundError("Shopping list not found")
    
    if shopping_list.user_id != current_user.id:
        raise AuthorizationError("You can only delete your own shopping lists")
    
    await db.delete(shopping_list)
    await db.commit()
    
    return {"message": "Shopping list deleted successfully"}