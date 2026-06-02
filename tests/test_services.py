import pytest
from app.services import user_service
from app.schemas.user import UserCreate
from fastapi import HTTPException


class TestUserService:
    def test_create_user(self, db):
        """Service creates user correctly."""
        payload = UserCreate(
            name="Alice",
            email="alice@example.com",
            password="Alice@1234",
            confirm_password="Alice@1234"
        )
        user = user_service.create_user(db, payload)
        assert user.id is not None
        assert user.email == "alice@example.com"
        assert user.name == "Alice"
        assert user.password_hash != "Alice@1234"   # must be hashed

    def test_create_user_duplicate_email(self, db):
        """Duplicate email raises 400."""
        payload = UserCreate(
            name="Alice",
            email="alice@example.com",
            password="Alice@1234",
            confirm_password="Alice@1234"
        )
        user_service.create_user(db, payload)

        with pytest.raises(HTTPException) as exc:
            user_service.create_user(db, payload)
        assert exc.value.status_code == 400

    def test_get_user_by_id_not_found(self, db):
        """Non-existent user raises 404."""
        with pytest.raises(HTTPException) as exc:
            user_service.get_user_by_id(db, 99999)
        assert exc.value.status_code == 404

    def test_list_users_pagination(self, db):
        """Pagination returns correct slice."""
        from app.models.user import User
        from app.core.security import hash_password

        # Create 15 users
        for i in range(15):
            db.add(User(
                name=f"User {i}",
                email=f"user{i}@example.com",
                password_hash=hash_password("Test@1234"),
                role="user"
            ))
        db.commit()

        result = user_service.list_users(db, page=1, limit=10)
        assert result["total"] == 15
        assert len(result["users"]) == 10

        result2 = user_service.list_users(db, page=2, limit=10)
        assert len(result2["users"]) == 5