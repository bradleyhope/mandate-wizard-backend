#!/usr/bin/env python3
"""
Import Senior Executive and Production Company Intelligence Data
Adds critical missing layers to Mandate Wizard
"""

import json
import os
from pinecone import Pinecone
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

# Initialize
print("Initializing...")

# Database credentials (from app.py)
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY', 'pcsk_2kvuLD_NLVH2XehCeitZUi3VCUJVkeH3KaceWniEE59Nh8f7GucxBNJDdg2eedfTaeYiD1')
PINECONE_INDEX_NAME = 'netflix-mandate-wizard'

NEO4J_URI = os.environ.get('NEO4J_URI', 'neo4j+s://0dd3462a.databases.neo4j.io')
NEO4J_USER = os.environ.get('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', 'cH-Jo3f9mcbbOr9ov-x22V7AQB3kOxxV42JJR55ZbMg')

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

neo4j_driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)

model = SentenceTransformer('all-MiniLM-L6-v2')

# Load data
print("Loading intelligence data...")
with open('data/senior_executives.json', 'r') as f:
    senior_exec_data = json.load(f)

with open('data/production_company_intelligence.json', 'r') as f:
    prodco_data = json.load(f)

# Import Senior Executives
print("\n=== Importing Senior Executives ===")
senior_execs = senior_exec_data['senior_executives']

vectors_to_upsert = []
neo4j_commands = []

for exec_data in senior_execs:
    name = exec_data['name']
    title = exec_data['title']
    
    print(f"Processing {name} ({title})...")
    
    # Create rich text for embedding
    mandate_text = f"""
    {name} - {title} at Netflix
    
    {exec_data['mandate']['overview']}
    
    Current Priorities:
    {chr(10).join(f"- {p}" for p in exec_data['mandate']['current_priorities'])}
    
    Recent Greenlights:
    {chr(10).join(f"- {g}" for g in exec_data['mandate']['recent_greenlights'])}
    
    Pitch Pathway: {exec_data['mandate']['pitch_pathway']}
    
    Decision Timeline: {exec_data['mandate']['decision_timeline']}
    
    Success Factors:
    {chr(10).join(f"- {s}" for s in exec_data['mandate']['success_factors'])}
    """
    
    # Generate embedding
    embedding = model.encode(mandate_text).tolist()
    
    # Prepare Pinecone vector
    vector_id = f"senior_exec_{name.lower().replace(' ', '_')}"
    vectors_to_upsert.append({
        'id': vector_id,
        'values': embedding,
        'metadata': {
            'type': 'senior_executive',
            'name': name,
            'title': title,
            'level': exec_data['level'],
            'scope': exec_data['scope'],
            'text': mandate_text[:1000]  # Truncate for metadata
        }
    })
    
    # Prepare Neo4j command
    neo4j_commands.append(f"""
    MERGE (e:Person {{name: "{name}"}})
    SET e.title = "{title}",
        e.level = "{exec_data['level']}",
        e.scope = "{exec_data['scope']}",
        e.is_senior_executive = true,
        e.decision_timeline = "{exec_data['mandate']['decision_timeline']}",
        e.pitch_pathway = "{exec_data['mandate']['pitch_pathway']}"
    """)

# Upsert to Pinecone
print(f"Upserting {len(vectors_to_upsert)} senior executive vectors to Pinecone...")
index.upsert(vectors=vectors_to_upsert, namespace='senior_executives')

# Import to Neo4j
print(f"Importing {len(neo4j_commands)} senior executives to Neo4j...")
with neo4j_driver.session() as session:
    for cmd in neo4j_commands:
        session.run(cmd)

# Import Competitive Intelligence
print("\n=== Importing Competitive Intelligence ===")
comp_intel = senior_exec_data['competitive_positioning']

comp_vectors = []
for competitor, data in comp_intel['netflix_vs_competitors'].items():
    comp_name = competitor.replace('vs_', '').replace('_', ' ').title()
    
    comp_text = f"""
    Netflix vs {comp_name}
    
    Netflix Advantages:
    {chr(10).join(f"- {a}" for a in data['netflix_advantages'])}
    
    {comp_name} Advantages:
    {chr(10).join(f"- {a}" for a in data[f"{competitor.split('_')[1]}_advantages"])}
    
    When to Choose Netflix: {data['when_to_choose_netflix']}
    """
    
    embedding = model.encode(comp_text).tolist()
    
    comp_vectors.append({
        'id': f"competitive_{competitor}",
        'values': embedding,
        'metadata': {
            'type': 'competitive_intelligence',
            'competitor': comp_name,
            'text': comp_text[:1000]
        }
    })

print(f"Upserting {len(comp_vectors)} competitive intelligence vectors...")
index.upsert(vectors=comp_vectors, namespace='competitive_intelligence')

# Import Timeline Intelligence
print("\n=== Importing Timeline Intelligence ===")
timeline_data = senior_exec_data['timeline_intelligence']

timeline_vectors = []
for project_type, timeline_info in timeline_data['by_project_type'].items():
    # Build timeline text based on available fields
    timeline_parts = [f"{project_type.replace('_', ' ').title()} Timeline at Netflix\n"]
    
    for key, value in timeline_info.items():
        field_name = key.replace('_', ' ').title()
        timeline_parts.append(f"{field_name}: {value}")
    
    timeline_text = "\n".join(timeline_parts)
    
    embedding = model.encode(timeline_text).tolist()
    
    timeline_vectors.append({
        'id': f"timeline_{project_type}",
        'values': embedding,
        'metadata': {
            'type': 'timeline_intelligence',
            'project_type': project_type,
            'text': timeline_text[:1000]
        }
    })

print(f"Upserting {len(timeline_vectors)} timeline intelligence vectors...")
index.upsert(vectors=timeline_vectors, namespace='timeline_intelligence')

# Import Production Company Intelligence
print("\n=== Importing Production Company Intelligence ===")
prodco_vectors = []

for genre, companies in prodco_data['production_companies_by_genre'].items():
    for company in companies:
        prodco_text = f"""
        {company['name']} - Production Company
        Principal: {company['principal']}
        Netflix Relationship: {company['netflix_relationship']}
        
        Genre Expertise: {genre.replace('_', ' ').title()}
        
        Track Record: {', '.join(company['track_record'])}
        Netflix Greenlights: {', '.join(company['netflix_greenlights'])}
        
        Why Strong: {company['why_strong']}
        """
        
        embedding = model.encode(prodco_text).tolist()
        
        prodco_vectors.append({
            'id': f"prodco_{company['name'].lower().replace(' ', '_')}_{genre}",
            'values': embedding,
            'metadata': {
                'type': 'production_company_intelligence',
                'name': company['name'],
                'genre': genre,
                'text': prodco_text[:1000]
            }
        })

print(f"Upserting {len(prodco_vectors)} production company intelligence vectors...")
index.upsert(vectors=prodco_vectors, namespace='production_company_intelligence')

# Import Packaging Best Practices
print("\n=== Importing Packaging Best Practices ===")
packaging_text = f"""
Netflix Packaging Best Practices

Essential Elements:
{chr(10).join(f"- {elem['element']}: {elem['guidance']}" for elem in prodco_data['packaging_best_practices']['essential_elements'])}

Common Mistakes to Avoid:
{chr(10).join(f"- {mistake}" for mistake in prodco_data['packaging_best_practices']['common_mistakes'])}

Success Formulas:
- Limited Series: {prodco_data['packaging_best_practices']['success_formula']['for_limited_series']}
- Drama Series: {prodco_data['packaging_best_practices']['success_formula']['for_drama_series']}
- Overall Deal: {prodco_data['packaging_best_practices']['success_formula']['for_overall_deal']}
"""

embedding = model.encode(packaging_text).tolist()

index.upsert(vectors=[{
    'id': 'packaging_best_practices',
    'values': embedding,
    'metadata': {
        'type': 'packaging_intelligence',
        'text': packaging_text[:1000]
    }
}], namespace='packaging_intelligence')

print("\n=== Import Complete ===")
print(f"✅ Senior Executives: {len(senior_execs)} imported")
print(f"✅ Competitive Intelligence: {len(comp_vectors)} vectors")
print(f"✅ Timeline Intelligence: {len(timeline_vectors)} vectors")
print(f"✅ Production Companies: {len(prodco_vectors)} vectors")
print(f"✅ Packaging Intelligence: 1 vector")

# Verify
print("\n=== Verification ===")
stats = index.describe_index_stats()
print(f"Total vectors in Pinecone: {stats.total_vector_count}")
for ns, count in stats.namespaces.items():
    print(f"  {ns}: {count.vector_count} vectors")

neo4j_driver.close()
print("\n✅ All intelligence data imported successfully!")
