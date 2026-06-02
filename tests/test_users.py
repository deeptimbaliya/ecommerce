# tests/test_users.py
import pytest


class TestGetMe:
    def test_get_me_authenticated(self, client, auth_headers, test_user_data):
        """Logged in user can get their profile."""
        response = client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == test_user_data["email"]

    def test_get_me_unauthenticated(self, client):
        """No token → 401."""
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401

    def test_get_me_invalid_token(self, client):
        """Fake token → 401."""
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer faketoken"}
        )
        assert response.status_code == 401


class TestAdminRoutes:
    def test_list_users_as_admin(self, client, admin_user):
        """Admin can list all users."""
        response = client.get("/api/v1/users", headers=admin_user["headers"])
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_list_users_as_regular_user(self, client, auth_headers):
        """Regular user cannot list all users."""
        response = client.get("/api/v1/users", headers=auth_headers)
        assert response.status_code == 403

    def test_delete_user_as_admin(self, client, admin_user, registered_user):
        """Admin can delete a user."""
        user_id = registered_user["id"]
        response = client.delete(
            f"/api/v1/users/{user_id}",
            headers=admin_user["headers"]
        )
        assert response.status_code == 204

    def test_delete_nonexistent_user(self, client, admin_user):
        """Deleting non-existent user returns 404."""
        response = client.delete(
            "/api/v1/users/99999",
            headers=admin_user["headers"]
        )
        assert response.status_code == 404