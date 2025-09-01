"""
Tests for voting system endpoints.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vote import Vote
from app.models.recipe import Recipe


class TestVoteCreation:
    """Test voting on recipes."""

    async def test_upvote_recipe_success(self, authenticated_client: AsyncClient, test_recipe):
        """Test successful upvote on recipe."""
        vote_data = {"vote_value": 1}
        
        response = await authenticated_client.post(f"/votes/recipes/{test_recipe.id}", json=vote_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["recipe_id"] == test_recipe.id
        assert data["upvotes"] == 1
        assert data["downvotes"] == 0
        assert data["vote_score"] == 1
        assert data["total_votes"] == 1

    async def test_downvote_recipe_success(self, authenticated_client: AsyncClient, test_recipe):
        """Test successful downvote on recipe."""
        vote_data = {"vote_value": -1}
        
        response = await authenticated_client.post(f"/votes/recipes/{test_recipe.id}", json=vote_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["recipe_id"] == test_recipe.id
        assert data["upvotes"] == 0
        assert data["downvotes"] == 1
        assert data["vote_score"] == -1
        assert data["total_votes"] == 1

    async def test_vote_nonexistent_recipe(self, authenticated_client: AsyncClient):
        """Test voting on non-existent recipe."""
        vote_data = {"vote_value": 1}
        
        response = await authenticated_client.post("/votes/recipes/99999", json=vote_data)
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"] is True
        assert data["type"] == "not_found_error"
        assert "Recipe not found" in data["message"]

    async def test_vote_unauthorized(self, client: AsyncClient, test_recipe):
        """Test voting without authentication."""
        vote_data = {"vote_value": 1}
        
        response = await client.post(f"/votes/recipes/{test_recipe.id}", json=vote_data)
        
        assert response.status_code == 401

    async def test_vote_invalid_value(self, authenticated_client: AsyncClient, test_recipe):
        """Test voting with invalid vote value."""
        vote_data = {"vote_value": 0}  # Only 1 and -1 are valid
        
        response = await authenticated_client.post(f"/votes/recipes/{test_recipe.id}", json=vote_data)
        
        assert response.status_code == 422  # Validation error

    async def test_vote_extreme_values(self, authenticated_client: AsyncClient, test_recipe):
        """Test voting with extreme values."""
        invalid_votes = [2, -2, 10, -10, 999]
        
        for vote_value in invalid_votes:
            vote_data = {"vote_value": vote_value}
            response = await authenticated_client.post(f"/votes/recipes/{test_recipe.id}", json=vote_data)
            assert response.status_code == 422

    async def test_vote_missing_data(self, authenticated_client: AsyncClient, test_recipe):
        """Test voting with missing vote value."""
        response = await authenticated_client.post(f"/votes/recipes/{test_recipe.id}", json={})
        
        assert response.status_code == 422

    async def test_vote_creates_database_record(
        self, 
        authenticated_client: AsyncClient, 
        test_recipe, 
        test_user,
        db_session: AsyncSession
    ):
        """Test that voting creates a proper database record."""
        vote_data = {"vote_value": 1}
        
        response = await authenticated_client.post(f"/votes/recipes/{test_recipe.id}", json=vote_data)
        assert response.status_code == 200
        
        # Check database record
        from sqlalchemy import select
        vote_result = await db_session.execute(
            select(Vote).where(
                Vote.user_id == test_user.id,
                Vote.recipe_id == test_recipe.id
            )
        )
        vote = vote_result
        vote_record = vote.scalar_one_or_none()
        
        assert vote_record is not None
        assert vote_record.vote_value == 1
        assert vote_record.user_id == test_user.id
        assert vote_record.recipe_id == test_recipe.id


class TestVoteChanges:
    """Test changing votes on recipes."""

    async def test_change_upvote_to_downvote(self, authenticated_client: AsyncClient, test_vote):
        """Test changing an upvote to a downvote."""
        recipe_id = test_vote.recipe_id
        
        # Initial state: upvote exists (from fixture)
        vote_data = {"vote_value": -1}  # Change to downvote
        
        response = await authenticated_client.post(f"/votes/recipes/{recipe_id}", json=vote_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["upvotes"] == 0  # Should decrease
        assert data["downvotes"] == 1  # Should increase
        assert data["vote_score"] == -1
        assert data["total_votes"] == 1

    async def test_change_downvote_to_upvote(
        self, 
        authenticated_client: AsyncClient, 
        test_recipe, 
        test_user,
        db_session: AsyncSession
    ):
        """Test changing a downvote to an upvote."""
        # Create initial downvote
        initial_downvote = Vote(
            user_id=test_user.id,
            recipe_id=test_recipe.id,
            vote_value=-1
        )
        db_session.add(initial_downvote)
        
        # Update recipe counts
        test_recipe.downvotes = 1
        test_recipe.upvotes = 0
        test_recipe.vote_score = -1
        
        await db_session.commit()
        
        # Change to upvote
        vote_data = {"vote_value": 1}
        
        response = await authenticated_client.post(f"/votes/recipes/{test_recipe.id}", json=vote_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["upvotes"] == 1
        assert data["downvotes"] == 0
        assert data["vote_score"] == 1
        assert data["total_votes"] == 1

    async def test_same_vote_value_update(self, authenticated_client: AsyncClient, test_vote):
        """Test voting with the same value (should update timestamp but not counts)."""
        recipe_id = test_vote.recipe_id
        
        # Vote with same value as existing vote
        vote_data = {"vote_value": 1}  # Same as test_vote
        
        response = await authenticated_client.post(f"/votes/recipes/{recipe_id}", json=vote_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Counts should remain the same
        assert data["upvotes"] == 1  # From original test_vote
        assert data["downvotes"] == 0
        assert data["vote_score"] == 1
        assert data["total_votes"] == 1

    async def test_vote_change_updates_recipe_counts(
        self, 
        authenticated_client: AsyncClient, 
        test_vote,
        db_session: AsyncSession
    ):
        """Test that vote changes properly update recipe denormalized counts."""
        recipe_id = test_vote.recipe_id
        
        # Change from upvote to downvote
        vote_data = {"vote_value": -1}
        response = await authenticated_client.post(f"/votes/recipes/{recipe_id}", json=vote_data)
        assert response.status_code == 200
        
        # Check recipe in database
        recipe = await db_session.get(Recipe, recipe_id)
        assert recipe.upvotes == 0
        assert recipe.downvotes == 1
        assert recipe.vote_score == -1


class TestVoteRemoval:
    """Test removing votes from recipes."""

    async def test_remove_vote_success(self, authenticated_client: AsyncClient, test_vote, db_session: AsyncSession):
        """Test successfully removing a vote."""
        recipe_id = test_vote.recipe_id
        user_id = test_vote.user_id
        
        response = await authenticated_client.delete(f"/votes/recipes/{recipe_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["recipe_id"] == recipe_id
        assert data["upvotes"] == 0  # Should decrease from 1 to 0
        assert data["downvotes"] == 0
        assert data["vote_score"] == 0
        assert data["total_votes"] == 0
        
        # Verify vote is deleted from database  
        from sqlalchemy import select
        vote_check = await db_session.execute(
            select(Vote).where(
                Vote.user_id == user_id,
                Vote.recipe_id == recipe_id
            )
        )
        deleted_vote = vote_check.scalar_one_or_none()
        assert deleted_vote is None

    async def test_remove_downvote(
        self, 
        authenticated_client: AsyncClient, 
        test_recipe,
        test_user,
        db_session: AsyncSession
    ):
        """Test removing a downvote."""
        # Create downvote
        downvote = Vote(
            user_id=test_user.id,
            recipe_id=test_recipe.id,
            vote_value=-1
        )
        db_session.add(downvote)
        
        # Update recipe counts
        test_recipe.downvotes = 1
        test_recipe.upvotes = 0
        test_recipe.vote_score = -1
        
        await db_session.commit()
        
        # Remove vote
        response = await authenticated_client.delete(f"/votes/recipes/{test_recipe.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["upvotes"] == 0
        assert data["downvotes"] == 0  # Should decrease from 1 to 0
        assert data["vote_score"] == 0
        assert data["total_votes"] == 0

    async def test_remove_vote_nonexistent_recipe(self, authenticated_client: AsyncClient):
        """Test removing vote from non-existent recipe."""
        response = await authenticated_client.delete("/votes/recipes/99999")
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"] is True
        assert "Recipe not found" in data["message"]

    async def test_remove_vote_not_voted(self, authenticated_client: AsyncClient, test_recipe):
        """Test removing vote when user hasn't voted."""
        response = await authenticated_client.delete(f"/votes/recipes/{test_recipe.id}")
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"] is True
        assert "Vote not found" in data["message"]

    async def test_remove_vote_unauthorized(self, client: AsyncClient, test_vote):
        """Test removing vote without authentication."""
        recipe_id = test_vote.recipe_id
        
        response = await client.delete(f"/votes/recipes/{recipe_id}")
        
        assert response.status_code == 401

    async def test_remove_vote_wrong_user(
        self, 
        authenticated_client: AsyncClient, 
        test_second_user,
        test_recipe,
        db_session: AsyncSession
    ):
        """Test removing vote created by different user."""
        # Create vote by second user
        other_vote = Vote(
            user_id=test_second_user.id,
            recipe_id=test_recipe.id,
            vote_value=1
        )
        db_session.add(other_vote)
        await db_session.commit()
        
        # Try to remove with different user (authenticated_client uses test_user)
        response = await authenticated_client.delete(f"/votes/recipes/{test_recipe.id}")
        
        assert response.status_code == 404  # Vote not found for current user
        data = response.json()
        assert "Vote not found" in data["message"]


class TestVoteStatus:
    """Test getting user vote status."""

    async def test_get_vote_status_with_upvote(self, authenticated_client: AsyncClient, test_vote):
        """Test getting vote status when user has upvoted."""
        recipe_id = test_vote.recipe_id
        
        response = await authenticated_client.get(f"/votes/recipes/{recipe_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["recipe_id"] == recipe_id
        assert data["user_vote"] == 1  # User has upvoted
        assert data["total_upvotes"] == 1
        assert data["total_downvotes"] == 0
        assert data["vote_score"] == 1

    async def test_get_vote_status_with_downvote(
        self, 
        authenticated_client: AsyncClient, 
        test_recipe,
        test_user,
        db_session: AsyncSession
    ):
        """Test getting vote status when user has downvoted."""
        # Create downvote
        downvote = Vote(
            user_id=test_user.id,
            recipe_id=test_recipe.id,
            vote_value=-1
        )
        db_session.add(downvote)
        
        # Update recipe counts
        test_recipe.downvotes = 1
        test_recipe.vote_score = -1
        
        await db_session.commit()
        
        response = await authenticated_client.get(f"/votes/recipes/{test_recipe.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["user_vote"] == -1  # User has downvoted
        assert data["total_upvotes"] == 0
        assert data["total_downvotes"] == 1
        assert data["vote_score"] == -1

    async def test_get_vote_status_no_vote(self, authenticated_client: AsyncClient, test_recipe):
        """Test getting vote status when user hasn't voted."""
        response = await authenticated_client.get(f"/votes/recipes/{test_recipe.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["recipe_id"] == test_recipe.id
        assert data["user_vote"] is None  # No vote
        assert data["total_upvotes"] == 0
        assert data["total_downvotes"] == 0
        assert data["vote_score"] == 0

    async def test_get_vote_status_nonexistent_recipe(self, authenticated_client: AsyncClient):
        """Test getting vote status for non-existent recipe."""
        response = await authenticated_client.get("/votes/recipes/99999")
        
        assert response.status_code == 404
        data = response.json()
        assert "Recipe not found" in data["message"]

    async def test_get_vote_status_unauthorized(self, client: AsyncClient, test_recipe):
        """Test getting vote status without authentication."""
        response = await client.get(f"/votes/recipes/{test_recipe.id}")
        
        assert response.status_code == 401

    async def test_get_vote_status_with_multiple_votes(
        self, 
        authenticated_client: AsyncClient, 
        test_recipe,
        test_user,
        test_second_user,
        db_session: AsyncSession
    ):
        """Test vote status when recipe has multiple votes from different users."""
        # Create votes from both users
        vote1 = Vote(user_id=test_user.id, recipe_id=test_recipe.id, vote_value=1)
        vote2 = Vote(user_id=test_second_user.id, recipe_id=test_recipe.id, vote_value=-1)
        
        db_session.add_all([vote1, vote2])
        
        # Update recipe counts
        test_recipe.upvotes = 1
        test_recipe.downvotes = 1
        test_recipe.vote_score = 0
        
        await db_session.commit()
        
        response = await authenticated_client.get(f"/votes/recipes/{test_recipe.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should show current user's vote and all totals
        assert data["user_vote"] == 1  # Current user's upvote
        assert data["total_upvotes"] == 1
        assert data["total_downvotes"] == 1
        assert data["vote_score"] == 0


class TestVoteStatistics:
    """Test getting recipe vote statistics."""

    async def test_get_vote_stats_success(self, client: AsyncClient, test_recipe, db_session: AsyncSession):
        """Test getting vote statistics for a recipe."""
        # Set up some vote data
        test_recipe.upvotes = 5
        test_recipe.downvotes = 2
        test_recipe.vote_score = 3
        await db_session.commit()
        
        response = await client.get(f"/votes/recipes/{test_recipe.id}/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["recipe_id"] == test_recipe.id
        assert data["upvotes"] == 5
        assert data["downvotes"] == 2
        assert data["vote_score"] == 3
        assert data["total_votes"] == 7

    async def test_get_vote_stats_no_votes(self, client: AsyncClient, test_recipe):
        """Test getting vote statistics for recipe with no votes."""
        response = await client.get(f"/votes/recipes/{test_recipe.id}/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["recipe_id"] == test_recipe.id
        assert data["upvotes"] == 0
        assert data["downvotes"] == 0
        assert data["vote_score"] == 0
        assert data["total_votes"] == 0

    async def test_get_vote_stats_nonexistent_recipe(self, client: AsyncClient):
        """Test getting vote statistics for non-existent recipe."""
        response = await client.get("/votes/recipes/99999/stats")
        
        assert response.status_code == 404
        data = response.json()
        assert "Recipe not found" in data["message"]

    async def test_get_vote_stats_public_endpoint(self, client: AsyncClient, test_recipe):
        """Test that vote stats endpoint doesn't require authentication."""
        # This test verifies the endpoint is public (no authentication required)
        response = await client.get(f"/votes/recipes/{test_recipe.id}/stats")
        
        assert response.status_code == 200  # Should work without authentication


class TestVoteAggregation:
    """Test vote aggregation and counting logic."""

    async def test_multiple_users_voting(
        self, 
        authenticated_client: AsyncClient, 
        test_recipe,
        test_second_user,
        db_session: AsyncSession
    ):
        """Test vote aggregation with multiple users."""
        # First user upvotes (via authenticated_client)
        vote_data = {"vote_value": 1}
        response1 = await authenticated_client.post(f"/votes/recipes/{test_recipe.id}", json=vote_data)
        assert response1.status_code == 200
        
        # Create second user's downvote manually (since we only have one auth client)
        second_vote = Vote(
            user_id=test_second_user.id,
            recipe_id=test_recipe.id,
            vote_value=-1
        )
        db_session.add(second_vote)
        
        # Update recipe counts manually (normally done by the endpoint)
        test_recipe.downvotes = 1  # Add second user's downvote
        test_recipe.vote_score = test_recipe.upvotes - test_recipe.downvotes
        
        await db_session.commit()
        
        # Check final stats
        stats_response = await authenticated_client.get(f"/votes/recipes/{test_recipe.id}/stats")
        assert stats_response.status_code == 200
        stats_data = stats_response.json()
        
        assert stats_data["upvotes"] == 1
        assert stats_data["downvotes"] == 1
        assert stats_data["vote_score"] == 0
        assert stats_data["total_votes"] == 2

    async def test_vote_count_consistency(
        self, 
        authenticated_client: AsyncClient, 
        test_recipe,
        db_session: AsyncSession
    ):
        """Test that vote counts remain consistent through operations."""
        # Initial upvote
        vote_data = {"vote_value": 1}
        response1 = await authenticated_client.post(f"/votes/recipes/{test_recipe.id}", json=vote_data)
        data1 = response1.json()
        
        assert data1["upvotes"] == 1
        assert data1["total_votes"] == 1
        
        # Change to downvote
        vote_data = {"vote_value": -1}
        response2 = await authenticated_client.post(f"/votes/recipes/{test_recipe.id}", json=vote_data)
        data2 = response2.json()
        
        assert data2["upvotes"] == 0
        assert data2["downvotes"] == 1
        assert data2["total_votes"] == 1  # Should remain 1
        
        # Remove vote
        response3 = await authenticated_client.delete(f"/votes/recipes/{test_recipe.id}")
        data3 = response3.json()
        
        assert data3["upvotes"] == 0
        assert data3["downvotes"] == 0
        assert data3["total_votes"] == 0

    async def test_vote_score_calculation(
        self, 
        authenticated_client: AsyncClient, 
        test_recipe,
        db_session: AsyncSession
    ):
        """Test vote score calculation (upvotes - downvotes)."""
        # Simulate multiple votes by directly manipulating recipe
        test_recipe.upvotes = 10
        test_recipe.downvotes = 3
        test_recipe.vote_score = 7  # 10 - 3
        await db_session.commit()
        
        response = await authenticated_client.get(f"/votes/recipes/{test_recipe.id}/stats")
        data = response.json()
        
        assert data["vote_score"] == 7
        assert data["vote_score"] == data["upvotes"] - data["downvotes"]

    async def test_negative_vote_score(
        self, 
        authenticated_client: AsyncClient, 
        test_recipe,
        db_session: AsyncSession
    ):
        """Test negative vote score when downvotes exceed upvotes."""
        test_recipe.upvotes = 2
        test_recipe.downvotes = 5
        test_recipe.vote_score = -3  # 2 - 5
        await db_session.commit()
        
        response = await authenticated_client.get(f"/votes/recipes/{test_recipe.id}/stats")
        data = response.json()
        
        assert data["vote_score"] == -3
        assert data["upvotes"] == 2
        assert data["downvotes"] == 5


class TestVoteWorkflows:
    """Test complete voting workflows."""

    async def test_complete_voting_workflow(
        self, 
        authenticated_client: AsyncClient, 
        test_recipe
    ):
        """Test a complete voting workflow: vote, change, remove."""
        recipe_id = test_recipe.id
        
        # 1. Initial upvote
        vote_data = {"vote_value": 1}
        response1 = await authenticated_client.post(f"/votes/recipes/{recipe_id}", json=vote_data)
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["vote_score"] == 1
        
        # 2. Check vote status
        status_response = await authenticated_client.get(f"/votes/recipes/{recipe_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["user_vote"] == 1
        
        # 3. Change to downvote
        vote_data = {"vote_value": -1}
        response2 = await authenticated_client.post(f"/votes/recipes/{recipe_id}", json=vote_data)
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["vote_score"] == -1
        
        # 4. Check updated status
        status_response2 = await authenticated_client.get(f"/votes/recipes/{recipe_id}")
        status_data2 = status_response2.json()
        assert status_data2["user_vote"] == -1
        
        # 5. Remove vote
        response3 = await authenticated_client.delete(f"/votes/recipes/{recipe_id}")
        assert response3.status_code == 200
        data3 = response3.json()
        assert data3["vote_score"] == 0
        
        # 6. Check final status
        status_response3 = await authenticated_client.get(f"/votes/recipes/{recipe_id}")
        status_data3 = status_response3.json()
        assert status_data3["user_vote"] is None

    async def test_vote_on_own_recipe(self, authenticated_client: AsyncClient, test_recipe):
        """Test voting on own recipe (should be allowed)."""
        vote_data = {"vote_value": 1}
        
        response = await authenticated_client.post(f"/votes/recipes/{test_recipe.id}", json=vote_data)
        
        # Should be allowed - users can vote on their own recipes
        assert response.status_code == 200
        data = response.json()
        assert data["vote_score"] == 1

    async def test_vote_on_private_recipe(
        self, 
        authenticated_client: AsyncClient, 
        test_private_recipe
    ):
        """Test voting on private recipe."""
        vote_data = {"vote_value": 1}
        
        response = await authenticated_client.post(f"/votes/recipes/{test_private_recipe.id}", json=vote_data)
        
        # Should work if recipe exists and user can access it
        assert response.status_code == 200
        data = response.json()
        assert data["recipe_id"] == test_private_recipe.id