-- Rollback: Fix SpotType Enum Case Mismatch
-- Purpose: Rollback the uppercase enum changes to lowercase (if needed)
-- Author: GitHub Copilot
-- Date: 2025-12-20
--
-- WARNING: Only use this if you need to rollback the fix_spot_type_enum.sql migration
-- This should rarely be needed.

-- Step 1: Convert the spot_type column to TEXT temporarily
ALTER TABLE spots ALTER COLUMN spot_type TYPE TEXT;

-- Step 2: Update all existing values to lowercase
UPDATE spots SET spot_type = LOWER(spot_type) WHERE spot_type IS NOT NULL;

-- Step 3: Drop the uppercase enum type
DROP TYPE IF EXISTS spottype CASCADE;

-- Step 4: Recreate the enum type with lowercase values (original)
CREATE TYPE spottype AS ENUM (
    'standard', 
    'church', 
    'sight', 
    'sports_facility', 
    'playground',
    'monument', 
    'museum', 
    'castle', 
    'park', 
    'viewpoint',
    'historic', 
    'cultural', 
    'religious', 
    'townhall', 
    'market',
    'fountain', 
    'statue'
);

-- Step 5: Convert the column back to the enum type
ALTER TABLE spots ALTER COLUMN spot_type TYPE spottype USING spot_type::spottype;

-- Step 6: Set the default value
ALTER TABLE spots ALTER COLUMN spot_type SET DEFAULT 'standard';

-- Step 7: Recreate the index
DROP INDEX IF EXISTS idx_spots_spot_type;
CREATE INDEX idx_spots_spot_type ON spots(spot_type);

-- Verification query: Check that all values are now lowercase
-- SELECT spot_type, COUNT(*) FROM spots GROUP BY spot_type ORDER BY spot_type;
