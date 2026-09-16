"""
SpaceLoop Users Service Layer
Handles user profile retrieval, verification status, and reputation score updates.
"""

from typing import Optional, Dict, Any
from models import db, User


class UsersService:
    """Service providing user management operations."""

    @staticmethod
    def get_user(user_id: int) -> Optional[User]:
        return User.query.get(user_id)

    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        if not email:
            return None
        return User.query.filter_by(email=email.strip().lower()).first()

    @staticmethod
    def update_profile(user_id: int, **kwargs) -> Optional[User]:
        user = User.query.get(user_id)
        if not user:
            return None

        allowed_fields = {'name', 'college_name', 'college_email', 'discom_provider'}
        for key, val in kwargs.items():
            if key in allowed_fields and hasattr(user, key):
                setattr(user, key, val)

        db.session.commit()
        return user
