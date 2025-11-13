#!/bin/bash
# Migration script for Conversational RAG schema

echo "🔄 Applying Conversational RAG schema migration..."

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL environment variable not set"
    exit 1
fi

# Apply schema
psql "$DATABASE_URL" -f schema.sql

if [ $? -eq 0 ]; then
    echo "✅ Conversational RAG schema migration completed successfully"
else
    echo "❌ Schema migration failed"
    exit 1
fi
