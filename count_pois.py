#!/usr/bin/env python3
"""
Helper script to count POIs in the database.
Returns the count to stdout for use in shell scripts.
"""
import sys
from app.database import SessionLocal
from app.models import Spot

def count_pois():
    """Count total number of spots in the database"""
    try:
        db = SessionLocal()
        count = db.query(Spot).count()
        db.close()
        return count
    except Exception as e:
        # Return 0 on error to trigger import
        sys.stderr.write(f"Warning: Could not count POIs: {e}\n")
        return 0

if __name__ == "__main__":
    count = count_pois()
    print(count)
    sys.exit(0)
