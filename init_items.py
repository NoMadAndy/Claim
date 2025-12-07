#!/usr/bin/env python3
"""
Initialize default items in the database.
Run this script after database setup to create default game items.
"""

from app.database import SessionLocal
from app.services.item_service import initialize_default_items

if __name__ == "__main__":
    print("Initializing default items...")
    db = SessionLocal()
    try:
        initialize_default_items(db)
        print("✅ Default items initialized successfully!")
    except Exception as e:
        print(f"❌ Error initializing items: {e}")
    finally:
        db.close()
