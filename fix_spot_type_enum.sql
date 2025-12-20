-- Migration: Fix SpotType Enum Case Mismatch
-- Purpose: Update the spottype enum from lowercase to uppercase values
-- Author: GitHub Copilot
-- Date: 2025-12-20
--
-- This migration fixes the issue where SQLAlchemy expects uppercase enum values
-- but the database was created with lowercase values.
--
-- IMPORTANT: This migration should be run on PostgreSQL databases only.
-- For SQLite, no action is needed (enums are stored as TEXT).

-- Step 1: Convert the spot_type column to TEXT temporarily
ALTER TABLE spots ALTER COLUMN spot_type TYPE TEXT;

-- Step 2: Update all existing values to uppercase
UPDATE spots SET spot_type = UPPER(spot_type) WHERE spot_type IS NOT NULL;

-- Step 3: Drop the old enum type
DROP TYPE IF EXISTS spottype CASCADE;

-- Step 4: Create the new enum type with uppercase values
CREATE TYPE spottype AS ENUM (
    'STANDARD', 
    'CHURCH', 
    'SIGHT', 
    'SPORTS_FACILITY', 
    'PLAYGROUND',
    'MONUMENT', 
    'MUSEUM', 
    'CASTLE', 
    'PARK', 
    'VIEWPOINT',
    'HISTORIC', 
    'CULTURAL', 
    'RELIGIOUS', 
    'TOWNHALL', 
    'MARKET',
    'FOUNTAIN', 
    'STATUE'
);

-- Step 5: Convert the column back to the enum type
ALTER TABLE spots ALTER COLUMN spot_type TYPE spottype USING spot_type::spottype;

-- Step 6: Set the default value
ALTER TABLE spots ALTER COLUMN spot_type SET DEFAULT 'STANDARD';

-- Step 7: Recreate the index
DROP INDEX IF EXISTS idx_spots_spot_type;
CREATE INDEX idx_spots_spot_type ON spots(spot_type);

-- Verification query: Check that all values are now uppercase
-- SELECT spot_type, COUNT(*) FROM spots GROUP BY spot_type ORDER BY spot_type;
