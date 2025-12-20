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
if ! python3 migrate_spot_types.py 2>&1 | tee -a /tmp/migration.log; then
    echo "Warning: Migration command returned non-zero exit code. This may be expected if migration was already applied."
    echo "Check /tmp/migration.log for details."
fi

# Check if POIs already exist
echo "Checking for existing POIs..."
POI_COUNT=$(python3 count_pois.py 2>&1)

if [ "$POI_COUNT" -lt 100 ]; then
    echo "No POIs found (count: $POI_COUNT). Starting automatic import..."
    echo "This may take 5-10 minutes. Please be patient..."
    if ! python3 import_bavaria_pois.py 2>&1 | tee -a /tmp/poi_import.log; then
        echo "Error: POI import failed. Check /tmp/poi_import.log for details."
        echo "The application will start anyway. You can run the import manually later."
    else
        echo "POI import completed successfully!"
    fi
else
    echo "POIs already exist (count: $POI_COUNT). Skipping import."
fi

# Start the application
echo "Starting Claim GPS Game API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
