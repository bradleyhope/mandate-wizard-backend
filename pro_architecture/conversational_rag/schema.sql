-- Phase 1: Conversational RAG Database Schema
-- Optimized for semantic similarity, multi-layer memory, and user feedback

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";  -- For semantic similarity

-- ============================================================================
-- CONVERSATIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    
    -- Goal tracking (free text for Phase 1, will become Mandate Graph in Phase 2)
    user_goal TEXT,
    inferred_goal TEXT,
    goal_confidence FLOAT DEFAULT 0.0,
    
    -- Conversation metadata
    started_at TIMESTAMP DEFAULT NOW(),
    last_active_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',  -- active, completed, abandoned
    
    -- Metrics
    total_turns INT DEFAULT 0,
    avg_quality_score FLOAT,
    goal_achieved BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_session_id ON conversations(session_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_last_active ON conversations(last_active_at DESC);

-- ============================================================================
-- CONVERSATION TURNS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS conversation_turns (
    id SERIAL PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    turn_number INT NOT NULL,
    
    -- User input
    user_query TEXT NOT NULL,
    user_query_embedding vector(1536),  -- For semantic similarity
    
    -- Query classification
    question_type VARCHAR(50),  -- DRILL_DOWN, EXPLORE_MORE, COMPARE, etc.
    rewritten_query TEXT,
    
    -- System response
    answer TEXT NOT NULL,
    answer_embedding vector(1536),  -- For semantic repetition detection
    response_strategy VARCHAR(50),  -- BREADTH, DEPTH, STRATEGIC_ADVICE, etc.
    
    -- Quality metrics
    quality_score FLOAT,
    specificity_score FLOAT,
    actionability_score FLOAT,
    strategic_value_score FLOAT,
    context_awareness_score FLOAT,
    novelty_score FLOAT,
    
    -- Repetition tracking
    repetition_score FLOAT,  -- Semantic similarity to previous turns
    regenerated BOOLEAN DEFAULT FALSE,
    
    -- Entities mentioned (for tracking coverage)
    entities_mentioned JSONB DEFAULT '[]',
    new_entities_count INT DEFAULT 0,
    
    -- Retrieval metadata
    documents_retrieved INT DEFAULT 0,
    web_search_triggered BOOLEAN DEFAULT FALSE,
    
    -- Timing
    response_time_ms INT,
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(conversation_id, turn_number)
);

CREATE INDEX idx_turns_conversation ON conversation_turns(conversation_id, turn_number);
CREATE INDEX idx_turns_answer_embedding ON conversation_turns USING ivfflat (answer_embedding vector_cosine_ops);
CREATE INDEX idx_turns_query_embedding ON conversation_turns USING ivfflat (user_query_embedding vector_cosine_ops);
CREATE INDEX idx_turns_entities ON conversation_turns USING gin (entities_mentioned);

-- ============================================================================
-- CONVERSATION STATE TABLE (Multi-Layer Memory)
-- ============================================================================
CREATE TABLE IF NOT EXISTS conversation_state (
    id SERIAL PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    
    -- Working memory (current focus - last 1-2 turns)
    working_memory JSONB DEFAULT '{}',
    
    -- Short-term memory (recent context - last 3-5 turns)
    short_term_memory JSONB DEFAULT '[]',
    
    -- Long-term memory (key facts - entire conversation)
    long_term_memory JSONB DEFAULT '{}',
    
    -- Entity coverage tracking
    covered_entities JSONB DEFAULT '[]',
    covered_topics JSONB DEFAULT '[]',
    
    -- Entity relationship graph
    entity_graph JSONB DEFAULT '{}',
    
    -- Conversation depth
    current_depth INT DEFAULT 1,
    max_depth_reached INT DEFAULT 1,
    
    -- Last updated
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(conversation_id)
);

CREATE INDEX idx_state_conversation ON conversation_state(conversation_id);
CREATE INDEX idx_state_covered_entities ON conversation_state USING gin (covered_entities);

-- ============================================================================
-- ENTITY COVERAGE TABLE (Detailed tracking per entity)
-- ============================================================================
CREATE TABLE IF NOT EXISTS entity_coverage (
    id SERIAL PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    entity_id VARCHAR(255) NOT NULL,
    entity_name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50),  -- person, company, platform, etc.
    
    -- Coverage tracking
    first_mentioned_turn INT,
    last_mentioned_turn INT,
    mention_count INT DEFAULT 1,
    
    -- Depth of coverage (for Phase 2 coverage ledger)
    facts_covered JSONB DEFAULT '[]',
    attributes_covered JSONB DEFAULT '[]',
    
    -- Context
    relationship_context JSONB DEFAULT '{}',  -- Related entities
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(conversation_id, entity_id)
);

CREATE INDEX idx_entity_coverage_conversation ON entity_coverage(conversation_id);
CREATE INDEX idx_entity_coverage_entity ON entity_coverage(entity_id);

-- ============================================================================
-- USER FEEDBACK TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_feedback (
    id SERIAL PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    turn_number INT,
    
    -- Explicit feedback
    feedback_type VARCHAR(20),  -- thumbs_up, thumbs_down, rating, comment
    feedback_value FLOAT,  -- 1.0 for thumbs_up, 0.0 for thumbs_down, 1-5 for rating
    feedback_comment TEXT,
    
    -- Implicit signals
    implicit_signals JSONB DEFAULT '{}',  -- dwell_time, scroll_depth, copy_paste, etc.
    
    -- User action tracking
    action_taken VARCHAR(50),  -- clicked_link, copied_text, exported, etc.
    goal_progress VARCHAR(20),  -- progressing, stuck, achieved
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_feedback_conversation ON user_feedback(conversation_id);
CREATE INDEX idx_feedback_type ON user_feedback(feedback_type);
CREATE INDEX idx_feedback_created ON user_feedback(created_at DESC);

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to update conversation last_active_at
CREATE OR REPLACE FUNCTION update_conversation_last_active()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations
    SET last_active_at = NOW(),
        total_turns = total_turns + 1,
        updated_at = NOW()
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_conversation_last_active
AFTER INSERT ON conversation_turns
FOR EACH ROW
EXECUTE FUNCTION update_conversation_last_active();

-- Function to calculate average quality score
CREATE OR REPLACE FUNCTION update_conversation_avg_quality()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations
    SET avg_quality_score = (
        SELECT AVG(quality_score)
        FROM conversation_turns
        WHERE conversation_id = NEW.conversation_id
        AND quality_score IS NOT NULL
    )
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_conversation_avg_quality
AFTER INSERT OR UPDATE ON conversation_turns
FOR EACH ROW
WHEN (NEW.quality_score IS NOT NULL)
EXECUTE FUNCTION update_conversation_avg_quality();

-- ============================================================================
-- VIEWS FOR ANALYTICS
-- ============================================================================

-- View: Conversation quality metrics
CREATE OR REPLACE VIEW conversation_quality_metrics AS
SELECT
    c.id AS conversation_id,
    c.user_id,
    c.total_turns,
    c.avg_quality_score,
    c.goal_achieved,
    c.status,
    AVG(ct.repetition_score) AS avg_repetition,
    AVG(ct.novelty_score) AS avg_novelty,
    COUNT(DISTINCT jsonb_array_elements_text(ct.entities_mentioned)) AS unique_entities_mentioned,
    SUM(ct.new_entities_count) AS total_new_entities,
    COUNT(CASE WHEN uf.feedback_value > 0.5 THEN 1 END)::FLOAT / NULLIF(COUNT(uf.id), 0) AS positive_feedback_rate,
    EXTRACT(EPOCH FROM (c.last_active_at - c.started_at)) / 60 AS duration_minutes
FROM conversations c
LEFT JOIN conversation_turns ct ON c.id = ct.conversation_id
LEFT JOIN user_feedback uf ON c.id = uf.conversation_id
GROUP BY c.id;

-- View: Turn-over-turn quality progression
CREATE OR REPLACE VIEW quality_progression AS
SELECT
    conversation_id,
    turn_number,
    quality_score,
    novelty_score,
    repetition_score,
    quality_score - LAG(quality_score) OVER (PARTITION BY conversation_id ORDER BY turn_number) AS quality_delta,
    novelty_score - LAG(novelty_score) OVER (PARTITION BY conversation_id ORDER BY turn_number) AS novelty_delta
FROM conversation_turns
ORDER BY conversation_id, turn_number;

-- ============================================================================
-- SAMPLE QUERIES FOR TESTING
-- ============================================================================

-- Get conversation with all turns
-- SELECT c.*, 
--        json_agg(ct ORDER BY ct.turn_number) AS turns
-- FROM conversations c
-- LEFT JOIN conversation_turns ct ON c.id = ct.conversation_id
-- WHERE c.id = 'conversation_uuid'
-- GROUP BY c.id;

-- Find similar queries (semantic search)
-- SELECT ct.user_query, ct.answer, 
--        1 - (ct.user_query_embedding <=> '[embedding_vector]'::vector) AS similarity
-- FROM conversation_turns ct
-- ORDER BY ct.user_query_embedding <=> '[embedding_vector]'::vector
-- LIMIT 10;

-- Get entity coverage for conversation
-- SELECT entity_name, mention_count, 
--        last_mentioned_turn - first_mentioned_turn AS span
-- FROM entity_coverage
-- WHERE conversation_id = 'conversation_uuid'
-- ORDER BY mention_count DESC;
