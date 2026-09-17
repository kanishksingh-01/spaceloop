#!/usr/bin/env python3
"""
SpaceLoop Server-Authorized Administrator Provisioning CLI.
Enforces administrative boundaries by provisioning admin accounts directly on the server
without exposing administrative privileges or registration switches to public HTTP endpoints.
"""

import sys
import os
import argparse
import getpass

# Add repository root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models import db, User
from backend.modules.auth.password import validate_password_complexity
from backend.modules.auth.audit import record_audit
from email_validator import validate_email, EmailNotValidError


def provision_admin(email: str, name: str, password: str) -> bool:
    app = create_app()
    with app.app_context():
        clean_email = email.strip().lower()
        try:
            valid = validate_email(clean_email, check_deliverability=False)
            clean_email = valid.normalized
        except EmailNotValidError as e:
            print(f"Error: Invalid email format ({str(e)})")
            return False

        is_valid, msg = validate_password_complexity(password)
        if not is_valid:
            print(f"Error: Insecure password ({msg})")
            return False

        name_parts = (name or "Platform Administrator").strip().split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else "Admin"

        user = User.query.filter(db.func.lower(User.email) == clean_email).first()
        if user:
            print(f"[*] Existing user found ({clean_email}). Promoting to Administrator...")
            user.is_admin = True
            user.is_active = True
            user.is_email_verified = True
            if password:
                user.set_password(password)
            if not user.first_name:
                user.first_name = first_name
                user.last_name = last_name
            db.session.commit()
            record_audit("AUTH_ADMIN_PROMOTED", user_id=user.id, details={"email": clean_email})
            print(f"[+] User {clean_email} successfully promoted to Administrator (User ID: {user.id}).")
            return True
        else:
            print(f"[*] Creating new Administrator account for {clean_email}...")
            user = User(
                name=f"{first_name} {last_name}".strip(),
                first_name=first_name,
                last_name=last_name,
                email=clean_email,
                role="owner",
                is_active=True,
                is_email_verified=True,
                is_admin=True,
                is_host_verified=True,
                upi_verified=True,
                objective_trust_score=100.0,
                bio="Platform System Administrator"
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            record_audit("AUTH_ADMIN_CREATED", user_id=user.id, details={"email": clean_email})
            print(f"[+] Administrator account {clean_email} successfully created (User ID: {user.id})!")
            return True


def main():
    parser = argparse.ArgumentParser(description="SpaceLoop Admin Provisioning Utility")
    parser.add_argument("--email", type=str, help="Administrator email address")
    parser.add_argument("--name", type=str, default="Platform Admin", help="Full name")
    parser.add_argument("--password", type=str, help="Password (optional, prompts securely if omitted)")
    parser.add_argument("--non-interactive", action="store_true", help="Fail if required fields are missing instead of prompting")

    args = parser.parse_args()

    email = args.email
    name = args.name
    password = args.password

    if not email:
        if args.non_interactive:
            print("Error: --email is required in non-interactive mode.", file=sys.stderr)
            sys.exit(1)
        email = input("Administrator Email: ").strip()

    if not email:
        print("Error: Email cannot be blank.", file=sys.stderr)
        sys.exit(1)

    if not password:
        if args.non_interactive:
            print("Error: --password is required in non-interactive mode.", file=sys.stderr)
            sys.exit(1)
        password = getpass.getpass("Password: ")
        confirm = getpass.getpass("Confirm Password: ")
        if password != confirm:
            print("Error: Passwords do not match.", file=sys.stderr)
            sys.exit(1)

    success = provision_admin(email, name, password)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
