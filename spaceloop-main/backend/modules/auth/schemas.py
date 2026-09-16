"""
Authentication Data Transfer Objects & Schemas
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class RegisterDTO:
    name: str
    email: str
    password: str
    role: str = 'seeker'
    college_name: Optional[str] = None
    college_email: Optional[str] = None


@dataclass
class LoginDTO:
    email: str
    password: str


@dataclass
class AuthResult:
    success: bool
    user: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    status_code: int = 200
