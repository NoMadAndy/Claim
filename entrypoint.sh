#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database..."
until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; do
  sleep 1
done
echo "Database is ready!"

# Run migrations
echo "Running spot types migration..."
python3 migrate_spot_types.py || echo "Migration may have already been run"

# Check if POIs already exist
echo "Checking for existing POIs..."
POI_COUNT=$(python3 -c "
from app.database import SessionLocal
from app.models import Spot
db = SessionLocal()
count = db.query(Spot).count()
db.close()
print(count)
" 2>/dev/null || echo "0")

if [ "$POI_COUNT" -lt 100 ]; then
    echo "No POIs found (count: $POI_COUNT). Starting automatic import..."
    echo "This may take 5-10 minutes..."
    python3 import_bavaria_pois.py || echo "POI import failed, continuing..."
else
    echo "POIs already exist (count: $POI_COUNT). Skipping import."
fi

# Start the application
echo "Starting Claim GPS Game API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
