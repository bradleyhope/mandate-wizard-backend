-- Migration 004: Add Priority Scoring Fields
-- Date: 2025-11-15
-- Description: Add priority_score, scope, and seniority fields to entities table

-- Add new columns to entities table
ALTER TABLE entities
ADD COLUMN IF NOT EXISTS priority_score INTEGER DEFAULT 50,
ADD COLUMN IF NOT EXISTS scope VARCHAR(20) DEFAULT 'local',
ADD COLUMN IF NOT EXISTS seniority VARCHAR(20) DEFAULT 'unknown',
ADD COLUMN IF NOT EXISTS last_embedded TIMESTAMP;

-- Add constraints
ALTER TABLE entities
ADD CONSTRAINT valid_priority_score CHECK (priority_score BETWEEN 0 AND 100),
ADD CONSTRAINT valid_scope CHECK (scope IN ('global', 'regional', 'local')),
ADD CONSTRAINT valid_seniority CHECK (seniority IN ('c-suite', 'vp', 'director', 'manager', 'unknown'));

-- Create indexes for filtering and sorting
CREATE INDEX IF NOT EXISTS idx_entities_priority ON entities(priority_score DESC);
CREATE INDEX IF NOT EXISTS idx_entities_scope ON entities(scope);
CREATE INDEX IF NOT EXISTS idx_entities_seniority ON entities(seniority);
CREATE INDEX IF NOT EXISTS idx_entities_last_embedded ON entities(last_embedded);

-- Add comment
COMMENT ON COLUMN entities.priority_score IS 'Priority score (0-100) based on seniority, scope, demand, and completeness';
COMMENT ON COLUMN entities.scope IS 'Scope of influence: global, regional, or local';
COMMENT ON COLUMN entities.seniority IS 'Seniority level: c-suite, vp, director, manager, or unknown';
COMMENT ON COLUMN entities.last_embedded IS 'Timestamp of last embedding generation for Pinecone';
