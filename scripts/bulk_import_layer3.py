#!/usr/bin/env python3
"""
Bulk Import Script: Layer 3 (Production Companies)

This script imports production company data from JSON into both Pinecone and Neo4j.

Usage:
    python3 bulk_import_layer3.py

Input File:
    /home/ubuntu/mandate_wizard_web_app/data/production_companies.json

Output:
    - Vectors in Pinecone namespace "production_companies"
    - Nodes in Neo4j with type ProductionCompany
    - Relationships: (Executive)-[:WORKS_WITH]->(ProductionCompany)
"""

import json
import os
import sys
from openai import OpenAI
import pinecone
from neo4j import GraphDatabase

# Configuration
DATA_FILE = "/home/ubuntu/mandate_wizard_web_app/data/production_companies.json"
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = "mandate-wizard"
PINECONE_NAMESPACE = "production_companies"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def load_data():
    """Load production companies from JSON file"""
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
    return data.get('production_companies', [])

def create_embedding_text(company):
    """Create text for embedding from company data"""
    text_parts = [
        f"{company['company_name']} is a production company based in {company['country']}.",
        f"Specializes in: {', '.join(company['specializations'])}."
    ]
    
    if company.get('netflix_relationship', {}).get('has_deal'):
        deal_info = company['netflix_relationship']
        text_parts.append(
            f"Has {deal_info.get('deal_type', 'a deal')} with Netflix since {deal_info.get('deal_year', 'unknown')}."
        )
        text_parts.append(
            f"Primary executive: {deal_info.get('primary_executive', 'unknown')}."
        )
    
    if company.get('notable_projects'):
        projects = [p['title'] for p in company['notable_projects'][:3]]
        text_parts.append(f"Notable productions: {', '.join(projects)}.")
    
    if company.get('submission_info', {}).get('submission_method'):
        text_parts.append(
            f"Submissions: {company['submission_info']['submission_method']}."
        )
    
    if company.get('notes'):
        text_parts.append(company['notes'])
    
    return " ".join(text_parts)

def import_to_pinecone(companies):
    """Import production companies to Pinecone"""
    print("\n" + "="*70)
    print("IMPORTING TO PINECONE")
    print("="*70)
    
    # Initialize OpenAI and Pinecone
    client = OpenAI()
    pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX)
    
    vectors = []
    for i, company in enumerate(companies):
        print(f"\nProcessing {i+1}/{len(companies)}: {company['company_name']}")
        
        # Create embedding text
        text = create_embedding_text(company)
        print(f"  Text: {text[:100]}...")
        
        # Generate embedding
        embedding = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        ).data[0].embedding
        
        # Prepare metadata
        metadata = {
            "company_name": company['company_name'],
            "country": company['country'],
            "specializations": company['specializations'],
            "has_netflix_deal": company.get('netflix_relationship', {}).get('has_deal', False),
            "deal_type": company.get('netflix_relationship', {}).get('deal_type', ''),
            "deal_year": company.get('netflix_relationship', {}).get('deal_year', 0),
            "primary_executive": company.get('netflix_relationship', {}).get('primary_executive', ''),
            "website": company.get('submission_info', {}).get('website', ''),
            "submission_method": company.get('submission_info', {}).get('submission_method', ''),
            "notes": company.get('notes', ''),
            "layer": "production_companies"
        }
        
        # Create vector ID
        vector_id = f"prodco_{company['company_name'].lower().replace(' ', '_')}"
        
        vectors.append({
            "id": vector_id,
            "values": embedding,
            "metadata": metadata
        })
        
        print(f"  ✅ Prepared vector: {vector_id}")
    
    # Batch upsert to Pinecone
    print(f"\n📤 Upserting {len(vectors)} vectors to Pinecone...")
    index.upsert(vectors=vectors, namespace=PINECONE_NAMESPACE)
    print(f"✅ Successfully imported {len(vectors)} production companies to Pinecone")

def import_to_neo4j(companies):
    """Import production companies to Neo4j"""
    print("\n" + "="*70)
    print("IMPORTING TO NEO4J")
    print("="*70)
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        for i, company in enumerate(companies):
            print(f"\nProcessing {i+1}/{len(companies)}: {company['company_name']}")
            
            # Create production company node
            session.run("""
                MERGE (pc:ProductionCompany {name: $name})
                SET pc.country = $country,
                    pc.specializations = $specializations,
                    pc.has_netflix_deal = $has_deal,
                    pc.deal_type = $deal_type,
                    pc.deal_year = $deal_year,
                    pc.website = $website,
                    pc.submission_method = $submission_method,
                    pc.notes = $notes
            """,
                name=company['company_name'],
                country=company['country'],
                specializations=company['specializations'],
                has_deal=company.get('netflix_relationship', {}).get('has_deal', False),
                deal_type=company.get('netflix_relationship', {}).get('deal_type', ''),
                deal_year=company.get('netflix_relationship', {}).get('deal_year', 0),
                website=company.get('submission_info', {}).get('website', ''),
                submission_method=company.get('submission_info', {}).get('submission_method', ''),
                notes=company.get('notes', '')
            )
            print(f"  ✅ Created ProductionCompany node")
            
            # Link to primary executive
            primary_exec = company.get('netflix_relationship', {}).get('primary_executive')
            if primary_exec:
                result = session.run("""
                    MATCH (e:Executive {name: $exec_name})
                    MATCH (pc:ProductionCompany {name: $company_name})
                    MERGE (e)-[r:WORKS_WITH]->(pc)
                    SET r.primary = true,
                        r.since = $since
                    RETURN e.name
                """,
                    exec_name=primary_exec,
                    company_name=company['company_name'],
                    since=company.get('netflix_relationship', {}).get('deal_year', 0)
                )
                
                if result.single():
                    print(f"  ✅ Linked to executive: {primary_exec}")
                else:
                    print(f"  ⚠️  Executive not found: {primary_exec}")
            
            # Link to secondary executives
            secondary_execs = company.get('netflix_relationship', {}).get('secondary_executives', [])
            for exec_name in secondary_execs:
                result = session.run("""
                    MATCH (e:Executive {name: $exec_name})
                    MATCH (pc:ProductionCompany {name: $company_name})
                    MERGE (e)-[r:WORKS_WITH]->(pc)
                    SET r.primary = false
                    RETURN e.name
                """,
                    exec_name=exec_name,
                    company_name=company['company_name']
                )
                
                if result.single():
                    print(f"  ✅ Linked to executive: {exec_name}")
                else:
                    print(f"  ⚠️  Executive not found: {exec_name}")
    
    driver.close()
    print(f"\n✅ Successfully imported {len(companies)} production companies to Neo4j")

def main():
    print("="*70)
    print("LAYER 3 BULK IMPORT: PRODUCTION COMPANIES")
    print("="*70)
    
    # Load data
    print("\n📂 Loading data from:", DATA_FILE)
    companies = load_data()
    print(f"✅ Loaded {len(companies)} production companies")
    
    if not companies:
        print("❌ No production companies found in file. Exiting.")
        sys.exit(1)
    
    # Import to Pinecone
    try:
        import_to_pinecone(companies)
    except Exception as e:
        print(f"\n❌ Error importing to Pinecone: {e}")
        sys.exit(1)
    
    # Import to Neo4j
    try:
        import_to_neo4j(companies)
    except Exception as e:
        print(f"\n❌ Error importing to Neo4j: {e}")
        sys.exit(1)
    
    # Summary
    print("\n" + "="*70)
    print("IMPORT COMPLETE")
    print("="*70)
    print(f"✅ {len(companies)} production companies imported successfully")
    print(f"📊 Pinecone namespace: {PINECONE_NAMESPACE}")
    print(f"📊 Neo4j node type: ProductionCompany")
    print("\nNext steps:")
    print("1. Verify data in Pinecone dashboard")
    print("2. Query Neo4j to verify relationships")
    print("3. Test queries in the web app")
    print("="*70)

if __name__ == "__main__":
    main()

