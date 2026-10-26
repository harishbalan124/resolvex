#!/usr/bin/env python3
"""
ResolveX CLI Script: Create Initial Administrator
Complies with Non-Negotiable Rule 3:
No default admin with a known password; create the first admin through a CLI script that prompts for the password.
"""
import argparse
import getpass
import os
import sys

# Ensure backend app is discoverable on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.database import SessionLocal, Base, engine
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.audit_log import AuditLog


def init_db():
    Base.metadata.create_all(bind=engine)


def create_admin(email: str, full_name: str, password: str) -> bool:
    init_db()
    db = SessionLocal()
    try:
        email = email.lower().strip()
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"[ERROR] User with email '{email}' already exists.")
            return False

        hashed_password = get_password_hash(password)
        admin = User(
            email=email,
            full_name=full_name.strip(),
            hashed_password=hashed_password,
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        audit = AuditLog(
            user_id=admin.id,
            action="INITIAL_ADMIN_CREATED_CLI",
            entity_type="user",
            entity_id=str(admin.id),
            details=f"Superadmin '{admin.email}' initialized via CLI setup script.",
            ip_address="127.0.0.1 (CLI)",
        )
        db.add(audit)
        db.commit()

        print("\n" + "="*50)
        print(" [SUCCESS] Administrator account successfully created!")
        print(f" ID:        {admin.id}")
        print(f" Full Name: {admin.full_name}")
        print(f" Email:     {admin.email}")
        print(f" Role:      {admin.role.value}")
        print("="*50 + "\n")
        return True
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="ResolveX - Create Initial Administrator")
    parser.add_argument("--email", help="Admin email address", default=None)
    parser.add_argument("--name", help="Admin full name", default=None)
    parser.add_argument("--password", help="Admin password (non-interactive)", default=None)

    args = parser.parse_args()

    print("\n--- ResolveX: Autonomous Dispute Resolution CLI Setup ---")
    print("Initialize system Administrator account.\n")

    email = args.email
    while not email or "@" not in email:
        email = input("Enter Admin Email: ").strip()
        if "@" not in email:
            print("Invalid email format. Please enter a valid email address.")

    full_name = args.name
    while not full_name:
        full_name = input("Enter Full Name: ").strip()

    password = args.password
    if not password:
        while True:
            password = getpass.getpass("Enter Admin Password (min 8 characters): ")
            if len(password) < 8:
                print("Password must be at least 8 characters long.")
                continue
            confirm = getpass.getpass("Confirm Admin Password: ")
            if password != confirm:
                print("Passwords do not match. Please try again.")
                continue
            break
    elif len(password) < 8:
        print("[ERROR] Password must be at least 8 characters.")
        sys.exit(1)

    success = create_admin(email, full_name, password)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
