"""
Voting system endpoints with vote aggregation.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config.database import get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.models.vote import Vote
from app.models.recipe import Recipe
from app.models.user import User
from app.schemas.vote import VoteCreate, VoteResponse, UserVoteStatus, VoteStatsResponse
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/recipes/{recipe_id}", response_model=VoteStatsResponse)
async def vote_on_recipe(
    recipe_id: int,
    vote_data: VoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Vote on a recipe (upvote or downvote).
    
    Args:
        recipe_id: Recipe ID to vote on.
        vote_data: Vote data (1 for upvote, -1 for downvote).
        current_user: Current authenticated user.
        db: Database session.
        
    Returns:
        Updated vote statistics for the recipe.
        
    Raises:
        NotFoundError: If recipe is not found.
        ValidationError: If voting fails.
    """
    try:
        # Check if recipe exists
        recipe_result = await db.execute(
            select(Recipe).where(Recipe.id == recipe_id)
        )
        recipe = recipe_result.scalar_one_or_none()
        
        if not recipe:
            raise NotFoundError("Recipe not found")
        
        # Check if user already voted
        existing_vote_result = await db.execute(
            select(Vote).where(
                Vote.user_id == current_user.id,
                Vote.recipe_id == recipe_id
            )
        )
        existing_vote = existing_vote_result.scalar_one_or_none()
        
        old_vote_value = 0
        
        if existing_vote:
            # User changing vote
            old_vote_value = existing_vote.vote_value
            existing_vote.vote_value = vote_data.vote_value
        else:
            # New vote
            new_vote = Vote(
                user_id=current_user.id,
                recipe_id=recipe_id,
                vote_value=vote_data.vote_value
            )
            db.add(new_vote)
        
        # Update denormalized vote counts atomically
        if vote_data.vote_value == 1:  # Upvote
            if old_vote_value == -1:  # Changed from downvote
                recipe.upvotes += 1
                recipe.downvotes -= 1
            elif old_vote_value == 0:  # New upvote
                recipe.upvotes += 1
        else:  # Downvote (-1)
            if old_vote_value == 1:  # Changed from upvote
                recipe.downvotes += 1
                recipe.upvotes -= 1
            elif old_vote_value == 0:  # New downvote
                recipe.downvotes += 1
        
        # Update vote score
        recipe.vote_score = recipe.upvotes - recipe.downvotes
        
        await db.commit()
        
        return VoteStatsResponse(
            recipe_id=recipe_id,
            upvotes=recipe.upvotes,
            downvotes=recipe.downvotes,
            vote_score=recipe.vote_score,
            total_votes=recipe.upvotes + recipe.downvotes
        )
    
    except Exception as e:
        await db.rollback()
        if isinstance(e, NotFoundError):
            raise
        raise ValidationError(f"Voting failed: {str(e)}")


@router.delete("/recipes/{recipe_id}", response_model=VoteStatsResponse)
async def remove_vote(
    recipe_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove user's vote from a recipe.
    
    Args:
        recipe_id: Recipe ID to remove vote from.
        current_user: Current authenticated user.
        db: Database session.
        
    Returns:
        Updated vote statistics for the recipe.
        
    Raises:
        NotFoundError: If recipe or vote is not found.
    """
    try:
        # Check if recipe exists
        recipe_result = await db.execute(
            select(Recipe).where(Recipe.id == recipe_id)
        )
        recipe = recipe_result.scalar_one_or_none()
        
        if not recipe:
            raise NotFoundError("Recipe not found")
        
        # Check if user has voted
        vote_result = await db.execute(
            select(Vote).where(
                Vote.user_id == current_user.id,
                Vote.recipe_id == recipe_id
            )
        )
        vote = vote_result.scalar_one_or_none()
        
        if not vote:
            raise NotFoundError("Vote not found")
        
        # Remove vote and update counts
        if vote.vote_value == 1:  # Removing upvote
            recipe.upvotes -= 1
        else:  # Removing downvote
            recipe.downvotes -= 1
        
        # Update vote score
        recipe.vote_score = recipe.upvotes - recipe.downvotes
        
        await db.delete(vote)
        await db.commit()
        
        return VoteStatsResponse(
            recipe_id=recipe_id,
            upvotes=recipe.upvotes,
            downvotes=recipe.downvotes,
            vote_score=recipe.vote_score,
            total_votes=recipe.upvotes + recipe.downvotes
        )
    
    except Exception as e:
        await db.rollback()
        if isinstance(e, NotFoundError):
            raise
        raise ValidationError(f"Vote removal failed: {str(e)}")


@router.get("/recipes/{recipe_id}", response_model=UserVoteStatus)
async def get_user_vote_status(
    recipe_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's vote status for a recipe.
    
    Args:
        recipe_id: Recipe ID to check vote status for.
        current_user: Current authenticated user.
        db: Database session.
        
    Returns:
        User's vote status and recipe vote statistics.
        
    Raises:
        NotFoundError: If recipe is not found.
    """
    # Check if recipe exists and get vote stats
    recipe_result = await db.execute(
        select(Recipe).where(Recipe.id == recipe_id)
    )
    recipe = recipe_result.scalar_one_or_none()
    
    if not recipe:
        raise NotFoundError("Recipe not found")
    
    # Check user's vote
    vote_result = await db.execute(
        select(Vote).where(
            Vote.user_id == current_user.id,
            Vote.recipe_id == recipe_id
        )
    )
    vote = vote_result.scalar_one_or_none()
    
    user_vote = vote.vote_value if vote else None
    
    return UserVoteStatus(
        recipe_id=recipe_id,
        user_vote=user_vote,
        total_upvotes=recipe.upvotes,
        total_downvotes=recipe.downvotes,
        vote_score=recipe.vote_score
    )


@router.get("/recipes/{recipe_id}/stats", response_model=VoteStatsResponse)
async def get_recipe_vote_stats(
    recipe_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get vote statistics for a recipe.
    
    Args:
        recipe_id: Recipe ID to get stats for.
        db: Database session.
        
    Returns:
        Recipe vote statistics.
        
    Raises:
        NotFoundError: If recipe is not found.
    """
    recipe_result = await db.execute(
        select(Recipe).where(Recipe.id == recipe_id)
    )
    recipe = recipe_result.scalar_one_or_none()
    
    if not recipe:
        raise NotFoundError("Recipe not found")
    
    return VoteStatsResponse(
        recipe_id=recipe_id,
        upvotes=recipe.upvotes,
        downvotes=recipe.downvotes,
        vote_score=recipe.vote_score,
        total_votes=recipe.upvotes + recipe.downvotes
    )