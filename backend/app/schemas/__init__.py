"""
Pydantic schemas for API validation and serialization.
"""
# User schemas
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserLogin,
    UserResponse,
    UserProfile,
    Token,
    TokenData,
)

# Tag schemas
from app.schemas.tag import (
    TagCategory,
    TagBase,
    TagCreate,
    TagUpdate,
    TagResponse,
    TagWithCount,
    PopularTagsResponse,
)

# Recipe schemas
from app.schemas.recipe import (
    IngredientItem,
    RecipeBase,
    RecipeCreate,
    RecipeUpdate,
    RecipeResponse,
    RecipeDetailResponse,
    RecipeListResponse,
    RecipeSearchQuery,
)

# Vote schemas
from app.schemas.vote import (
    VoteValue,
    VoteBase,
    VoteCreate,
    VoteUpdate,
    VoteResponse,
    UserVoteStatus,
    VoteStatsResponse,
    RecipeVoteSummary,
)

# Shopping list schemas
from app.schemas.shopping_list import (
    AggregatedIngredient,
    ShoppingListBase,
    ShoppingListCreate,
    ShoppingListUpdate,
    ShoppingListResponse,
    ShoppingListSummary,
    GenerateShoppingListRequest,
    IngredientGrouping,
    ShoppingListWithGrouping,
)

__all__ = [
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserLogin",
    "UserResponse",
    "UserProfile",
    "Token",
    "TokenData",
    # Tag
    "TagCategory",
    "TagBase",
    "TagCreate",
    "TagUpdate",
    "TagResponse",
    "TagWithCount",
    "PopularTagsResponse",
    # Recipe
    "IngredientItem",
    "RecipeBase",
    "RecipeCreate",
    "RecipeUpdate",
    "RecipeResponse",
    "RecipeDetailResponse",
    "RecipeListResponse",
    "RecipeSearchQuery",
    # Vote
    "VoteValue",
    "VoteBase",
    "VoteCreate",
    "VoteUpdate",
    "VoteResponse",
    "UserVoteStatus",
    "VoteStatsResponse",
    "RecipeVoteSummary",
    # Shopping list
    "AggregatedIngredient",
    "ShoppingListBase",
    "ShoppingListCreate",
    "ShoppingListUpdate",
    "ShoppingListResponse",
    "ShoppingListSummary",
    "GenerateShoppingListRequest",
    "IngredientGrouping",
    "ShoppingListWithGrouping",
]