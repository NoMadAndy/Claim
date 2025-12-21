#!/usr/bin/env python3
"""
Migration script to fix the SpotType enum case mismatch.

The issue: PostgreSQL enum was created with lowercase values ('standard', 'church', etc.)
but SQLAlchemy expects uppercase enum member names (STANDARD, CHURCH, etc.) when using
native PostgreSQL enums.

This script:
1. Drops the existing enum type
2. Recreates it with uppercase values
3. Updates all existing data to use uppercase values
"""

import sys
import logging
from sqlalchemy import text
from app.database import SessionLocal, engine
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Run the migration to fix SpotType enum"""
    
    if not settings.is_postgresql():
        logger.info("This migration is only for PostgreSQL. Skipping for SQLite.")
        return
    
    db = SessionLocal()
    
    try:
        logger.info("Starting migration: Fixing SpotType enum case mismatch")
        
        # Convert the column to TEXT temporarily
        logger.info("Converting spot_type column to TEXT...")
        db.execute(text("""
            ALTER TABLE spots 
            ALTER COLUMN spot_type TYPE TEXT;
        """))
        db.commit()
        
        # Update all values to uppercase
        logger.info("Updating all spot_type values to uppercase...")
        db.execute(text("""
            UPDATE spots 
            SET spot_type = UPPER(spot_type)
            WHERE spot_type IS NOT NULL;
        """))
        db.commit()
        
        # Drop the old enum type
        logger.info("Dropping old spottype enum...")
        db.execute(text("DROP TYPE IF EXISTS spottype CASCADE;"))
        db.commit()
        
        # Create new enum with uppercase values
        logger.info("Creating new spottype enum with uppercase values...")
        db.execute(text("""
            CREATE TYPE spottype AS ENUM (
                'STANDARD', 'CHURCH', 'SIGHT', 'SPORTS_FACILITY', 'PLAYGROUND',
                'MONUMENT', 'MUSEUM', 'CASTLE', 'PARK', 'VIEWPOINT',
                'HISTORIC', 'CULTURAL', 'RELIGIOUS', 'TOWNHALL', 'MARKET',
                'FOUNTAIN', 'STATUE'
            );
        """))
        db.commit()
        
        # Convert the column back to the enum type
        logger.info("Converting spot_type column back to spottype enum...")
        db.execute(text("""
            ALTER TABLE spots 
            ALTER COLUMN spot_type TYPE spottype USING spot_type::spottype;
        """))
        db.commit()
        
        # Set the default value
        logger.info("Setting default value...")
        db.execute(text("""
            ALTER TABLE spots 
            ALTER COLUMN spot_type SET DEFAULT 'STANDARD';
        """))
        db.commit()
        
        # Recreate the index
        logger.info("Recreating index on spot_type...")
        db.execute(text("""
            DROP INDEX IF EXISTS idx_spots_spot_type;
            CREATE INDEX idx_spots_spot_type ON spots(spot_type);
        """))
        db.commit()
        
        logger.info("✅ Migration completed successfully!")
        logger.info("SpotType enum now uses uppercase values matching SQLAlchemy expectations")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)
