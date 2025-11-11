-- Migration 002: Add more entity types
-- Date: 2025-11-11
-- Description: Expand entity_type constraint to support production_company, platform, etc.

-- Drop the old constraint
ALTER TABLE entities DROP CONSTRAINT IF EXISTS valid_entity_type;

-- Add new constraint with all entity types
ALTER TABLE entities ADD CONSTRAINT valid_entity_type 
CHECK (entity_type IN (
    'person', 
    'company', 
    'project', 
    'production_company', 
    'platform',
    'deal',
    'genre',
    'format'
));
