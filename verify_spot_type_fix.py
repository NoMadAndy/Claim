#!/usr/bin/env python3
"""
Verification script to check if the SpotType enum fix has been applied correctly.

This script checks:
1. Python enum has correct structure (lowercase values, uppercase names)
2. PostgreSQL enum has uppercase values
3. Existing data has been converted to uppercase
"""

import sys
import logging
from sqlalchemy import text
from app.database import SessionLocal
from app.config import settings
from app.models import SpotType, Spot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_python_enum():
    """Verify Python enum structure"""
    logger.info("Checking Python SpotType enum...")
    
    issues = []
    
    for spot_type in SpotType:
        # Check that name is uppercase
        if spot_type.name != spot_type.name.upper():
            issues.append(f"  ❌ {spot_type.name} should be uppercase")
        
        # Check that value is lowercase
        expected_value = spot_type.name.lower()
        if spot_type.value != expected_value:
            issues.append(f"  ❌ {spot_type.name}.value should be '{expected_value}', got '{spot_type.value}'")
    
    if issues:
        logger.error("Python enum has issues:")
        for issue in issues:
            logger.error(issue)
        return False
    
    logger.info(f"✅ Python enum is correct ({len(list(SpotType))} types)")
    return True


def verify_postgresql_enum():
    """Verify PostgreSQL enum values"""
    if not settings.is_postgresql():
        logger.info("⏭️  Skipping PostgreSQL enum check (not using PostgreSQL)")
        return True
    
    logger.info("Checking PostgreSQL spottype enum...")
    
    db = SessionLocal()
    try:
        # Query the enum values from PostgreSQL
        result = db.execute(text("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = 'spottype'::regtype 
            ORDER BY enumlabel;
        """))
        
        db_enum_values = [row[0] for row in result]
        
        if not db_enum_values:
            logger.error("❌ spottype enum not found in database")
            return False
        
        logger.info(f"Database enum values: {db_enum_values}")
        
        # Check that all values are uppercase
        uppercase_values = set(e.name for e in SpotType)
        db_values_set = set(db_enum_values)
        
        if db_values_set != uppercase_values:
            logger.error("❌ Database enum values don't match expected uppercase values")
            logger.error(f"  Expected: {sorted(uppercase_values)}")
            logger.error(f"  Got:      {sorted(db_values_set)}")
            
            missing = uppercase_values - db_values_set
            extra = db_values_set - uppercase_values
            
            if missing:
                logger.error(f"  Missing from database: {sorted(missing)}")
            if extra:
                logger.error(f"  Extra in database: {sorted(extra)}")
            
            return False
        
        logger.info(f"✅ PostgreSQL enum has correct uppercase values ({len(db_enum_values)} types)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error checking PostgreSQL enum: {e}")
        return False
    finally:
        db.close()


def verify_spot_data():
    """Verify that existing spot data uses uppercase values"""
    logger.info("Checking existing spot data...")
    
    db = SessionLocal()
    try:
        # Query spots and check their spot_type values
        spots = db.query(Spot).limit(100).all()
        
        if not spots:
            logger.info("⏭️  No spots in database to check")
            return True
        
        logger.info(f"Checking {len(spots)} spots...")
        
        issues = []
        spot_types_found = set()
        
        for spot in spots:
            spot_types_found.add(spot.spot_type)
            
            # Verify it's a valid SpotType
            if not isinstance(spot.spot_type, SpotType):
                issues.append(f"  ❌ Spot {spot.id}: spot_type is not a SpotType enum: {spot.spot_type}")
        
        if issues:
            logger.error("Issues found in spot data:")
            for issue in issues:
                logger.error(issue)
            return False
        
        logger.info(f"✅ All spots have valid SpotType values")
        logger.info(f"   SpotTypes found: {sorted([st.name for st in spot_types_found])}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error checking spot data: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    """Run all verification checks"""
    logger.info("=" * 70)
    logger.info("SpotType Enum Fix Verification")
    logger.info("=" * 70)
    
    results = {
        "Python Enum": verify_python_enum(),
        "PostgreSQL Enum": verify_postgresql_enum(),
        "Spot Data": verify_spot_data(),
    }
    
    logger.info("=" * 70)
    logger.info("Verification Results:")
    logger.info("=" * 70)
    
    all_passed = True
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"  {check:20s}: {status}")
        if not passed:
            all_passed = False
    
    logger.info("=" * 70)
    
    if all_passed:
        logger.info("✅ All verifications passed! The fix is working correctly.")
        return 0
    else:
        logger.error("❌ Some verifications failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
