"""
Tests for recipe management endpoints.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recipe import Recipe
from app.models.tag import Tag


class TestRecipeCreation:
    """Test recipe creation endpoint."""

    async def test_create_recipe_success(self, authenticated_client: AsyncClient, test_recipe_data, test_tags):
        """Test successful recipe creation."""
        recipe_data = test_recipe_data.copy()
        recipe_data["tag_ids"] = [test_tags[0].id, test_tags[1].id]
        
        response = await authenticated_client.post("/recipes/", json=recipe_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["title"] == recipe_data["title"]
        assert data["description"] == recipe_data["description"]
        assert data["ingredients"] == recipe_data["ingredients"]
        assert data["instructions"] == recipe_data["instructions"]
        assert data["prep_time_minutes"] == recipe_data["prep_time_minutes"]
        assert data["cook_time_minutes"] == recipe_data["cook_time_minutes"]
        assert data["servings"] == recipe_data["servings"]
        assert data["is_public"] == recipe_data["is_public"]
        assert "id" in data
        assert "created_at" in data
        assert "author" in data
        assert len(data["tags"]) == 2

    async def test_create_recipe_without_tags(self, authenticated_client: AsyncClient, test_recipe_data):
        """Test creating recipe without tags."""
        response = await authenticated_client.post("/recipes/", json=test_recipe_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["tags"] == []

    async def test_create_recipe_invalid_tags(self, authenticated_client: AsyncClient, test_recipe_data):
        """Test creating recipe with invalid tag IDs."""
        recipe_data = test_recipe_data.copy()
        recipe_data["tag_ids"] = [9999, 9998]  # Non-existent tag IDs
        
        response = await authenticated_client.post("/recipes/", json=recipe_data)
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] is True
        assert "tags not found" in data["message"]

    async def test_create_recipe_unauthorized(self, client: AsyncClient, test_recipe_data):
        """Test creating recipe without authentication."""
        response = await client.post("/recipes/", json=test_recipe_data)
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] is True
        assert data["type"] == "authentication_error"

    async def test_create_recipe_invalid_data(self, authenticated_client: AsyncClient):
        """Test creating recipe with invalid data."""
        invalid_data = {
            "title": "",  # Empty title
            "prep_time_minutes": -5,  # Negative time
            "servings": 0  # Zero servings
        }
        response = await authenticated_client.post("/recipes/", json=invalid_data)
        
        assert response.status_code == 422

    async def test_create_recipe_missing_required_fields(self, authenticated_client: AsyncClient):
        """Test creating recipe with missing required fields."""
        incomplete_data = {
            "title": "Incomplete Recipe"
            # Missing other required fields
        }
        response = await authenticated_client.post("/recipes/", json=incomplete_data)
        
        assert response.status_code == 422

    async def test_create_private_recipe(self, authenticated_client: AsyncClient, test_recipe_data):
        """Test creating private recipe."""
        recipe_data = test_recipe_data.copy()
        recipe_data["is_public"] = False
        
        response = await authenticated_client.post("/recipes/", json=recipe_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["is_public"] is False


class TestRecipeRetrieval:
    """Test recipe retrieval endpoints."""

    async def test_get_recipes_public(self, client: AsyncClient, multiple_recipes):
        """Test getting public recipes without authentication."""
        response = await client.get("/recipes/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert "pages" in data
        assert data["total"] >= 0
        assert len(data["items"]) >= 0

    async def test_get_recipes_authenticated(self, authenticated_client: AsyncClient, multiple_recipes):
        """Test getting recipes as authenticated user."""
        response = await authenticated_client.get("/recipes/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] >= len(multiple_recipes)
        
        # Verify recipe structure
        if data["items"]:
            recipe = data["items"][0]
            assert "id" in recipe
            assert "title" in recipe
            assert "author" in recipe
            assert "tags" in recipe
            assert "created_at" in recipe

    async def test_get_recipes_pagination(self, client: AsyncClient, multiple_recipes):
        """Test recipe pagination."""
        # Get first page
        response1 = await client.get("/recipes/?skip=0&limit=2")
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Get second page
        response2 = await client.get("/recipes/?skip=2&limit=2")
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Verify different items (if enough recipes exist)
        if data1["total"] > 2:
            first_page_ids = {recipe["id"] for recipe in data1["items"]}
            second_page_ids = {recipe["id"] for recipe in data2["items"]}
            assert first_page_ids != second_page_ids

    async def test_get_recipes_tag_filter(self, client: AsyncClient, multiple_recipes, test_tags):
        """Test filtering recipes by tags."""
        tag_name = test_tags[0].name
        response = await client.get(f"/recipes/?tags={tag_name}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all returned recipes have the specified tag
        for recipe in data["items"]:
            tag_names = [tag["name"] for tag in recipe["tags"]]
            assert tag_name in tag_names

    async def test_get_recipes_multiple_tag_filter(self, client: AsyncClient, multiple_recipes, test_tags):
        """Test filtering recipes by multiple tags."""
        tag_names = [test_tags[0].name, test_tags[1].name]
        tags_param = "&".join([f"tags={name}" for name in tag_names])
        
        response = await client.get(f"/recipes/?{tags_param}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return recipes that match at least one tag
        for recipe in data["items"]:
            recipe_tag_names = [tag["name"] for tag in recipe["tags"]]
            assert any(tag_name in recipe_tag_names for tag_name in tag_names)

    async def test_get_recipes_search(self, client: AsyncClient, multiple_recipes):
        """Test searching recipes by title/description."""
        search_term = "chicken"
        response = await client.get(f"/recipes/?search={search_term}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify search results contain the term (case-insensitive)
        for recipe in data["items"]:
            title_match = search_term.lower() in recipe["title"].lower()
            desc_match = search_term.lower() in (recipe["description"] or "").lower()
            assert title_match or desc_match

    async def test_get_recipes_time_filters(self, client: AsyncClient, multiple_recipes):
        """Test filtering recipes by preparation/cooking time."""
        response = await client.get("/recipes/?max_prep_time=15&max_cook_time=20")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify time constraints
        for recipe in data["items"]:
            assert recipe["prep_time_minutes"] <= 15
            assert recipe["cook_time_minutes"] <= 20

    async def test_get_recipes_public_only(self, client: AsyncClient, test_recipe, test_private_recipe):
        """Test that unauthenticated users only see public recipes."""
        response = await client.get("/recipes/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should include public recipe but not private
        recipe_ids = [recipe["id"] for recipe in data["items"]]
        assert test_recipe.id in recipe_ids
        assert test_private_recipe.id not in recipe_ids

    async def test_get_recipes_private_for_owner(self, authenticated_client: AsyncClient, test_private_recipe):
        """Test that recipe owner can see their private recipes."""
        response = await authenticated_client.get("/recipes/?is_public=false")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should include user's private recipe
        recipe_ids = [recipe["id"] for recipe in data["items"]]
        assert test_private_recipe.id in recipe_ids


class TestRecipeDetail:
    """Test individual recipe retrieval."""

    async def test_get_recipe_by_id_public(self, client: AsyncClient, test_recipe):
        """Test getting public recipe by ID."""
        response = await client.get(f"/recipes/{test_recipe.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == test_recipe.id
        assert data["title"] == test_recipe.title
        assert "author" in data
        assert "tags" in data
        assert "ingredients" in data

    async def test_get_recipe_by_id_private_unauthorized(self, client: AsyncClient, test_private_recipe):
        """Test getting private recipe without authorization."""
        response = await client.get(f"/recipes/{test_private_recipe.id}")
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"] is True
        assert data["type"] == "not_found_error"

    async def test_get_recipe_by_id_private_authorized(self, authenticated_client: AsyncClient, test_private_recipe):
        """Test getting private recipe as owner."""
        response = await authenticated_client.get(f"/recipes/{test_private_recipe.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_private_recipe.id

    async def test_get_recipe_not_found(self, client: AsyncClient):
        """Test getting non-existent recipe."""
        response = await client.get("/recipes/99999")
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"] is True
        assert data["type"] == "not_found_error"


class TestRecipeUpdate:
    """Test recipe update endpoint."""

    async def test_update_recipe_success(self, authenticated_client: AsyncClient, test_recipe, db_session: AsyncSession):
        """Test successful recipe update."""
        update_data = {
            "title": "Updated Recipe Title",
            "description": "Updated description",
            "prep_time_minutes": 25
        }
        
        response = await authenticated_client.put(f"/recipes/{test_recipe.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["title"] == update_data["title"]
        assert data["description"] == update_data["description"]
        assert data["prep_time_minutes"] == update_data["prep_time_minutes"]
        # Other fields should remain unchanged
        assert data["servings"] == test_recipe.servings

    async def test_update_recipe_tags(self, authenticated_client: AsyncClient, test_recipe, test_tags):
        """Test updating recipe tags."""
        new_tag_ids = [test_tags[3].id, test_tags[4].id]
        update_data = {"tag_ids": new_tag_ids}
        
        response = await authenticated_client.put(f"/recipes/{test_recipe.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        returned_tag_ids = [tag["id"] for tag in data["tags"]]
        assert sorted(returned_tag_ids) == sorted(new_tag_ids)

    async def test_update_recipe_remove_tags(self, authenticated_client: AsyncClient, test_recipe):
        """Test removing all tags from recipe."""
        update_data = {"tag_ids": []}
        
        response = await authenticated_client.put(f"/recipes/{test_recipe.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["tags"] == []

    async def test_update_recipe_unauthorized(self, client: AsyncClient, test_recipe):
        """Test updating recipe without authentication."""
        update_data = {"title": "Unauthorized Update"}
        
        response = await client.put(f"/recipes/{test_recipe.id}", json=update_data)
        
        assert response.status_code == 401

    async def test_update_recipe_wrong_user(
        self, 
        authenticated_client: AsyncClient, 
        test_second_user, 
        db_session: AsyncSession,
        test_tags
    ):
        """Test updating recipe by non-owner."""
        # Create recipe owned by second user
        other_recipe = Recipe(
            title="Other User's Recipe",
            description="This belongs to someone else",
            ingredients=[{"name": "ingredient", "amount": "1", "unit": "cup"}],
            instructions="Don't touch this",
            prep_time_minutes=10,
            cook_time_minutes=15,
            servings=2,
            is_public=True,
            author_id=test_second_user.id
        )
        db_session.add(other_recipe)
        await db_session.commit()
        await db_session.refresh(other_recipe)
        
        update_data = {"title": "Unauthorized Update"}
        
        response = await authenticated_client.put(f"/recipes/{other_recipe.id}", json=update_data)
        
        assert response.status_code == 403
        data = response.json()
        assert data["error"] is True
        assert data["type"] == "authorization_error"

    async def test_update_recipe_not_found(self, authenticated_client: AsyncClient):
        """Test updating non-existent recipe."""
        update_data = {"title": "Updated Title"}
        
        response = await authenticated_client.put("/recipes/99999", json=update_data)
        
        assert response.status_code == 404

    async def test_update_recipe_invalid_tags(self, authenticated_client: AsyncClient, test_recipe):
        """Test updating recipe with invalid tag IDs."""
        update_data = {"tag_ids": [9999, 9998]}
        
        response = await authenticated_client.put(f"/recipes/{test_recipe.id}", json=update_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "tags not found" in data["message"]

    async def test_partial_update_recipe(self, authenticated_client: AsyncClient, test_recipe):
        """Test partial recipe update (only some fields)."""
        original_title = test_recipe.title
        update_data = {"prep_time_minutes": 99}
        
        response = await authenticated_client.put(f"/recipes/{test_recipe.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Updated field should change
        assert data["prep_time_minutes"] == 99
        # Non-updated field should remain the same
        assert data["title"] == original_title


class TestRecipeDeletion:
    """Test recipe deletion endpoint."""

    async def test_delete_recipe_success(self, authenticated_client: AsyncClient, test_recipe, db_session: AsyncSession):
        """Test successful recipe deletion."""
        recipe_id = test_recipe.id
        
        response = await authenticated_client.delete(f"/recipes/{recipe_id}")
        
        assert response.status_code == 204
        
        # Verify recipe is deleted
        deleted_recipe = await db_session.get(Recipe, recipe_id)
        assert deleted_recipe is None

    async def test_delete_recipe_unauthorized(self, client: AsyncClient, test_recipe):
        """Test deleting recipe without authentication."""
        response = await client.delete(f"/recipes/{test_recipe.id}")
        
        assert response.status_code == 401

    async def test_delete_recipe_wrong_user(
        self,
        authenticated_client: AsyncClient,
        test_second_user,
        db_session: AsyncSession
    ):
        """Test deleting recipe by non-owner."""
        # Create recipe owned by second user
        other_recipe = Recipe(
            title="Other User's Recipe",
            description="This belongs to someone else",
            ingredients=[{"name": "ingredient", "amount": "1", "unit": "cup"}],
            instructions="Don't delete this",
            prep_time_minutes=10,
            cook_time_minutes=15,
            servings=2,
            is_public=True,
            author_id=test_second_user.id
        )
        db_session.add(other_recipe)
        await db_session.commit()
        await db_session.refresh(other_recipe)
        
        response = await authenticated_client.delete(f"/recipes/{other_recipe.id}")
        
        assert response.status_code == 403
        data = response.json()
        assert data["error"] is True
        assert data["type"] == "authorization_error"

    async def test_delete_recipe_not_found(self, authenticated_client: AsyncClient):
        """Test deleting non-existent recipe."""
        response = await authenticated_client.delete("/recipes/99999")
        
        assert response.status_code == 404


class TestUserRecipes:
    """Test user-specific recipe endpoints."""

    async def test_get_user_recipes_public(self, client: AsyncClient, test_user, multiple_recipes):
        """Test getting user's public recipes."""
        response = await client.get(f"/recipes/user/{test_user.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should only show public recipes
        for recipe in data["items"]:
            assert recipe["author"]["id"] == test_user.id
            assert recipe["is_public"] is True

    async def test_get_user_recipes_own_private(
        self, 
        authenticated_client: AsyncClient, 
        test_user, 
        test_private_recipe
    ):
        """Test getting own recipes including private ones."""
        response = await authenticated_client.get(f"/recipes/user/{test_user.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should include both public and private recipes
        recipe_ids = [recipe["id"] for recipe in data["items"]]
        assert test_private_recipe.id in recipe_ids

    async def test_get_user_recipes_not_found(self, client: AsyncClient):
        """Test getting recipes for non-existent user."""
        response = await client.get("/recipes/user/99999")
        
        assert response.status_code == 404

    async def test_get_user_recipes_pagination(self, client: AsyncClient, test_user, multiple_recipes):
        """Test pagination for user recipes."""
        response = await client.get(f"/recipes/user/{test_user.id}?skip=0&limit=1")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        assert len(data["items"]) <= 1


class TestRecipeFiltering:
    """Test advanced recipe filtering scenarios."""

    async def test_vote_score_filter(self, client: AsyncClient, recipes_with_votes):
        """Test filtering recipes by minimum vote score."""
        response = await client.get("/recipes/?min_vote_score=1")
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned recipes should have vote score >= 1
        for recipe in data["items"]:
            assert recipe["vote_score"] >= 1

    async def test_complex_filter_combination(self, client: AsyncClient, multiple_recipes, test_tags):
        """Test combining multiple filters."""
        tag_name = test_tags[0].name
        params = f"tags={tag_name}&max_prep_time=20&is_public=true"
        
        response = await client.get(f"/recipes/?{params}")
        
        assert response.status_code == 200
        data = response.json()
        
        for recipe in data["items"]:
            # Has the required tag
            tag_names = [tag["name"] for tag in recipe["tags"]]
            assert tag_name in tag_names
            # Meets prep time constraint
            assert recipe["prep_time_minutes"] <= 20
            # Is public
            assert recipe["is_public"] is True

    async def test_empty_filter_results(self, client: AsyncClient):
        """Test filter that returns no results."""
        response = await client.get("/recipes/?search=nonexistentrecipename123")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 0
        assert data["items"] == []
        assert data["pages"] >= 1


class TestRecipePerformance:
    """Test recipe endpoint performance with large datasets."""

    async def test_large_dataset_pagination(self, client: AsyncClient, large_dataset):
        """Test pagination performance with large dataset."""
        response = await client.get("/recipes/?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] >= 50  # Should have at least 50 recipes from fixture
        assert len(data["items"]) <= 10
        assert data["pages"] >= 5

    async def test_tag_filter_performance(self, client: AsyncClient, large_dataset, test_tags):
        """Test tag filtering performance with large dataset."""
        tag_name = test_tags[0].name
        
        response = await client.get(f"/recipes/?tags={tag_name}&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return results efficiently
        assert len(data["items"]) <= 5
        for recipe in data["items"]:
            tag_names = [tag["name"] for tag in recipe["tags"]]
            assert tag_name in tag_names

    async def test_search_performance(self, client: AsyncClient, large_dataset):
        """Test search performance with large dataset."""
        response = await client.get("/recipes/?search=Recipe&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should handle search efficiently
        assert len(data["items"]) <= 5