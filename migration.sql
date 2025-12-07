-- Migration: Add photo storage columns to logs table
-- This adds support for storing photos as BLOB data in the database

-- Add photo_data column (BYTEA for binary data)
ALTER TABLE logs ADD COLUMN IF NOT EXISTS photo_data BYTEA;

-- Add photo_mime column (for MIME type like 'image/jpeg', 'image/png', etc.)
ALTER TABLE logs ADD COLUMN IF NOT EXISTS photo_mime VARCHAR(50);

-- Add notes column (for log notes/description)
ALTER TABLE logs ADD COLUMN IF NOT EXISTS notes TEXT;

-- Verify the columns were added
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'logs';
