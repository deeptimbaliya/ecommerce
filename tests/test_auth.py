import pytest 


class TestRegister:
    def test_register_success(self, client, test_user_data):
        """Happy path — register a new user."""
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == test_user_data["email"]
        assert "password" not in data["data"]   # never expose password

    def test_register_duplicate_email(self, client, test_user_data, registered_user):
        """Can't register same email twice."""
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client, test_user_data):
        """Invalid email format rejected."""
        test_user_data["email"] = "not-an-email"
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 422

    def test_register_weak_password(self, client, test_user_data):
        """Weak password rejected."""
        test_user_data["password"] = "weak"
        test_user_data["confirm_password"] = "weak"
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 422

    def test_register_password_mismatch(self, client, test_user_data):
        """Mismatched passwords rejected."""
        test_user_data["confirm_password"] = "Different@1234"
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 422

    def test_register_missing_fields(self, client):
        """Missing required fields rejected."""
        response = client.post("/api/v1/auth/register", json={})
        assert response.status_code == 422


class TestLogin:
    def test_login_success(self, client, test_user_data, registered_user):
        """Happy path — login returns token."""
        response = client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user_data, registered_user):
        """Wrong password returns 401."""
        response = client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": "WrongPassword@1"
        })
        assert response.status_code == 401
        assert "invalid credentials" in response.json()["detail"].lower()

    def test_login_nonexistent_email(self, client):
        """Login with unknown email returns 401."""
        response = client.post("/api/v1/auth/login", json={
            "email": "nobody@example.com",
            "password": "Test@1234"
        })
        assert response.status_code == 401