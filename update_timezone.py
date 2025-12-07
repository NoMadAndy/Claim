"""
Script to update all existing timestamps from UTC to CET
Run this ONCE after deploying the timezone changes
"""
import sys
from datetime import datetime, timezone, timedelta
import pytz

# Add app to path
sys.path.insert(0, '/workspaces/Claim')

from app.database import SessionLocal
from app.models import User, Log, Track, Spot

CET = pytz.timezone('Europe/Berlin')

def update_timestamps():
    db = SessionLocal()
    
    try:
        # Update User timestamps
        users = db.query(User).all()
        for user in users:
            if user.created_at and user.created_at.tzinfo is None:
                # Assume old times are UTC, convert to CET
                utc_time = user.created_at.replace(tzinfo=pytz.UTC)
                user.created_at = utc_time.astimezone(CET)
            if user.last_login and user.last_login.tzinfo is None:
                utc_time = user.last_login.replace(tzinfo=pytz.UTC)
                user.last_login = utc_time.astimezone(CET)
        
        # Update Log timestamps
        logs = db.query(Log).all()
        for log in logs:
            if log.timestamp and log.timestamp.tzinfo is None:
                utc_time = log.timestamp.replace(tzinfo=pytz.UTC)
                log.timestamp = utc_time.astimezone(CET)
        
        # Update Track timestamps
        tracks = db.query(Track).all()
        for track in tracks:
            if track.started_at and track.started_at.tzinfo is None:
                utc_time = track.started_at.replace(tzinfo=pytz.UTC)
                track.started_at = utc_time.astimezone(CET)
            if track.ended_at and track.ended_at.tzinfo is None:
                utc_time = track.ended_at.replace(tzinfo=pytz.UTC)
                track.ended_at = utc_time.astimezone(CET)
        
        # Update Spot timestamps
        spots = db.query(Spot).all()
        for spot in spots:
            if spot.created_at and spot.created_at.tzinfo is None:
                utc_time = spot.created_at.replace(tzinfo=pytz.UTC)
                spot.created_at = utc_time.astimezone(CET)
        
        db.commit()
        print("✅ All timestamps updated from UTC to CET!")
        print(f"   Updated {len(users)} users")
        print(f"   Updated {len(logs)} logs")
        print(f"   Updated {len(tracks)} tracks")
        print(f"   Updated {len(spots)} spots")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    update_timestamps()
