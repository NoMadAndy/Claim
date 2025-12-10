-- Migration: Add is_active columns to users and spots tables
-- This adds the is_active flag to enable/disable users and spots

-- Add is_active column to users table (default: true, meaning active)
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

-- Add is_active column to spots table (default: true, meaning active)
ALTER TABLE spots ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

-- Verify the columns were added
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users' ORDER BY ordinal_position;
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'spots' ORDER BY ordinal_position;
