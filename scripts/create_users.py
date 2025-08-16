#!/usr/bin/env python3
"""
Script to create initial users for the WIP reporting tool
"""
import sys
import os

# Add the parent directory to the path so we can import our app
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash


def create_users():
    """Create initial users for the WIP reporting tool"""

    # User data - usernames are email addresses, all with password "123456"
    users_data = [
        {
            "username": "kulike@muehlhan.com",
            "email": "kulike@muehlhan.com",
            "role": "viewer",
        },
        {
            "username": "mueler-arends@muehlhan.com",
            "email": "mueler-arends@muehlhan.com",
            "role": "viewer",
        },
        {
            "username": "brockman@muehlhan.com",
            "email": "brockman@muehlhan.com",
            "role": "viewer",
        },
        {
            "username": "paulb@gototsi.com",
            "email": "paulb@gototsi.com",
            "role": "viewer",
        },
        {
            "username": "evans@muehlhan.com",
            "email": "evans@muehlhan.com",
            "role": "viewer",
        },
        {
            "username": "walz@muehlhan.com",
            "email": "walz@muehlhan.com",
            "role": "viewer",
        },
        {
            "username": "zaczeniuk@muehlhan.com",
            "email": "zaczeniuk@muehlhan.com",
            "role": "viewer",
        },
        {
            "username": "nedal@muehlhan.com",
            "email": "nedal@muehlhan.com",
            "role": "viewer",
        },
        {
            "username": "hell@muehlhan.com",
            "email": "hell@muehlhan.com",
            "role": "viewer",
        },
        {
            "username": "dahern@gototsi.com",
            "email": "dahern@gototsi.com",
            "role": "admin",
        },
    ]

    password = "123456"
    hashed_password = get_password_hash(password)

    db = SessionLocal()
    try:
        for user_data in users_data:
            # Check if user already exists
            existing_user = (
                db.query(User).filter(User.username == user_data["username"]).first()
            )
            if existing_user:
                print(f"User {user_data['username']} already exists, skipping...")
                continue

            # Create new user
            db_user = User(
                username=user_data["username"],
                email=user_data["email"],
                role=user_data["role"],
                password_hash=hashed_password,
                is_active=True,
            )

            db.add(db_user)
            print(f"Created user: {user_data['username']} ({user_data['role']})")

        db.commit()
        print(f"\n✅ Successfully created users!")
        print(f"📝 All users have password: {password}")
        print(f"👨‍💼 Admin: dahern@gototsi.com")
        print(f"👀 Viewers: All other users")

    except Exception as e:
        print(f"❌ Error creating users: {e}")
        db.rollback()
    finally:
        db.close()


def list_users():
    """List all users in the database"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print(f"\n📋 Current users in database:")
        print(f"{'Email/Username':<30} {'Role':<10}")
        print("-" * 45)
        for user in users:
            print(f"{user.username:<30} {user.role:<10}")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        list_users()
    else:
        create_users()
        list_users()
