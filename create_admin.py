#!/usr/bin/env python3
"""
Script to create an admin user for Claim GPS Game.
Run this after the app has initialized the database.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models import User, UserRole
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin(username: str, email: str, password: str):
    """Create an admin user"""
    db = SessionLocal()
    try:
        # Check if user already exists
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"[error] User '{username}' already exists!")
            return False
        
        # Hash password
        hashed_pw = pwd_context.hash(password)
        
        # Create admin user
        admin = User(
            username=username,
            email=email,
            hashed_password=hashed_pw,
            role=UserRole.ADMIN,
            level=1,
            xp=0,
            total_claim_points=0
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print(f"[success] Admin user '{username}' created successfully!")
        print(f"  Email: {email}")
        print(f"  Role: {admin.role}")
        return True
        
    except Exception as e:
        print(f"[error] Failed to create admin user: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    import getpass
    
    print("=== Claim GPS Game - Admin User Creator ===\n")
    
    username = input("Enter admin username: ").strip()
    if not username:
        print("[error] Username cannot be empty!")
        sys.exit(1)
    
    email = input("Enter admin email: ").strip()
    if not email or "@" not in email:
        print("[error] Invalid email!")
        sys.exit(1)
    
    password = getpass.getpass("Enter admin password: ")
    password_confirm = getpass.getpass("Confirm password: ")
    
    if password != password_confirm:
        print("[error] Passwords do not match!")
        sys.exit(1)
    
    if len(password) < 8:
        print("[warn] Password is short (< 8 chars). Continue? (y/n): ", end="")
        if input().lower() != "y":
            sys.exit(1)
    
    if create_admin(username, email, password):
        sys.exit(0)
    else:
        sys.exit(1)
