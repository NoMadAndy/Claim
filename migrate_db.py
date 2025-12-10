#!/usr/bin/env python3
"""
Manual database migration to add photo_data and photo_mime columns to logs table
"""

import sys
from sqlalchemy import text, inspect
from app.database import engine

def migrate():
    """Add missing columns to logs table and users table"""
    with engine.connect() as conn:
        # Check logs table columns
        inspector = inspect(engine)
        logs_columns = [col['name'] for col in inspector.get_columns('logs')]
        users_columns = [col['name'] for col in inspector.get_columns('users')]
        
        print("Current logs table columns:", logs_columns)
        print("Current users table columns:", users_columns)
        
        # Check if columns exist in logs
        if 'photo_data' not in logs_columns:
            print("Adding photo_data column...")
            conn.execute(text("ALTER TABLE logs ADD COLUMN photo_data BYTEA"))
            conn.commit()
            print("✓ photo_data column added")
        else:
            print("✓ photo_data column already exists")
        
        if 'photo_mime' not in logs_columns:
            print("Adding photo_mime column...")
            conn.execute(text("ALTER TABLE logs ADD COLUMN photo_mime VARCHAR(50)"))
            conn.commit()
            print("✓ photo_mime column added")
        else:
            print("✓ photo_mime column already exists")
        
        # Check if notes column exists (newer schema)
        if 'notes' not in logs_columns:
            print("Adding notes column...")
            conn.execute(text("ALTER TABLE logs ADD COLUMN notes TEXT"))
            conn.commit()
            print("✓ notes column added")
        else:
            print("✓ notes column already exists")
        
        # Check if heatmap_color column exists in users
        if 'heatmap_color' not in users_columns:
            print("Adding heatmap_color column...")
            conn.execute(text("ALTER TABLE users ADD COLUMN heatmap_color VARCHAR(7)"))
            conn.commit()
            print("✓ heatmap_color column added")
        else:
            print("✓ heatmap_color column already exists")
        
        print("\nMigration complete!")
        return True

if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"Error during migration: {e}", file=sys.stderr)
        sys.exit(1)
