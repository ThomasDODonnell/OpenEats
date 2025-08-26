"""
Pydantic schemas for vote-related API operations.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator
from enum import IntEnum


class VoteValue(IntEnum):
    """Vote values enum."""
    
    DOWNVOTE = -1
    UPVOTE = 1


class VoteBase(BaseModel):
    """Base vote schema."""
    
    vote_value: VoteValue
    
    @field_validator('vote_value')
    @classmethod
    def validate_vote_value(cls, v: int) -> int:
        """Validate vote value."""
        if v not in [-1, 1]:
            raise ValueError('Vote value must be either -1 (downvote) or 1 (upvote)')
        return v


class VoteCreate(VoteBase):
    """Schema for creating a vote."""
    pass


class VoteUpdate(VoteBase):
    """Schema for updating a vote."""
    pass


class VoteResponse(VoteBase):
    """Schema for vote responses."""
    
    model_config = ConfigDict(from_attributes=True)
    
    user_id: int
    recipe_id: int
    created_at: datetime


class UserVoteStatus(BaseModel):
    """Schema for user's vote status on a recipe."""
    
    recipe_id: int
    user_vote: Optional[VoteValue] = None
    total_upvotes: int = 0
    total_downvotes: int = 0
    vote_score: int = 0


class VoteStatsResponse(BaseModel):
    """Schema for vote statistics."""
    
    recipe_id: int
    upvotes: int = 0
    downvotes: int = 0
    vote_score: int = 0
    total_votes: int = 0
    
    @property
    def upvote_percentage(self) -> float:
        """Calculate upvote percentage."""
        if self.total_votes == 0:
            return 0.0
        return (self.upvotes / self.total_votes) * 100


class RecipeVoteSummary(BaseModel):
    """Schema for recipe vote summary."""
    
    recipe_id: int
    recipe_title: str
    vote_score: int
    upvotes: int
    downvotes: int
    user_vote: Optional[VoteValue] = None