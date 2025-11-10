#!/usr/bin/env python3
"""
Newsletter processing pipeline for Mandate Wizard.
- Fetches emails from Gmail
- Parses newsletters from key sources
- Extracts structured data
- Ingests to Pinecone + Neo4j
"""
import os
import base64
import json
from datetime import datetime, timedelta
from openai import OpenAI
from data_schemas import validate_card
from rag.embedder import get_embedder
from rag.retrievers.pinecone_retriever import PineconeRetriever
from rag.graph.dao import Neo4jDAO

# Initialize clients
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], base_url=\'https://api.openai.com/v1\')
embedder = get_embedder()
retriever = PineconeRetriever()
graph = Neo4jDAO()

NEWSLETTER_SOURCES = [
    "Hollywood Signal",
    "Deadline",
    "Variety",
    "The Ankler",
    "Puck",
    "The Wrap",
]

def fetch_emails(days=7):
    """Fetch recent emails from Gmail MCP."""
    import subprocess
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    query = f"after:{start_date.strftime(\"%Y/%m/%d\")} before:{end_date.strftime(\"%Y/%m/%d\")}"
    
    # Call Gmail MCP
    cmd = [
        "manus-mcp-cli", "tool", "call", "search_messages",
        "--server", "gmail",
        "--input", json.dumps({"query": query, "max_results": 100})
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error fetching emails: {result.stderr}")
        return []
    
    messages = json.loads(result.stdout)
    print(f"Fetched {len(messages)} messages from Gmail")
    return messages

def parse_newsletter(message):
    """Parse a single newsletter email."""
    snippet = message.get("snippet", "")
    payload = message.get("payload", {})
    headers = payload.get("headers", [])
    
    # Find sender
    sender = ""
    for h in headers:
        if h["name"] == "From":
            sender = h["value"]
            break
    
    # Check if it's a target newsletter
    is_target = any(source in sender for source in NEWSLETTER_SOURCES)
    if not is_target:
        return None
    
    # Get email body
    body_data = payload.get("body", {}).get("data", "")
    if body_data:
        body = base64.urlsafe_b64decode(body_data).decode("utf-8")
    else:
        # Handle multipart emails
        parts = payload.get("parts", [])
        for part in parts:
            if part["mimeType"] == "text/plain":
                body_data = part.get("body", {}).get("data", "")
                if body_data:
                    body = base64.urlsafe_b64decode(body_data).decode("utf-8")
                    break
    
    if not body:
        return None
    
    print(f"Parsing newsletter from: {sender}")
    return body

def extract_structured_data(content):
    """Use LLM to extract structured data from newsletter content."""
    prompt = f"""Extract structured data from this newsletter content. Identify the card type (executive, mandate, news, etc.) and extract all relevant fields based on the provided schemas. Return a list of JSON objects.

    Content:
    {content[:4000]}

    Schemas:
    - Executive: name, title, company, region, bio, mandate, etc.
    - Mandate: platform, department, summary, genres, etc.
    - News/Deal: title, date, platform, executives, etc.

    Return a list of JSON objects, one for each card found.
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.1,
        messages=[{"role":"system","content":"You are a data extraction expert."},{"role":"user","content":prompt}]
    )
    
    try:
        extracted_data = json.loads(response.choices[0].message.content)
        if isinstance(extracted_data, list):
            return extracted_data
        else:
            return [extracted_data]
    except Exception as e:
        print(f"Error parsing LLM response: {e}")
        return []

def ingest_card(card_data):
    """Validate and ingest a single card to Pinecone and Neo4j."""
    try:
        # Validate schema
        validated_data = validate_card(card_data)
        
        # Generate embedding
        text_to_embed = json.dumps(validated_data)
        embedding = embedder.embed(text_to_embed)
        
        # Ingest to Pinecone
        retriever.upsert(
            id=validated_data["id"],
            vector=embedding,
            metadata=validated_data
        )
        
        # Ingest to Neo4j (simplified)
        if validated_data["type"] == "executive":
            graph.upsert_person(validated_data["name"], validated_data["title"], validated_data["company"])
        elif validated_data["type"] == "company":
            graph.upsert_company(validated_data["name"])
        
        print(f"  Ingested card: {validated_data["id"]}")
        return True
    except Exception as e:
        print(f"  Error ingesting card: {e}")
        return False

def run_pipeline():
    """Run the full newsletter processing pipeline."""
    print("Starting newsletter processing pipeline...")
    
    # 1. Fetch emails
    messages = fetch_emails(days=7)
    
    # 2. Parse newsletters
    all_cards = []
    for msg in messages:
        content = parse_newsletter(msg)
        if content:
            # 3. Extract structured data
            cards = extract_structured_data(content)
            all_cards.extend(cards)
    
    print(f"Extracted {len(all_cards)} potential cards from newsletters")
    
    # 4. Ingest to database
    ingested_count = 0
    for card in all_cards:
        if ingest_card(card):
            ingested_count += 1
    
    print(f"Pipeline complete. Ingested {ingested_count} new/updated cards.")

if __name__ == "__main__":
    run_pipeline()
