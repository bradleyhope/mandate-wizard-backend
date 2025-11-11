-- Migration 003: Remove entity type constraint to allow all Neo4j node types
-- This enables importing all 40+ Neo4j node types (mandate, quote, process, greenlight, etc.)

-- Drop the restrictive entity type constraint
ALTER TABLE entities DROP CONSTRAINT IF EXISTS valid_entity_type;

-- Add a more permissive constraint that just ensures it's not null or empty
ALTER TABLE entities ADD CONSTRAINT valid_entity_type 
CHECK (entity_type IS NOT NULL AND entity_type != '');

-- Add index on entity_type for better query performance with many types
CREATE INDEX IF NOT EXISTS idx_entities_entity_type ON entities(entity_type);

-- Add comment explaining the change
COMMENT ON COLUMN entities.entity_type IS 'Type of entity - allows any non-empty string to support dynamic schema from Neo4j and other sources';
