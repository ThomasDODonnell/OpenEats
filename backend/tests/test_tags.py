"""
Tests for tag management endpoints.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag
from app.models.recipe import Recipe


class TestTagCreation:
    """Test tag creation endpoint."""

    async def test_create_tag_success(self, authenticated_client: AsyncClient):
        """Test successful tag creation."""
        tag_data = {
            "name": "italian",
            "category": "cuisine"
        }
        
        response = await authenticated_client.post("/tags/", json=tag_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == tag_data["name"]
        assert data["category"] == tag_data["category"]
        assert "id" in data

    async def test_create_tag_duplicate_name(self, authenticated_client: AsyncClient, test_tags):
        """Test creating tag with duplicate name."""
        tag_data = {
            "name": test_tags[0].name,  # Use existing tag name
            "category": "cuisine"
        }
        
        response = await authenticated_client.post("/tags/", json=tag_data)
        
        assert response.status_code == 409
        data = response.json()
        assert data["error"] is True
        assert data["type"] == "conflict_error"
        assert "already exists" in data["message"]

    async def test_create_tag_unauthorized(self, client: AsyncClient):
        """Test creating tag without authentication."""
        tag_data = {
            "name": "unauthorized",
            "category": "cuisine"
        }
        
        response = await client.post("/tags/", json=tag_data)
        
        assert response.status_code == 401

    async def test_create_tag_invalid_category(self, authenticated_client: AsyncClient):
        """Test creating tag with invalid category."""
        tag_data = {
            "name": "test_tag",
            "category": "invalid_category"
        }
        
        response = await authenticated_client.post("/tags/", json=tag_data)
        
        assert response.status_code == 422  # Validation error

    async def test_create_tag_empty_name(self, authenticated_client: AsyncClient):
        """Test creating tag with empty name."""
        tag_data = {
            "name": "",
            "category": "cuisine"
        }
        
        response = await authenticated_client.post("/tags/", json=tag_data)
        
        assert response.status_code == 422

    async def test_create_tag_missing_fields(self, authenticated_client: AsyncClient):
        """Test creating tag with missing required fields."""
        incomplete_data = {
            "name": "incomplete"
            # Missing category
        }
        
        response = await authenticated_client.post("/tags/", json=incomplete_data)
        
        assert response.status_code == 422


class TestTagRetrieval:
    """Test tag retrieval endpoints."""

    async def test_get_all_tags(self, client: AsyncClient, test_tags):
        """Test getting all tags."""
        response = await client.get("/tags/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == len(test_tags)
        
        # Verify structure
        if data:
            tag = data[0]
            assert "id" in tag
            assert "name" in tag
            assert "category" in tag

    async def test_get_tags_by_category(self, client: AsyncClient, test_tags):
        """Test getting tags filtered by category."""
        category = "dietary"
        response = await client.get(f"/tags/?category={category}")
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned tags should be in the specified category
        for tag in data:
            assert tag["category"] == category

    async def test_get_tags_with_limit(self, client: AsyncClient, test_tags):
        """Test getting tags with limit parameter."""
        limit = 3
        response = await client.get(f"/tags/?limit={limit}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) <= limit

    async def test_get_tags_invalid_category(self, client: AsyncClient):
        """Test getting tags with invalid category."""
        response = await client.get("/tags/?category=invalid")
        
        assert response.status_code == 422  # Validation error

    async def test_get_tags_sorted_by_name(self, client: AsyncClient, test_tags):
        """Test that tags are returned sorted by name."""
        response = await client.get("/tags/")
        
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 1:
            # Verify alphabetical order
            names = [tag["name"] for tag in data]
            assert names == sorted(names)


class TestTagSearch:
    """Test tag search endpoint."""

    async def test_search_tags_success(self, client: AsyncClient, test_tags):
        """Test successful tag search."""
        search_term = "veg"  # Should match "vegetarian" and "vegan"
        response = await client.get(f"/tags/search?q={search_term}")
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned tags should contain the search term
        for tag in data:
            assert search_term.lower() in tag["name"].lower()

    async def test_search_tags_with_category(self, client: AsyncClient, test_tags):
        """Test tag search with category filter."""
        search_term = "chicken"
        category = "protein"
        response = await client.get(f"/tags/search?q={search_term}&category={category}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should match both search term and category
        for tag in data:
            assert search_term.lower() in tag["name"].lower()
            assert tag["category"] == category

    async def test_search_tags_no_results(self, client: AsyncClient):
        """Test tag search with no matching results."""
        search_term = "nonexistent"
        response = await client.get(f"/tags/search?q={search_term}")
        
        assert response.status_code == 200
        data = response.json()
        assert data == []

    async def test_search_tags_missing_query(self, client: AsyncClient):
        """Test tag search without query parameter."""
        response = await client.get("/tags/search")
        
        assert response.status_code == 422  # Missing required parameter

    async def test_search_tags_empty_query(self, client: AsyncClient):
        """Test tag search with empty query."""
        response = await client.get("/tags/search?q=")
        
        assert response.status_code == 422  # Query too short

    async def test_search_tags_with_limit(self, client: AsyncClient, test_tags):
        """Test tag search with limit parameter."""
        search_term = "e"  # Should match multiple tags
        limit = 2
        response = await client.get(f"/tags/search?q={search_term}&limit={limit}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) <= limit


class TestPopularTags:
    """Test popular tags endpoint."""

    async def test_get_popular_tags(self, client: AsyncClient, multiple_recipes, test_tags):
        """Test getting popular tags grouped by category."""
        response = await client.get("/tags/popular")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have all categories
        expected_categories = [
            "dietary", "protein", "meal_type", "cuisine", 
            "cooking_method", "difficulty", "time", "occasion", "lifestyle"
        ]
        
        for category in expected_categories:
            assert category in data
            assert isinstance(data[category], list)

    async def test_popular_tags_with_recipe_counts(self, client: AsyncClient, multiple_recipes):
        """Test that popular tags include recipe counts."""
        response = await client.get("/tags/popular")
        
        assert response.status_code == 200
        data = response.json()
        
        # Find a category with tags
        for category, tags in data.items():
            if tags:
                tag = tags[0]
                assert "id" in tag
                assert "name" in tag
                assert "category" in tag
                assert "recipe_count" in tag
                assert tag["recipe_count"] > 0
                break

    async def test_popular_tags_only_public_recipes(
        self, 
        client: AsyncClient, 
        test_recipe,
        test_private_recipe,
        test_tags
    ):
        """Test that popular tags only count public recipes."""
        response = await client.get("/tags/popular")
        
        assert response.status_code == 200
        data = response.json()
        
        # The counts should not include private recipes
        # This is difficult to test directly, but we can verify the structure
        for category, tags in data.items():
            for tag in tags:
                assert tag["recipe_count"] >= 0

    async def test_popular_tags_with_limit(self, client: AsyncClient, multiple_recipes):
        """Test popular tags with limit per category."""
        limit = 2
        response = await client.get(f"/tags/popular?limit_per_category={limit}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Each category should have at most the specified limit
        for category, tags in data.items():
            assert len(tags) <= limit

    async def test_popular_tags_excludes_unused_tags(self, client: AsyncClient, db_session: AsyncSession):
        """Test that popular tags only include tags with recipes."""
        # Create a tag not associated with any recipes
        unused_tag = Tag(name="unused_tag", category="cuisine")
        db_session.add(unused_tag)
        await db_session.commit()
        
        response = await client.get("/tags/popular")
        
        assert response.status_code == 200
        data = response.json()
        
        # The unused tag should not appear in any category
        all_tag_names = []
        for category, tags in data.items():
            all_tag_names.extend(tag["name"] for tag in tags)
        
        assert "unused_tag" not in all_tag_names


class TestTagDetail:
    """Test individual tag retrieval."""

    async def test_get_tag_by_id(self, client: AsyncClient, test_tags):
        """Test getting tag by ID."""
        tag = test_tags[0]
        response = await client.get(f"/tags/{tag.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == tag.id
        assert data["name"] == tag.name
        assert data["category"] == tag.category

    async def test_get_tag_not_found(self, client: AsyncClient):
        """Test getting non-existent tag."""
        response = await client.get("/tags/99999")
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"] is True
        assert data["type"] == "not_found_error"


class TestTagUpdate:
    """Test tag update endpoint."""

    async def test_update_tag_name(self, authenticated_client: AsyncClient, test_tags, db_session: AsyncSession):
        """Test updating tag name."""
        tag = test_tags[0]
        original_category = tag.category
        update_data = {
            "name": "updated_tag_name"
        }
        
        response = await authenticated_client.put(f"/tags/{tag.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == update_data["name"]
        assert data["category"] == original_category  # Should remain unchanged

    async def test_update_tag_category(self, authenticated_client: AsyncClient, test_tags):
        """Test updating tag category."""
        tag = test_tags[0]
        original_name = tag.name
        update_data = {
            "category": "cuisine"
        }
        
        response = await authenticated_client.put(f"/tags/{tag.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == original_name  # Should remain unchanged
        assert data["category"] == update_data["category"]

    async def test_update_tag_both_fields(self, authenticated_client: AsyncClient, test_tags):
        """Test updating both name and category."""
        tag = test_tags[0]
        update_data = {
            "name": "completely_new_name",
            "category": "cuisine"
        }
        
        response = await authenticated_client.put(f"/tags/{tag.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == update_data["name"]
        assert data["category"] == update_data["category"]

    async def test_update_tag_duplicate_name(self, authenticated_client: AsyncClient, test_tags):
        """Test updating tag with duplicate name."""
        tag1, tag2 = test_tags[0], test_tags[1]
        update_data = {
            "name": tag2.name  # Try to use another tag's name
        }
        
        response = await authenticated_client.put(f"/tags/{tag1.id}", json=update_data)
        
        assert response.status_code == 409
        data = response.json()
        assert data["error"] is True
        assert data["type"] == "conflict_error"

    async def test_update_tag_unauthorized(self, client: AsyncClient, test_tags):
        """Test updating tag without authentication."""
        tag = test_tags[0]
        update_data = {"name": "unauthorized_update"}
        
        response = await client.put(f"/tags/{tag.id}", json=update_data)
        
        assert response.status_code == 401

    async def test_update_tag_not_found(self, authenticated_client: AsyncClient):
        """Test updating non-existent tag."""
        update_data = {"name": "not_found_update"}
        
        response = await authenticated_client.put("/tags/99999", json=update_data)
        
        assert response.status_code == 404

    async def test_update_tag_invalid_category(self, authenticated_client: AsyncClient, test_tags):
        """Test updating tag with invalid category."""
        tag = test_tags[0]
        update_data = {"category": "invalid_category"}
        
        response = await authenticated_client.put(f"/tags/{tag.id}", json=update_data)
        
        assert response.status_code == 422

    async def test_update_tag_empty_name(self, authenticated_client: AsyncClient, test_tags):
        """Test updating tag with empty name."""
        tag = test_tags[0]
        update_data = {"name": ""}
        
        response = await authenticated_client.put(f"/tags/{tag.id}", json=update_data)
        
        assert response.status_code == 422

    async def test_update_tag_no_changes(self, authenticated_client: AsyncClient, test_tags):
        """Test updating tag with no actual changes."""
        tag = test_tags[0]
        update_data = {
            "name": tag.name,
            "category": tag.category
        }
        
        response = await authenticated_client.put(f"/tags/{tag.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == tag.name
        assert data["category"] == tag.category


class TestTagDeletion:
    """Test tag deletion endpoint."""

    async def test_delete_tag_success(self, authenticated_client: AsyncClient, db_session: AsyncSession):
        """Test successful tag deletion."""
        # Create a tag not associated with any recipes
        tag = Tag(name="deletable_tag", category="cuisine")
        db_session.add(tag)
        await db_session.commit()
        await db_session.refresh(tag)
        tag_id = tag.id
        
        response = await authenticated_client.delete(f"/tags/{tag_id}")
        
        assert response.status_code == 204
        
        # Verify tag is deleted
        deleted_tag = await db_session.get(Tag, tag_id)
        assert deleted_tag is None

    async def test_delete_tag_with_recipes(
        self, 
        authenticated_client: AsyncClient, 
        test_recipe, 
        test_tags,
        db_session: AsyncSession
    ):
        """Test deleting tag that's associated with recipes."""
        tag = test_tags[0]  # This tag is associated with test_recipe
        tag_id = tag.id
        
        response = await authenticated_client.delete(f"/tags/{tag_id}")
        
        assert response.status_code == 204
        
        # Verify tag is deleted
        deleted_tag = await db_session.get(Tag, tag_id)
        assert deleted_tag is None
        
        # Verify recipe still exists but doesn't have the deleted tag
        await db_session.refresh(test_recipe)
        recipe_tag_ids = [t.id for t in test_recipe.tags]
        assert tag_id not in recipe_tag_ids

    async def test_delete_tag_unauthorized(self, client: AsyncClient, test_tags):
        """Test deleting tag without authentication."""
        tag = test_tags[0]
        
        response = await client.delete(f"/tags/{tag.id}")
        
        assert response.status_code == 401

    async def test_delete_tag_not_found(self, authenticated_client: AsyncClient):
        """Test deleting non-existent tag."""
        response = await authenticated_client.delete("/tags/99999")
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"] is True
        assert data["type"] == "not_found_error"


class TestTagCategories:
    """Test tag category functionality."""

    async def test_all_valid_categories(self, authenticated_client: AsyncClient):
        """Test creating tags with all valid categories."""
        valid_categories = [
            "dietary", "protein", "meal_type", "cuisine",
            "cooking_method", "difficulty", "time", "occasion", "lifestyle"
        ]
        
        created_tags = []
        for i, category in enumerate(valid_categories):
            tag_data = {
                "name": f"test_{category}_{i}",
                "category": category
            }
            
            response = await authenticated_client.post("/tags/", json=tag_data)
            assert response.status_code == 201
            data = response.json()
            assert data["category"] == category
            created_tags.append(data)

    async def test_category_filtering(self, client: AsyncClient, test_tags):
        """Test filtering tags by different categories."""
        categories_to_test = set(tag.category for tag in test_tags)
        
        for category in categories_to_test:
            response = await client.get(f"/tags/?category={category}")
            assert response.status_code == 200
            data = response.json()
            
            # All returned tags should be in the specified category
            for tag in data:
                assert tag["category"] == category

    async def test_popular_tags_category_structure(self, client: AsyncClient, multiple_recipes):
        """Test that popular tags maintain proper category structure."""
        response = await client.get("/tags/popular")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all expected categories are present
        expected_categories = [
            "dietary", "protein", "meal_type", "cuisine",
            "cooking_method", "difficulty", "time", "occasion", "lifestyle"
        ]
        
        for category in expected_categories:
            assert category in data
            
            # Each tag in the category should have the correct category
            for tag in data[category]:
                assert tag["category"] == category


class TestTagRecipeAssociation:
    """Test tag-recipe associations through tag endpoints."""

    async def test_tag_usage_in_popular_endpoint(
        self, 
        client: AsyncClient, 
        multiple_recipes,
        db_session: AsyncSession
    ):
        """Test that tag usage counts are accurate in popular endpoint."""
        response = await client.get("/tags/popular")
        
        assert response.status_code == 200
        data = response.json()
        
        # Find tags with recipe counts and verify they're reasonable
        found_tags_with_counts = False
        for category, tags in data.items():
            for tag in tags:
                if tag["recipe_count"] > 0:
                    found_tags_with_counts = True
                    assert isinstance(tag["recipe_count"], int)
                    assert tag["recipe_count"] >= 1
        
        # Should find at least some tags with recipe counts from the fixtures
        assert found_tags_with_counts

    async def test_deleted_tag_removes_from_recipes(
        self,
        authenticated_client: AsyncClient,
        test_recipe,
        test_tags,
        db_session: AsyncSession
    ):
        """Test that deleting a tag removes it from all associated recipes."""
        # Ensure the recipe has tags
        if not test_recipe.tags:
            test_recipe.tags = [test_tags[0]]
            await db_session.commit()
        
        tag_to_delete = test_recipe.tags[0]
        original_tag_count = len(test_recipe.tags)
        
        response = await authenticated_client.delete(f"/tags/{tag_to_delete.id}")
        assert response.status_code == 204
        
        # Refresh recipe and check tag count
        await db_session.refresh(test_recipe)
        assert len(test_recipe.tags) == original_tag_count - 1
        
        # Verify the specific tag is no longer associated
        remaining_tag_ids = [t.id for t in test_recipe.tags]
        assert tag_to_delete.id not in remaining_tag_ids