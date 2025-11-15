-- Migration 004: Add Priority Scoring Fields (v2 - Safe)
-- Date: 2025-11-15
-- Description: Add priority_score, scope, and seniority fields to entities table
-- This version handles existing columns and constraints gracefully

-- Step 1: Add new columns (will skip if already exist)
DO $$ 
BEGIN
    -- Add priority_score column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='entities' AND column_name='priority_score') THEN
        ALTER TABLE entities ADD COLUMN priority_score INTEGER DEFAULT 50;
        RAISE NOTICE 'Added priority_score column';
    ELSE
        RAISE NOTICE 'priority_score column already exists, skipping';
    END IF;
    
    -- Add scope column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='entities' AND column_name='scope') THEN
        ALTER TABLE entities ADD COLUMN scope VARCHAR(20) DEFAULT 'local';
        RAISE NOTICE 'Added scope column';
    ELSE
        RAISE NOTICE 'scope column already exists, skipping';
    END IF;
    
    -- Add seniority column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='entities' AND column_name='seniority') THEN
        ALTER TABLE entities ADD COLUMN seniority VARCHAR(20) DEFAULT 'unknown';
        RAISE NOTICE 'Added seniority column';
    ELSE
        RAISE NOTICE 'seniority column already exists, skipping';
    END IF;
    
    -- Add last_embedded column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='entities' AND column_name='last_embedded') THEN
        ALTER TABLE entities ADD COLUMN last_embedded TIMESTAMP;
        RAISE NOTICE 'Added last_embedded column';
    ELSE
        RAISE NOTICE 'last_embedded column already exists, skipping';
    END IF;
END $$;

-- Step 2: Add constraints (will skip if already exist)
DO $$ 
BEGIN
    -- Add priority_score constraint
    IF NOT EXISTS (SELECT 1 FROM information_schema.constraint_column_usage 
                   WHERE constraint_name='valid_priority_score') THEN
        ALTER TABLE entities ADD CONSTRAINT valid_priority_score 
            CHECK (priority_score BETWEEN 0 AND 100);
        RAISE NOTICE 'Added valid_priority_score constraint';
    ELSE
        RAISE NOTICE 'valid_priority_score constraint already exists, skipping';
    END IF;
    
    -- Add scope constraint
    IF NOT EXISTS (SELECT 1 FROM information_schema.constraint_column_usage 
                   WHERE constraint_name='valid_scope') THEN
        ALTER TABLE entities ADD CONSTRAINT valid_scope 
            CHECK (scope IN ('global', 'regional', 'local'));
        RAISE NOTICE 'Added valid_scope constraint';
    ELSE
        RAISE NOTICE 'valid_scope constraint already exists, skipping';
    END IF;
    
    -- Add seniority constraint
    IF NOT EXISTS (SELECT 1 FROM information_schema.constraint_column_usage 
                   WHERE constraint_name='valid_seniority') THEN
        ALTER TABLE entities ADD CONSTRAINT valid_seniority 
            CHECK (seniority IN ('c-suite', 'vp', 'director', 'manager', 'unknown'));
        RAISE NOTICE 'Added valid_seniority constraint';
    ELSE
        RAISE NOTICE 'valid_seniority constraint already exists, skipping';
    END IF;
END $$;

-- Step 3: Create indexes (will skip if already exist)
CREATE INDEX IF NOT EXISTS idx_entities_priority ON entities(priority_score DESC);
CREATE INDEX IF NOT EXISTS idx_entities_scope ON entities(scope);
CREATE INDEX IF NOT EXISTS idx_entities_seniority ON entities(seniority);
CREATE INDEX IF NOT EXISTS idx_entities_last_embedded ON entities(last_embedded);

-- Step 4: Add comments
DO $$ 
BEGIN
    COMMENT ON COLUMN entities.priority_score IS 'Priority score (0-100) based on seniority, scope, demand, and completeness';
    COMMENT ON COLUMN entities.scope IS 'Scope of influence: global, regional, or local';
    COMMENT ON COLUMN entities.seniority IS 'Seniority level: c-suite, vp, director, manager, or unknown';
    COMMENT ON COLUMN entities.last_embedded IS 'Timestamp of last embedding generation for Pinecone';
    RAISE NOTICE 'Added column comments';
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Could not add comments (table may not exist), continuing...';
END $$;

-- Final status check
DO $$ 
DECLARE
    col_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO col_count
    FROM information_schema.columns 
    WHERE table_name='entities' 
    AND column_name IN ('priority_score', 'scope', 'seniority', 'last_embedded');
    
    IF col_count = 4 THEN
        RAISE NOTICE '✅ Migration successful! All 4 columns present.';
    ELSE
        RAISE WARNING '⚠️ Migration incomplete. Only % of 4 columns present.', col_count;
    END IF;
END $$;
