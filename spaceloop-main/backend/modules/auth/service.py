"""
SpaceLoop Authentication Service Layer
Handles user registration, credential authentication, and session identity.
"""

from typing import Optional, Dict, Any
from models import db, User
from backend.modules.auth.validators import validate_registration_input, validate_login_input
from backend.modules.auth.schemas import AuthResult


class AuthService:
    """Service providing core identity and authentication operations."""

    @staticmethod
    def register(name: str, email: str, password: str, role: str = 'seeker') -> AuthResult:
        """Registers a new platform user with hashed credentials."""
        name = name.strip() if name else ""
        email = email.strip().lower() if email else ""
        role = role.strip().lower() if role else "seeker"

        is_valid, err = validate_registration_input(name, email, password, role)
        if not is_valid:
            return AuthResult(success=False, error=err, status_code=400)

        existing = User.query.filter_by(email=email).first()
        if existing:
            return AuthResult(
                success=False,
                error=f"An account with email '{email}' already exists. Please log in.",
                status_code=400
            )

        new_user = User(
            name=name,
            email=email,
            role=role,
            objective_trust_score=85.0
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        return AuthResult(
            success=True,
            user=new_user.to_dict(),
            status_code=201
        )

    @staticmethod
    def authenticate(email: str, password: str) -> AuthResult:
        """Verifies credentials and returns user profile if authenticated."""
        email = email.strip().lower() if email else ""

        is_valid, err = validate_login_input(email, password)
        if not is_valid:
            return AuthResult(success=False, error=err, status_code=400)

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return AuthResult(
                success=False,
                error="Invalid email or password. Please try again.",
                status_code=401
            )

        return AuthResult(
            success=True,
            user=user.to_dict(),
            status_code=200
        )

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Loads User instance by database primary key."""
        if not user_id:
            return None
        return User.query.get(user_id)

    @staticmethod
    def get_demo_user(role: str = 'seeker') -> Optional[User]:
        """Finds primary seeded demo user for the specified role."""
        target_role = 'owner' if role in ['owner', 'host'] else 'seeker'
        if target_role == 'owner':
            return User.query.filter_by(email="sunita.rao@blrspaces.in").first() or User.query.filter_by(role='owner').first()
        return User.query.filter_by(email="rohit@iitd.ac.in").first() or User.query.filter_by(role='seeker').first()
