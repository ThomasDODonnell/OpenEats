"""
Pytest configuration and fixtures for the GoodEats backend tests.
"""
import asyncio
import pytest
from typing import AsyncGenerator, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timedelta

from app.main import app
from app.config.database import Base, get_db
from app.config.settings import settings
from app.core.security import create_access_token, get_password_hash
from app.models import User, Recipe, Tag, Vote, ShoppingList


# Test database URL (SQLite in-memory)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an instance of the default event loop for the test session.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a clean database session for each test.
    """
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    # Drop tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test client with database session override.
    """
    def override_get_db():
        return db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver"
    ) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user_data() -> Dict[str, Any]:
    """
    Test user data for registration/login.
    """
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User"
    }


@pytest.fixture
async def test_user(db_session: AsyncSession, test_user_data: Dict[str, Any]) -> User:
    """
    Create a test user in the database.
    """
    user = User(
        email=test_user_data["email"],
        hashed_password=get_password_hash(test_user_data["password"]),
        first_name=test_user_data["first_name"],
        last_name=test_user_data["last_name"],
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_user_token(test_user: User) -> str:
    """
    Create a valid JWT token for the test user.
    """
    access_token_expires = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    return create_access_token(
        data={"sub": str(test_user.id)},
        expires_delta=access_token_expires
    )


@pytest.fixture
async def authenticated_client(client: AsyncClient, test_user_token: str) -> AsyncClient:
    """
    Create an authenticated test client with Authorization header.
    """
    client.headers.update({"Authorization": f"Bearer {test_user_token}"})
    return client


@pytest.fixture
async def test_tags(db_session: AsyncSession) -> list[Tag]:
    """
    Create test tags in the database.
    """
    tags_data = [
        {"name": "vegetarian", "category": "dietary"},
        {"name": "vegan", "category": "dietary"},
        {"name": "gluten-free", "category": "dietary"},
        {"name": "chicken", "category": "protein"},
        {"name": "beef", "category": "protein"},
        {"name": "breakfast", "category": "meal_type"},
        {"name": "lunch", "category": "meal_type"},
        {"name": "dinner", "category": "meal_type"},
        {"name": "dessert", "category": "meal_type"},
        {"name": "quick", "category": "time"},
        {"name": "comfort", "category": "cuisine"}
    ]
    
    tags = []
    for tag_data in tags_data:
        tag = Tag(**tag_data)
        db_session.add(tag)
        tags.append(tag)
    
    await db_session.commit()
    
    # Refresh all tags
    for tag in tags:
        await db_session.refresh(tag)
    
    return tags


@pytest.fixture
async def test_recipe_data() -> Dict[str, Any]:
    """
    Test recipe data for creation.
    """
    return {
        "title": "Test Recipe",
        "description": "A delicious test recipe",
        "ingredients": [
            {"name": "flour", "amount": "2 cups", "unit": "cup"},
            {"name": "milk", "amount": "1 cup", "unit": "cup"},
            {"name": "eggs", "amount": "2", "unit": "piece"}
        ],
        "instructions": "1. Mix ingredients\n2. Cook for 30 minutes\n3. Serve hot",
        "prep_time_minutes": 15,
        "cook_time_minutes": 30,
        "servings": 4,
        "is_public": True
    }


@pytest.fixture
async def test_recipe(
    db_session: AsyncSession,
    test_user: User,
    test_recipe_data: Dict[str, Any],
    test_tags: list[Tag]
) -> Recipe:
    """
    Create a test recipe in the database.
    """
    recipe = Recipe(
        **test_recipe_data,
        author_id=test_user.id
    )
    
    # Add some tags
    recipe.tags = test_tags[:3]  # First 3 tags
    
    db_session.add(recipe)
    await db_session.commit()
    await db_session.refresh(recipe)
    return recipe


@pytest.fixture
async def test_private_recipe(
    db_session: AsyncSession,
    test_user: User,
    test_tags: list[Tag]
) -> Recipe:
    """
    Create a private test recipe in the database.
    """
    recipe = Recipe(
        title="Private Test Recipe",
        description="A private test recipe",
        ingredients=[
            {"name": "secret ingredient", "amount": "1", "unit": "pinch"}
        ],
        instructions="1. Keep it secret\n2. Keep it safe",
        prep_time_minutes=5,
        cook_time_minutes=10,
        servings=1,
        is_public=False,
        author_id=test_user.id
    )
    
    recipe.tags = test_tags[3:5]  # Different tags
    
    db_session.add(recipe)
    await db_session.commit()
    await db_session.refresh(recipe)
    return recipe


@pytest.fixture
async def test_second_user(db_session: AsyncSession) -> User:
    """
    Create a second test user for multi-user tests.
    """
    user = User(
        email="second@example.com",
        hashed_password=get_password_hash("password123"),
        first_name="Second",
        last_name="User",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_vote(
    db_session: AsyncSession,
    test_user: User,
    test_recipe: Recipe
) -> Vote:
    """
    Create a test vote in the database.
    """
    vote = Vote(
        user_id=test_user.id,
        recipe_id=test_recipe.id,
        vote_value=1  # Upvote
    )
    db_session.add(vote)
    await db_session.commit()
    await db_session.refresh(vote)
    return vote


@pytest.fixture
async def test_shopping_list_data() -> Dict[str, Any]:
    """
    Test shopping list data.
    """
    return {
        "name": "Weekly Shopping",
        "recipe_ids": [],  # Will be populated in tests
        "custom_ingredients": [
            {"name": "bread", "amount": "1 loaf", "category": "bakery"},
            {"name": "bananas", "amount": "6", "category": "produce"}
        ]
    }


@pytest.fixture
async def test_shopping_list(
    db_session: AsyncSession,
    test_user: User,
    test_recipe: Recipe,
    test_shopping_list_data: Dict[str, Any]
) -> ShoppingList:
    """
    Create a test shopping list in the database.
    """
    shopping_list_data = test_shopping_list_data.copy()
    shopping_list_data["recipe_ids"] = [test_recipe.id]
    
    shopping_list = ShoppingList(
        name=shopping_list_data["name"],
        user_id=test_user.id,
        recipe_ids=shopping_list_data["recipe_ids"],
        custom_ingredients=shopping_list_data["custom_ingredients"]
    )
    
    db_session.add(shopping_list)
    await db_session.commit()
    await db_session.refresh(shopping_list)
    return shopping_list


# Utility fixtures for common test scenarios
@pytest.fixture
async def multiple_recipes(
    db_session: AsyncSession,
    test_user: User,
    test_second_user: User,
    test_tags: list[Tag]
) -> list[Recipe]:
    """
    Create multiple test recipes for pagination and filtering tests.
    """
    recipes_data = [
        {
            "title": "Chicken Stir Fry",
            "description": "Quick and healthy chicken stir fry",
            "ingredients": [{"name": "chicken", "amount": "1 lb", "unit": "lb"}],
            "instructions": "Cook chicken with vegetables",
            "prep_time_minutes": 10,
            "cook_time_minutes": 15,
            "servings": 4,
            "is_public": True,
            "author_id": test_user.id,
            "tags": [test_tags[3], test_tags[7]]  # chicken, dinner
        },
        {
            "title": "Vegan Buddha Bowl",
            "description": "Nutritious vegan bowl",
            "ingredients": [{"name": "quinoa", "amount": "1 cup", "unit": "cup"}],
            "instructions": "Prepare quinoa and vegetables",
            "prep_time_minutes": 20,
            "cook_time_minutes": 25,
            "servings": 2,
            "is_public": True,
            "author_id": test_second_user.id,
            "tags": [test_tags[1], test_tags[6]]  # vegan, lunch
        },
        {
            "title": "Gluten-Free Pancakes",
            "description": "Fluffy gluten-free pancakes",
            "ingredients": [{"name": "almond flour", "amount": "2 cups", "unit": "cup"}],
            "instructions": "Mix and cook pancakes",
            "prep_time_minutes": 5,
            "cook_time_minutes": 10,
            "servings": 3,
            "is_public": True,
            "author_id": test_user.id,
            "tags": [test_tags[2], test_tags[5]]  # gluten-free, breakfast
        }
    ]
    
    recipes = []
    for recipe_data in recipes_data:
        tags = recipe_data.pop("tags")
        recipe = Recipe(**recipe_data)
        recipe.tags = tags
        db_session.add(recipe)
        recipes.append(recipe)
    
    await db_session.commit()
    
    # Refresh all recipes
    for recipe in recipes:
        await db_session.refresh(recipe)
    
    return recipes


@pytest.fixture
async def recipes_with_votes(
    db_session: AsyncSession,
    multiple_recipes: list[Recipe],
    test_user: User,
    test_second_user: User
) -> list[Recipe]:
    """
    Add votes to recipes for voting system tests.
    """
    # Recipe 1: 2 upvotes, 1 downvote (score: 1)
    vote1 = Vote(user_id=test_user.id, recipe_id=multiple_recipes[0].id, vote_value=1)
    vote2 = Vote(user_id=test_second_user.id, recipe_id=multiple_recipes[0].id, vote_value=1)
    
    # Recipe 2: 1 upvote (score: 1)
    vote3 = Vote(user_id=test_user.id, recipe_id=multiple_recipes[1].id, vote_value=1)
    
    # Recipe 3: 1 downvote (score: -1)  
    vote4 = Vote(user_id=test_second_user.id, recipe_id=multiple_recipes[2].id, vote_value=-1)
    
    db_session.add_all([vote1, vote2, vote3, vote4])
    
    # Update vote counts
    multiple_recipes[0].upvotes = 2
    multiple_recipes[0].downvotes = 0
    multiple_recipes[0].vote_score = 2
    
    multiple_recipes[1].upvotes = 1
    multiple_recipes[1].downvotes = 0
    multiple_recipes[1].vote_score = 1
    
    multiple_recipes[2].upvotes = 0
    multiple_recipes[2].downvotes = 1
    multiple_recipes[2].vote_score = -1
    
    await db_session.commit()
    
    return multiple_recipes


# Performance test fixtures
@pytest.fixture
async def large_dataset(
    db_session: AsyncSession,
    test_user: User,
    test_tags: list[Tag]
) -> None:
    """
    Create a large dataset for performance testing.
    """
    recipes = []
    for i in range(50):  # Create 50 recipes
        recipe = Recipe(
            title=f"Recipe {i}",
            description=f"Description for recipe {i}",
            ingredients=[
                {"name": f"ingredient_{i}_1", "amount": "1 cup", "unit": "cup"},
                {"name": f"ingredient_{i}_2", "amount": "2 tbsp", "unit": "tbsp"}
            ],
            instructions=f"Instructions for recipe {i}",
            prep_time_minutes=10 + (i % 20),
            cook_time_minutes=20 + (i % 30),
            servings=2 + (i % 6),
            is_public=True,
            author_id=test_user.id
        )
        # Assign random tags
        recipe.tags = test_tags[(i % 3):(i % 3) + 2]
        recipes.append(recipe)
    
    db_session.add_all(recipes)
    await db_session.commit()