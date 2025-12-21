#!/usr/bin/env python3
"""
Migration script to add spot type columns to the spots table.
Adds: spot_type, xp_multiplier, claim_multiplier, icon_name
"""

import sys
from app.database import SessionLocal, engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Run the migration to add spot type columns"""
    db = SessionLocal()
    
    try:
        logger.info("Starting migration: Adding spot type columns to spots table")
        
        # Check if we're using PostgreSQL or SQLite
        from app.config import settings
        
        if settings.is_postgresql():
            logger.info("Using PostgreSQL")
            
            # Add spot_type enum type first
            try:
                db.execute(text("""
                    CREATE TYPE spottype AS ENUM (
                        'STANDARD', 'CHURCH', 'SIGHT', 'SPORTS_FACILITY', 'PLAYGROUND',
                        'MONUMENT', 'MUSEUM', 'CASTLE', 'PARK', 'VIEWPOINT',
                        'HISTORIC', 'CULTURAL', 'RELIGIOUS', 'TOWNHALL', 'MARKET',
                        'FOUNTAIN', 'STATUE'
                    );
                """))
                db.commit()
                logger.info("Created SpotType enum")
            except Exception as e:
                logger.info(f"SpotType enum might already exist: {e}")
                db.rollback()
            
            # Add columns with proper types
            migration_sql = """
            -- Add spot_type column
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'spots' AND column_name = 'spot_type'
                ) THEN
                    ALTER TABLE spots ADD COLUMN spot_type spottype DEFAULT 'STANDARD' NOT NULL;
                    CREATE INDEX idx_spots_spot_type ON spots(spot_type);
                END IF;
            END $$;
            
            -- Add xp_multiplier column
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'spots' AND column_name = 'xp_multiplier'
                ) THEN
                    ALTER TABLE spots ADD COLUMN xp_multiplier DOUBLE PRECISION DEFAULT 1.0;
                END IF;
            END $$;
            
            -- Add claim_multiplier column
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'spots' AND column_name = 'claim_multiplier'
                ) THEN
                    ALTER TABLE spots ADD COLUMN claim_multiplier DOUBLE PRECISION DEFAULT 1.0;
                END IF;
            END $$;
            
            -- Add icon_name column
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'spots' AND column_name = 'icon_name'
                ) THEN
                    ALTER TABLE spots ADD COLUMN icon_name VARCHAR(100);
                END IF;
            END $$;
            """
            
        else:
            logger.info("Using SQLite")
            
            # SQLite doesn't support ALTER TABLE ADD COLUMN IF NOT EXISTS directly
            # We need to check column existence manually
            migration_sql = """
            -- Note: SQLite doesn't support IF NOT EXISTS for ALTER TABLE
            -- This will fail if columns already exist, which is fine
            """
            
            # Check and add columns one by one for SQLite
            try:
                db.execute(text("ALTER TABLE spots ADD COLUMN spot_type TEXT DEFAULT 'standard' NOT NULL"))
                logger.info("Added spot_type column")
            except Exception as e:
                logger.info(f"spot_type column might already exist: {e}")
                db.rollback()
            
            try:
                db.execute(text("ALTER TABLE spots ADD COLUMN xp_multiplier REAL DEFAULT 1.0"))
                logger.info("Added xp_multiplier column")
            except Exception as e:
                logger.info(f"xp_multiplier column might already exist: {e}")
                db.rollback()
            
            try:
                db.execute(text("ALTER TABLE spots ADD COLUMN claim_multiplier REAL DEFAULT 1.0"))
                logger.info("Added claim_multiplier column")
            except Exception as e:
                logger.info(f"claim_multiplier column might already exist: {e}")
                db.rollback()
            
            try:
                db.execute(text("ALTER TABLE spots ADD COLUMN icon_name TEXT"))
                logger.info("Added icon_name column")
            except Exception as e:
                logger.info(f"icon_name column might already exist: {e}")
                db.rollback()
            
            try:
                db.execute(text("CREATE INDEX IF NOT EXISTS idx_spots_spot_type ON spots(spot_type)"))
                logger.info("Created index on spot_type")
            except Exception as e:
                logger.info(f"Index might already exist: {e}")
                db.rollback()
            
            db.commit()
            logger.info("SQLite migration completed")
            return
        
        # Execute PostgreSQL migration
        if settings.is_postgresql():
            db.execute(text(migration_sql))
            db.commit()
            logger.info("PostgreSQL migration completed successfully")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    try:
        run_migration()
        logger.info("✅ Migration completed successfully!")
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)
