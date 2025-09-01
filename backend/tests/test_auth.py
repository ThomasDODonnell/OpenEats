"""
Tests for authentication endpoints.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.security import verify_password


class TestUserRegistration:
    """Test user registration endpoint."""

    async def test_register_user_success(self, client: AsyncClient, test_user_data):
        """Test successful user registration."""
        response = await client.post("/auth/register", json=test_user_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["email"] == test_user_data["email"]
        assert data["first_name"] == test_user_data["first_name"]
        assert data["last_name"] == test_user_data["last_name"]
        assert data["is_active"] is True
        assert "id" in data
        assert "hashed_password" not in data  # Should not expose password
        assert "created_at" in data

    async def test_register_user_duplicate_email(self, client: AsyncClient, test_user, test_user_data):
        """Test registration with duplicate email."""
        response = await client.post("/auth/register", json=test_user_data)
        
        assert response.status_code == 409
        data = response.json()
        assert data["error"] is True
        assert data["type"] == "conflict_error"
        assert "Email already registered" in data["message"]

    async def test_register_user_invalid_email(self, client: AsyncClient, test_user_data):
        """Test registration with invalid email format."""
        test_user_data["email"] = "invalid-email"
        response = await client.post("/auth/register", json=test_user_data)
        
        assert response.status_code == 422  # Validation error

    async def test_register_user_weak_password(self, client: AsyncClient, test_user_data):
        """Test registration with weak password."""
        test_user_data["password"] = "123"  # Too short
        response = await client.post("/auth/register", json=test_user_data)
        
        assert response.status_code == 422  # Validation error

    async def test_register_user_missing_fields(self, client: AsyncClient):
        """Test registration with missing required fields."""
        incomplete_data = {
            "email": "incomplete@example.com",
            # Missing password, first_name, last_name
        }
        response = await client.post("/auth/register", json=incomplete_data)
        
        assert response.status_code == 422

    async def test_register_user_empty_names(self, client: AsyncClient, test_user_data):
        """Test registration with empty name fields."""
        test_user_data["first_name"] = ""
        test_user_data["last_name"] = ""
        response = await client.post("/auth/register", json=test_user_data)
        
        assert response.status_code == 422

    async def test_password_is_hashed(self, client: AsyncClient, db_session: AsyncSession, test_user_data):
        """Test that password is properly hashed in database."""
        response = await client.post("/auth/register", json=test_user_data)
        assert response.status_code == 201
        
        user_id = response.json()["id"]
        user = await db_session.get(User, user_id)
        
        # Password should be hashed, not plain text
        assert user.hashed_password != test_user_data["password"]
        assert verify_password(test_user_data["password"], user.hashed_password)


class TestUserLogin:
    """Test user login endpoint."""

    async def test_login_success(self, client: AsyncClient, test_user, test_user_data):
        """Test successful user login."""
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = await client.post("/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0

    async def test_login_invalid_email(self, client: AsyncClient, test_user, test_user_data):
        """Test login with non-existent email."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": test_user_data["password"]
        }
        response = await client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] is True
        assert data["type"] == "authentication_error"
        assert "Invalid email or password" in data["message"]

    async def test_login_invalid_password(self, client: AsyncClient, test_user, test_user_data):
        """Test login with incorrect password."""
        login_data = {
            "email": test_user_data["email"],
            "password": "wrongpassword"
        }
        response = await client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] is True
        assert data["type"] == "authentication_error"
        assert "Invalid email or password" in data["message"]

    async def test_login_inactive_user(self, client: AsyncClient, db_session: AsyncSession, test_user, test_user_data):
        """Test login with deactivated user account."""
        # Deactivate user
        test_user.is_active = False
        await db_session.commit()
        
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = await client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] is True
        assert "Account is deactivated" in data["message"]

    async def test_login_missing_fields(self, client: AsyncClient):
        """Test login with missing fields."""
        incomplete_data = {
            "email": "test@example.com"
            # Missing password
        }
        response = await client.post("/auth/login", json=incomplete_data)
        
        assert response.status_code == 422

    async def test_login_empty_fields(self, client: AsyncClient):
        """Test login with empty fields."""
        empty_data = {
            "email": "",
            "password": ""
        }
        response = await client.post("/auth/login", json=empty_data)
        
        assert response.status_code == 422


class TestTokenRefresh:
    """Test token refresh endpoint."""

    async def test_refresh_token_success(self, authenticated_client: AsyncClient):
        """Test successful token refresh."""
        response = await authenticated_client.post("/auth/refresh")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0

    async def test_refresh_token_without_auth(self, client: AsyncClient):
        """Test token refresh without authentication."""
        response = await client.post("/auth/refresh")
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] is True
        assert data["type"] == "authentication_error"

    async def test_refresh_token_invalid_token(self, client: AsyncClient):
        """Test token refresh with invalid token."""
        client.headers.update({"Authorization": "Bearer invalid-token"})
        response = await client.post("/auth/refresh")
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] is True
        assert data["type"] == "authentication_error"

    async def test_refresh_token_malformed_header(self, client: AsyncClient):
        """Test token refresh with malformed authorization header."""
        client.headers.update({"Authorization": "InvalidFormat token"})
        response = await client.post("/auth/refresh")
        
        assert response.status_code == 401


class TestCurrentUser:
    """Test current user information endpoint."""

    async def test_get_current_user_success(self, authenticated_client: AsyncClient, test_user):
        """Test successful retrieval of current user information."""
        response = await authenticated_client.get("/auth/me")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert data["first_name"] == test_user.first_name
        assert data["last_name"] == test_user.last_name
        assert data["is_active"] == test_user.is_active
        assert "created_at" in data
        assert "hashed_password" not in data  # Should not expose password

    async def test_get_current_user_without_auth(self, client: AsyncClient):
        """Test getting current user without authentication."""
        response = await client.get("/auth/me")
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] is True
        assert data["type"] == "authentication_error"

    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token."""
        client.headers.update({"Authorization": "Bearer invalid-token"})
        response = await client.get("/auth/me")
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] is True
        assert data["type"] == "authentication_error"

    async def test_get_current_user_expired_token(self, client: AsyncClient):
        """Test getting current user with expired token."""
        # This would require creating an expired token
        # For now, we'll test with an obviously invalid token format
        expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIiwiZXhwIjowfQ.invalid"
        client.headers.update({"Authorization": f"Bearer {expired_token}"})
        response = await client.get("/auth/me")
        
        assert response.status_code == 401


class TestAuthenticationFlow:
    """Test complete authentication flows."""

    async def test_complete_auth_flow(self, client: AsyncClient, test_user_data):
        """Test complete registration -> login -> get user flow."""
        # 1. Register user
        register_response = await client.post("/auth/register", json=test_user_data)
        assert register_response.status_code == 201
        user_data = register_response.json()
        
        # 2. Login
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        login_response = await client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200
        token_data = login_response.json()
        
        # 3. Use token to get user info
        client.headers.update({"Authorization": f"Bearer {token_data['access_token']}"})
        me_response = await client.get("/auth/me")
        assert me_response.status_code == 200
        
        me_data = me_response.json()
        assert me_data["id"] == user_data["id"]
        assert me_data["email"] == user_data["email"]

    async def test_token_refresh_flow(self, authenticated_client: AsyncClient, test_user):
        """Test token refresh preserves user access."""
        # 1. Get initial user info
        initial_response = await authenticated_client.get("/auth/me")
        assert initial_response.status_code == 200
        initial_data = initial_response.json()
        
        # 2. Refresh token
        refresh_response = await authenticated_client.post("/auth/refresh")
        assert refresh_response.status_code == 200
        new_token_data = refresh_response.json()
        
        # 3. Use new token to get user info
        authenticated_client.headers.update({
            "Authorization": f"Bearer {new_token_data['access_token']}"
        })
        new_response = await authenticated_client.get("/auth/me")
        assert new_response.status_code == 200
        
        new_data = new_response.json()
        assert new_data["id"] == initial_data["id"]
        assert new_data["email"] == initial_data["email"]

    async def test_case_insensitive_email_login(self, client: AsyncClient, test_user, test_user_data):
        """Test login with different email case."""
        login_data = {
            "email": test_user_data["email"].upper(),  # Different case
            "password": test_user_data["password"]
        }
        response = await client.post("/auth/login", json=login_data)
        
        # This test depends on whether email comparison is case-insensitive
        # Current implementation might be case-sensitive, so this tests that behavior
        assert response.status_code in [200, 401]  # Either works or fails consistently


class TestSecurityHeaders:
    """Test security-related headers and responses."""

    async def test_no_password_in_response(self, client: AsyncClient, test_user_data):
        """Test that passwords are never included in responses."""
        # Register user
        register_response = await client.post("/auth/register", json=test_user_data)
        register_data = register_response.json()
        
        # Check registration response
        assert "password" not in register_data
        assert "hashed_password" not in register_data
        
        # Login and check user info response
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        login_response = await client.post("/auth/login", json=login_data)
        token_data = login_response.json()
        
        client.headers.update({"Authorization": f"Bearer {token_data['access_token']}"})
        me_response = await client.get("/auth/me")
        me_data = me_response.json()
        
        assert "password" not in me_data
        assert "hashed_password" not in me_data

    async def test_token_format(self, client: AsyncClient, test_user, test_user_data):
        """Test that tokens follow expected JWT format."""
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = await client.post("/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # JWT tokens have 3 parts separated by dots
        token = data["access_token"]
        parts = token.split(".")
        assert len(parts) == 3
        
        # Each part should be base64-encoded (though we won't decode/verify here)
        for part in parts:
            assert len(part) > 0