#!/bin/bash

# Migration Script für Claim-Datenbank
# Führt die is_active Spalten-Migration aus

set -e  # Exit on error

echo "================================"
echo "Claim Database Migration"
echo "================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "add_is_active_columns.sql" ]; then
    echo -e "${RED}Error: add_is_active_columns.sql not found!${NC}"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '#' | xargs)

# Check required variables
if [ -z "$DATABASE_URL" ] && [ -z "$DB_HOST" ]; then
    echo -e "${RED}Error: DATABASE_URL or DB_HOST not set in .env${NC}"
    exit 1
fi

echo -e "${YELLOW}Starting migration...${NC}"
echo ""

# Method 1: Using DATABASE_URL (if set)
if [ ! -z "$DATABASE_URL" ]; then
    echo "Using DATABASE_URL from .env"
    
    # Extract connection details from DATABASE_URL
    # Format: postgresql://user:password@host:port/database
    psql "$DATABASE_URL" -f add_is_active_columns.sql
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Migration completed successfully!${NC}"
    else
        echo -e "${RED}✗ Migration failed!${NC}"
        exit 1
    fi

# Method 2: Using individual connection parameters
elif [ ! -z "$DB_HOST" ]; then
    echo "Using DB connection parameters from .env"
    
    DB_USER="${DB_USER:-postgres}"
    DB_PASSWORD="${DB_PASSWORD:-}"
    DB_PORT="${DB_PORT:-5432}"
    DB_NAME="${DB_NAME:-claim_db}"
    
    # Use PGPASSWORD environment variable for authentication
    if [ ! -z "$DB_PASSWORD" ]; then
        export PGPASSWORD="$DB_PASSWORD"
    fi
    
    psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -p "$DB_PORT" -f add_is_active_columns.sql
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Migration completed successfully!${NC}"
    else
        echo -e "${RED}✗ Migration failed!${NC}"
        exit 1
    fi
fi

echo ""
echo "================================"
echo "Running Python migration script..."
echo "================================"
echo ""

# Also run the Python migration script if it exists
if [ -f "migrate_db.py" ]; then
    python3 migrate_db.py
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Python migration completed!${NC}"
    else
        echo -e "${YELLOW}⚠ Python migration had warnings${NC}"
    fi
fi

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}All migrations completed!${NC}"
echo -e "${GREEN}================================${NC}"
