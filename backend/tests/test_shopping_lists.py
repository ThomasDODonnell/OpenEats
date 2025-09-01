"""
Tests for shopping list endpoints.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shopping_list import ShoppingList
from app.models.recipe import Recipe


class TestShoppingListCreation:
    """Test shopping list creation endpoint."""

    async def test_create_shopping_list_success(
        self, 
        authenticated_client: AsyncClient, 
        multiple_recipes,
        db_session: AsyncSession
    ):
        """Test successful shopping list creation."""
        recipe_ids = [recipe.id for recipe in multiple_recipes[:2]]
        shopping_list_data = {
            "name": "Weekly Groceries",
            "description": "Shopping list for this week",
            "recipe_ids": recipe_ids
        }
        
        response = await authenticated_client.post("/shopping-lists/", json=shopping_list_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == shopping_list_data["name"]
        assert data["description"] == shopping_list_data["description"]
        assert data["recipe_ids"] == recipe_ids
        assert "id" in data
        assert "ingredients" in data
        assert len(data["ingredients"]) > 0  # Should have aggregated ingredients
        assert "created_at" in data

    async def test_create_shopping_list_single_recipe(
        self, 
        authenticated_client: AsyncClient, 
        test_recipe
    ):
        """Test creating shopping list from single recipe."""
        shopping_list_data = {
            "name": "Single Recipe List",
            "recipe_ids": [test_recipe.id]
        }
        
        response = await authenticated_client.post("/shopping-lists/", json=shopping_list_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["recipe_ids"] == [test_recipe.id]
        assert len(data["ingredients"]) > 0

    async def test_create_shopping_list_nonexistent_recipe(self, authenticated_client: AsyncClient):
        """Test creating shopping list with non-existent recipe."""
        shopping_list_data = {
            "name": "Invalid List",
            "recipe_ids": [99999]
        }
        
        response = await authenticated_client.post("/shopping-lists/", json=shopping_list_data)
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"] is True
        assert "Recipes not found" in data["message"]

    async def test_create_shopping_list_empty_recipes(self, authenticated_client: AsyncClient):
        """Test creating shopping list with empty recipe list."""
        shopping_list_data = {
            "name": "Empty List",
            "recipe_ids": []
        }
        
        response = await authenticated_client.post("/shopping-lists/", json=shopping_list_data)
        
        assert response.status_code == 422  # Validation error

    async def test_create_shopping_list_unauthorized(self, client: AsyncClient, test_recipe):
        """Test creating shopping list without authentication."""
        shopping_list_data = {
            "name": "Unauthorized List",
            "recipe_ids": [test_recipe.id]
        }
        
        response = await client.post("/shopping-lists/", json=shopping_list_data)
        
        assert response.status_code == 401

    async def test_create_shopping_list_missing_name(self, authenticated_client: AsyncClient, test_recipe):
        """Test creating shopping list without name."""
        shopping_list_data = {
            "recipe_ids": [test_recipe.id]
            # Missing name
        }
        
        response = await authenticated_client.post("/shopping-lists/", json=shopping_list_data)
        
        assert response.status_code == 422

    async def test_create_shopping_list_includes_private_recipe(
        self, 
        authenticated_client: AsyncClient, 
        test_private_recipe
    ):
        """Test creating shopping list includes user's private recipes."""
        shopping_list_data = {
            "name": "Private Recipe List",
            "recipe_ids": [test_private_recipe.id]
        }
        
        response = await authenticated_client.post("/shopping-lists/", json=shopping_list_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["recipe_ids"] == [test_private_recipe.id]

    async def test_create_shopping_list_ingredient_aggregation(
        self, 
        authenticated_client: AsyncClient, 
        db_session: AsyncSession,
        test_user
    ):
        """Test that ingredients are properly aggregated from multiple recipes."""
        # Create recipes with overlapping ingredients
        recipe1 = Recipe(
            title="Recipe 1",
            description="Test recipe 1",
            ingredients=[
                {"name": "flour", "amount": "2 cups", "unit": "cup"},
                {"name": "salt", "amount": "1 tsp", "unit": "tsp"}
            ],
            instructions="Mix and bake",
            prep_time_minutes=10,
            cook_time_minutes=20,
            servings=4,
            is_public=True,
            author_id=test_user.id
        )
        
        recipe2 = Recipe(
            title="Recipe 2",
            description="Test recipe 2",
            ingredients=[
                {"name": "flour", "amount": "1 cup", "unit": "cup"},  # Same ingredient
                {"name": "sugar", "amount": "1 cup", "unit": "cup"}
            ],
            instructions="Mix and bake",
            prep_time_minutes=15,
            cook_time_minutes=25,
            servings=6,
            is_public=True,
            author_id=test_user.id
        )
        
        db_session.add_all([recipe1, recipe2])
        await db_session.commit()
        await db_session.refresh(recipe1)
        await db_session.refresh(recipe2)
        
        shopping_list_data = {
            "name": "Aggregated List",
            "recipe_ids": [recipe1.id, recipe2.id]
        }
        
        response = await authenticated_client.post("/shopping-lists/", json=shopping_list_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have aggregated flour (2 cups + 1 cup = 3 cups)
        ingredient_names = [ing["name"] for ing in data["ingredients"]]
        assert "flour" in ingredient_names
        assert "salt" in ingredient_names
        assert "sugar" in ingredient_names
        
        # Find flour ingredient and check aggregation
        flour_ingredient = next(ing for ing in data["ingredients"] if ing["name"] == "flour")
        assert "3" in flour_ingredient["total_amount"]  # Should be aggregated


class TestShoppingListGeneration:
    """Test shopping list generation/preview endpoint."""

    async def test_generate_shopping_list_preview(
        self, 
        authenticated_client: AsyncClient, 
        multiple_recipes
    ):
        """Test generating shopping list preview without saving."""
        recipe_ids = [recipe.id for recipe in multiple_recipes[:2]]
        request_data = {
            "recipe_ids": recipe_ids,
            "list_name": "Preview List",
            "merge_similar_ingredients": True
        }
        
        response = await authenticated_client.post("/shopping-lists/generate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == 0  # Preview ID
        assert data["name"] == "Preview List"
        assert data["recipe_ids"] == recipe_ids
        assert "ingredients" in data
        assert "ingredient_groups" in data  # Should have grouping
        assert data["created_at"] is None  # Preview doesn't have timestamps
        
        # Should have ingredient groups by category
        assert len(data["ingredient_groups"]) > 0
        for group in data["ingredient_groups"]:
            assert "category" in group
            assert "ingredients" in group

    async def test_generate_shopping_list_no_merge(
        self, 
        authenticated_client: AsyncClient, 
        multiple_recipes
    ):
        """Test generating shopping list without ingredient merging."""
        recipe_ids = [recipe.id for recipe in multiple_recipes[:1]]
        request_data = {
            "recipe_ids": recipe_ids,
            "merge_similar_ingredients": False
        }
        
        response = await authenticated_client.post("/shopping-lists/generate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should still work but ingredients won't be merged
        assert len(data["ingredients"]) > 0
        assert len(data["ingredient_groups"]) > 0

    async def test_generate_shopping_list_auto_name(
        self, 
        authenticated_client: AsyncClient, 
        multiple_recipes
    ):
        """Test auto-generated shopping list name."""
        recipe_ids = [recipe.id for recipe in multiple_recipes[:2]]
        request_data = {
            "recipe_ids": recipe_ids,
            "merge_similar_ingredients": True
            # No list_name provided
        }
        
        response = await authenticated_client.post("/shopping-lists/generate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have auto-generated name
        assert "Shopping List" in data["name"]
        assert len(data["name"]) > len("Shopping List")

    async def test_generate_shopping_list_nonexistent_recipe(
        self, 
        authenticated_client: AsyncClient
    ):
        """Test generating shopping list with non-existent recipe."""
        request_data = {
            "recipe_ids": [99999],
            "merge_similar_ingredients": True
        }
        
        response = await authenticated_client.post("/shopping-lists/generate", json=request_data)
        
        assert response.status_code == 404
        data = response.json()
        assert "Recipes not found" in data["message"]

    async def test_generate_shopping_list_unauthorized(self, client: AsyncClient, test_recipe):
        """Test generating shopping list without authentication."""
        request_data = {
            "recipe_ids": [test_recipe.id],
            "merge_similar_ingredients": True
        }
        
        response = await client.post("/shopping-lists/generate", json=request_data)
        
        assert response.status_code == 401


class TestShoppingListRetrieval:
    """Test shopping list retrieval endpoints."""

    async def test_get_user_shopping_lists(
        self, 
        authenticated_client: AsyncClient, 
        test_shopping_list
    ):
        """Test getting user's shopping lists."""
        response = await authenticated_client.get("/shopping-lists/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 1  # Should include test_shopping_list
        
        # Find our test shopping list
        found_list = next((sl for sl in data if sl["id"] == test_shopping_list.id), None)
        assert found_list is not None
        assert found_list["name"] == test_shopping_list.name
        assert "recipe_count" in found_list
        assert "ingredient_count" in found_list
        assert "created_at" in found_list

    async def test_get_user_shopping_lists_pagination(
        self, 
        authenticated_client: AsyncClient, 
        test_shopping_list
    ):
        """Test shopping list pagination."""
        response = await authenticated_client.get("/shopping-lists/?skip=0&limit=1")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) <= 1

    async def test_get_user_shopping_lists_empty(self, authenticated_client: AsyncClient):
        """Test getting shopping lists when user has none."""
        # This user has no shopping lists yet
        response = await authenticated_client.get("/shopping-lists/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return empty list, not error
        assert isinstance(data, list)

    async def test_get_user_shopping_lists_unauthorized(self, client: AsyncClient):
        """Test getting shopping lists without authentication."""
        response = await client.get("/shopping-lists/")
        
        assert response.status_code == 401

    async def test_get_shopping_lists_only_own(
        self, 
        authenticated_client: AsyncClient, 
        test_second_user,
        db_session: AsyncSession
    ):
        """Test that users only see their own shopping lists."""
        # Create shopping list for second user
        other_shopping_list = ShoppingList(
            name="Other User's List",
            user_id=test_second_user.id,
            recipe_ids=[],
            ingredients=[]
        )
        db_session.add(other_shopping_list)
        await db_session.commit()
        
        response = await authenticated_client.get("/shopping-lists/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should not include other user's shopping list
        list_names = [sl["name"] for sl in data]
        assert "Other User's List" not in list_names


class TestShoppingListDetail:
    """Test individual shopping list retrieval."""

    async def test_get_shopping_list_by_id(
        self, 
        authenticated_client: AsyncClient, 
        test_shopping_list
    ):
        """Test getting shopping list by ID with grouping."""
        response = await authenticated_client.get(f"/shopping-lists/{test_shopping_list.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == test_shopping_list.id
        assert data["name"] == test_shopping_list.name
        assert data["description"] == test_shopping_list.description
        assert data["recipe_ids"] == test_shopping_list.recipe_ids
        assert "ingredients" in data
        assert "ingredient_groups" in data  # Should have category grouping
        assert "created_at" in data
        assert "updated_at" in data

    async def test_get_shopping_list_with_ingredient_groups(
        self, 
        authenticated_client: AsyncClient, 
        test_shopping_list
    ):
        """Test that shopping list includes ingredient category grouping."""
        response = await authenticated_client.get(f"/shopping-lists/{test_shopping_list.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have ingredient groups
        assert "ingredient_groups" in data
        assert len(data["ingredient_groups"]) >= 0  # Might be empty if no ingredients
        
        # Each group should have category and ingredients
        for group in data["ingredient_groups"]:
            assert "category" in group
            assert "ingredients" in group
            assert isinstance(group["ingredients"], list)

    async def test_get_shopping_list_not_found(self, authenticated_client: AsyncClient):
        """Test getting non-existent shopping list."""
        response = await authenticated_client.get("/shopping-lists/99999")
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"] is True
        assert "Shopping list not found" in data["message"]

    async def test_get_shopping_list_wrong_user(
        self, 
        authenticated_client: AsyncClient, 
        test_second_user,
        db_session: AsyncSession
    ):
        """Test getting shopping list owned by different user."""
        # Create shopping list for second user
        other_shopping_list = ShoppingList(
            name="Other User's List",
            user_id=test_second_user.id,
            recipe_ids=[],
            ingredients=[]
        )
        db_session.add(other_shopping_list)
        await db_session.commit()
        await db_session.refresh(other_shopping_list)
        
        response = await authenticated_client.get(f"/shopping-lists/{other_shopping_list.id}")
        
        assert response.status_code == 403
        data = response.json()
        assert data["error"] is True
        assert data["type"] == "authorization_error"

    async def test_get_shopping_list_unauthorized(self, client: AsyncClient, test_shopping_list):
        """Test getting shopping list without authentication."""
        response = await client.get(f"/shopping-lists/{test_shopping_list.id}")
        
        assert response.status_code == 401


class TestShoppingListUpdate:
    """Test shopping list update endpoint."""

    async def test_update_shopping_list_name(
        self, 
        authenticated_client: AsyncClient, 
        test_shopping_list
    ):
        """Test updating shopping list name."""
        update_data = {
            "name": "Updated Shopping List Name"
        }
        
        response = await authenticated_client.put(
            f"/shopping-lists/{test_shopping_list.id}", 
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == update_data["name"]
        assert data["description"] == test_shopping_list.description  # Unchanged

    async def test_update_shopping_list_description(
        self, 
        authenticated_client: AsyncClient, 
        test_shopping_list
    ):
        """Test updating shopping list description."""
        update_data = {
            "description": "Updated description"
        }
        
        response = await authenticated_client.put(
            f"/shopping-lists/{test_shopping_list.id}", 
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["description"] == update_data["description"]
        assert data["name"] == test_shopping_list.name  # Unchanged

    async def test_update_shopping_list_ingredients(
        self, 
        authenticated_client: AsyncClient, 
        test_shopping_list
    ):
        """Test updating shopping list ingredients."""
        update_data = {
            "ingredients": [
                {
                    "name": "updated_ingredient",
                    "total_amount": "2 cups",
                    "unit": "cup",
                    "notes": ["Updated note"],
                    "recipe_names": ["Test Recipe"]
                }
            ]
        }
        
        response = await authenticated_client.put(
            f"/shopping-lists/{test_shopping_list.id}", 
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["ingredients"]) == 1
        assert data["ingredients"][0]["name"] == "updated_ingredient"

    async def test_update_shopping_list_not_found(self, authenticated_client: AsyncClient):
        """Test updating non-existent shopping list."""
        update_data = {"name": "Updated Name"}
        
        response = await authenticated_client.put("/shopping-lists/99999", json=update_data)
        
        assert response.status_code == 404

    async def test_update_shopping_list_wrong_user(
        self, 
        authenticated_client: AsyncClient, 
        test_second_user,
        db_session: AsyncSession
    ):
        """Test updating shopping list owned by different user."""
        # Create shopping list for second user
        other_shopping_list = ShoppingList(
            name="Other User's List",
            user_id=test_second_user.id,
            recipe_ids=[],
            ingredients=[]
        )
        db_session.add(other_shopping_list)
        await db_session.commit()
        await db_session.refresh(other_shopping_list)
        
        update_data = {"name": "Hacked Name"}
        
        response = await authenticated_client.put(
            f"/shopping-lists/{other_shopping_list.id}", 
            json=update_data
        )
        
        assert response.status_code == 403

    async def test_update_shopping_list_unauthorized(self, client: AsyncClient, test_shopping_list):
        """Test updating shopping list without authentication."""
        update_data = {"name": "Unauthorized Update"}
        
        response = await client.put(f"/shopping-lists/{test_shopping_list.id}", json=update_data)
        
        assert response.status_code == 401

    async def test_partial_update_shopping_list(
        self, 
        authenticated_client: AsyncClient, 
        test_shopping_list
    ):
        """Test partial update (only some fields)."""
        original_description = test_shopping_list.description
        update_data = {"name": "Partially Updated Name"}
        
        response = await authenticated_client.put(
            f"/shopping-lists/{test_shopping_list.id}", 
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Updated field
        assert data["name"] == "Partially Updated Name"
        # Unchanged field
        assert data["description"] == original_description


class TestShoppingListDeletion:
    """Test shopping list deletion endpoint."""

    async def test_delete_shopping_list_success(
        self, 
        authenticated_client: AsyncClient, 
        test_shopping_list,
        db_session: AsyncSession
    ):
        """Test successful shopping list deletion."""
        shopping_list_id = test_shopping_list.id
        
        response = await authenticated_client.delete(f"/shopping-lists/{shopping_list_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]
        
        # Verify deletion
        deleted_list = await db_session.get(ShoppingList, shopping_list_id)
        assert deleted_list is None

    async def test_delete_shopping_list_not_found(self, authenticated_client: AsyncClient):
        """Test deleting non-existent shopping list."""
        response = await authenticated_client.delete("/shopping-lists/99999")
        
        assert response.status_code == 404

    async def test_delete_shopping_list_wrong_user(
        self, 
        authenticated_client: AsyncClient, 
        test_second_user,
        db_session: AsyncSession
    ):
        """Test deleting shopping list owned by different user."""
        # Create shopping list for second user
        other_shopping_list = ShoppingList(
            name="Other User's List",
            user_id=test_second_user.id,
            recipe_ids=[],
            ingredients=[]
        )
        db_session.add(other_shopping_list)
        await db_session.commit()
        await db_session.refresh(other_shopping_list)
        
        response = await authenticated_client.delete(f"/shopping-lists/{other_shopping_list.id}")
        
        assert response.status_code == 403

    async def test_delete_shopping_list_unauthorized(self, client: AsyncClient, test_shopping_list):
        """Test deleting shopping list without authentication."""
        response = await client.delete(f"/shopping-lists/{test_shopping_list.id}")
        
        assert response.status_code == 401


class TestShoppingListIngredientLogic:
    """Test shopping list ingredient aggregation and grouping logic."""

    async def test_ingredient_aggregation_same_unit(
        self, 
        authenticated_client: AsyncClient, 
        db_session: AsyncSession,
        test_user
    ):
        """Test ingredient aggregation with same units."""
        # Create recipes with same ingredient and unit
        recipe1 = Recipe(
            title="Recipe 1",
            description="Test recipe 1",
            ingredients=[
                {"name": "flour", "amount": "2", "unit": "cup"}
            ],
            instructions="Instructions",
            prep_time_minutes=10,
            cook_time_minutes=20,
            servings=4,
            is_public=True,
            author_id=test_user.id
        )
        
        recipe2 = Recipe(
            title="Recipe 2",
            description="Test recipe 2", 
            ingredients=[
                {"name": "flour", "amount": "1.5", "unit": "cup"}
            ],
            instructions="Instructions",
            prep_time_minutes=10,
            cook_time_minutes=20,
            servings=4,
            is_public=True,
            author_id=test_user.id
        )
        
        db_session.add_all([recipe1, recipe2])
        await db_session.commit()
        await db_session.refresh(recipe1)
        await db_session.refresh(recipe2)
        
        shopping_list_data = {
            "name": "Aggregation Test",
            "recipe_ids": [recipe1.id, recipe2.id]
        }
        
        response = await authenticated_client.post("/shopping-lists/", json=shopping_list_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have one flour entry with aggregated amount
        flour_ingredients = [ing for ing in data["ingredients"] if ing["name"] == "flour"]
        assert len(flour_ingredients) == 1
        assert "3.5" in flour_ingredients[0]["total_amount"] or "7/2" in flour_ingredients[0]["total_amount"]

    async def test_ingredient_grouping_categories(
        self, 
        authenticated_client: AsyncClient, 
        test_shopping_list
    ):
        """Test that ingredients are grouped by categories."""
        response = await authenticated_client.get(f"/shopping-lists/{test_shopping_list.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have ingredient groups
        assert "ingredient_groups" in data
        
        # Categories should be properly formatted
        for group in data["ingredient_groups"]:
            assert "category" in group
            assert group["category"] != group["category"].lower()  # Should be title case

    async def test_recipe_names_tracking(
        self, 
        authenticated_client: AsyncClient, 
        multiple_recipes
    ):
        """Test that ingredient tracking includes recipe names."""
        recipe_ids = [recipe.id for recipe in multiple_recipes[:2]]
        shopping_list_data = {
            "name": "Recipe Tracking Test",
            "recipe_ids": recipe_ids
        }
        
        response = await authenticated_client.post("/shopping-lists/", json=shopping_list_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Each ingredient should track which recipes it came from
        for ingredient in data["ingredients"]:
            assert "recipe_names" in ingredient
            assert isinstance(ingredient["recipe_names"], list)
            if ingredient["recipe_names"]:  # If has recipe names
                # Should be valid recipe names
                recipe_names = [recipe.title for recipe in multiple_recipes[:2]]
                for recipe_name in ingredient["recipe_names"]:
                    assert recipe_name in recipe_names


class TestShoppingListWorkflows:
    """Test complete shopping list workflows."""

    async def test_complete_shopping_list_workflow(
        self, 
        authenticated_client: AsyncClient, 
        multiple_recipes
    ):
        """Test complete workflow: generate preview -> create -> update -> delete."""
        recipe_ids = [recipe.id for recipe in multiple_recipes[:2]]
        
        # 1. Generate preview
        preview_request = {
            "recipe_ids": recipe_ids,
            "list_name": "Workflow Test",
            "merge_similar_ingredients": True
        }
        
        preview_response = await authenticated_client.post("/shopping-lists/generate", json=preview_request)
        assert preview_response.status_code == 200
        preview_data = preview_response.json()
        assert preview_data["id"] == 0  # Preview
        
        # 2. Create shopping list
        create_data = {
            "name": "Workflow Test List",
            "description": "Complete workflow test",
            "recipe_ids": recipe_ids
        }
        
        create_response = await authenticated_client.post("/shopping-lists/", json=create_data)
        assert create_response.status_code == 200
        create_data = create_response.json()
        shopping_list_id = create_data["id"]
        
        # 3. Get shopping list
        get_response = await authenticated_client.get(f"/shopping-lists/{shopping_list_id}")
        assert get_response.status_code == 200
        
        # 4. Update shopping list
        update_data = {"name": "Updated Workflow List"}
        update_response = await authenticated_client.put(f"/shopping-lists/{shopping_list_id}", json=update_data)
        assert update_response.status_code == 200
        updated_data = update_response.json()
        assert updated_data["name"] == "Updated Workflow List"
        
        # 5. Delete shopping list
        delete_response = await authenticated_client.delete(f"/shopping-lists/{shopping_list_id}")
        assert delete_response.status_code == 200

    async def test_shopping_list_with_private_and_public_recipes(
        self, 
        authenticated_client: AsyncClient, 
        test_recipe,
        test_private_recipe
    ):
        """Test shopping list with mix of private and public recipes."""
        recipe_ids = [test_recipe.id, test_private_recipe.id]
        shopping_list_data = {
            "name": "Mixed Recipes List",
            "recipe_ids": recipe_ids
        }
        
        response = await authenticated_client.post("/shopping-lists/", json=shopping_list_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should include both recipes
        assert set(data["recipe_ids"]) == set(recipe_ids)
        assert len(data["ingredients"]) > 0