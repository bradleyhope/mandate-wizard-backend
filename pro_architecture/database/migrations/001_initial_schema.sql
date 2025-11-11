-- Initial schema for Mandate Wizard PostgreSQL System of Record
-- Migration: 001
-- Date: 2025-11-11
-- Description: Create entities, cards, relations, and events tables

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Entities table: Core data for people, companies, projects
CREATE TABLE IF NOT EXISTS entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    attributes JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    confidence_score FLOAT DEFAULT 0.5,
    verification_status VARCHAR(50) DEFAULT 'pending',
    source VARCHAR(100),
    demand_score INT DEFAULT 0,
    last_queried_at TIMESTAMP,
    query_count INT DEFAULT 0,
    search_vector tsvector,
    CONSTRAINT valid_entity_type CHECK (entity_type IN ('person', 'company', 'project')),
    CONSTRAINT valid_confidence CHECK (confidence_score BETWEEN 0.0 AND 1.0)
);

CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_slug ON entities(slug);
CREATE INDEX IF NOT EXISTS idx_entities_demand ON entities(demand_score DESC);
CREATE INDEX IF NOT EXISTS idx_entities_search ON entities USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS idx_entities_attributes ON entities USING GIN(attributes);

-- Cards table: Mandate cards, bio cards, contact cards, etc.
CREATE TABLE IF NOT EXISTS cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    card_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    confidence_score FLOAT DEFAULT 0.5,
    verification_status VARCHAR(50) DEFAULT 'pending',
    source VARCHAR(100),
    version INT DEFAULT 1,
    previous_version_id UUID REFERENCES cards(id),
    CONSTRAINT valid_card_type CHECK (card_type IN ('mandate', 'bio', 'contact', 'deal', 'process'))
);

CREATE INDEX IF NOT EXISTS idx_cards_entity ON cards(entity_id);
CREATE INDEX IF NOT EXISTS idx_cards_type ON cards(card_type);

-- Relations table: Relationships between entities
CREATE TABLE IF NOT EXISTS relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    to_entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    relation_type VARCHAR(50) NOT NULL,
    attributes JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    confidence_score FLOAT DEFAULT 0.5,
    CONSTRAINT no_self_relation CHECK (from_entity_id != to_entity_id),
    CONSTRAINT unique_relation UNIQUE (from_entity_id, to_entity_id, relation_type)
);

CREATE INDEX IF NOT EXISTS idx_relations_from ON relations(from_entity_id);
CREATE INDEX IF NOT EXISTS idx_relations_to ON relations(to_entity_id);
CREATE INDEX IF NOT EXISTS idx_relations_type ON relations(relation_type);

-- Events table: Audit trail and query signals
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id VARCHAR(50) UNIQUE NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    user_id VARCHAR(255),
    entity_id UUID REFERENCES entities(id),
    data JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT valid_event_type CHECK (event_type IN (
        'query_signal',
        'data_update_signal',
        'entity_created',
        'entity_updated',
        'entity_verified',
        'card_created',
        'card_updated'
    ))
);

CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_user ON events(user_id);
CREATE INDEX IF NOT EXISTS idx_events_entity ON events(entity_id);
CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at DESC);

-- Trigger to update search_vector on entities
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', 
        COALESCE(NEW.name, '') || ' ' || 
        COALESCE(NEW.attributes::text, '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS entities_search_vector_update ON entities;
CREATE TRIGGER entities_search_vector_update
BEFORE INSERT OR UPDATE ON entities
FOR EACH ROW
EXECUTE FUNCTION update_search_vector();

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS entities_updated_at ON entities;
CREATE TRIGGER entities_updated_at
BEFORE UPDATE ON entities
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS cards_updated_at ON cards;
CREATE TRIGGER cards_updated_at
BEFORE UPDATE ON cards
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS relations_updated_at ON relations;
CREATE TRIGGER relations_updated_at
BEFORE UPDATE ON relations
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();
