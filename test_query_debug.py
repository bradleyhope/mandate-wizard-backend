import os
import sys

# Set environment variables
os.environ['MY_OPENAI_API_KEY'] = os.getenv('MY_OPENAI_API_KEY', '')
os.environ['PINECONE_API_KEY'] = os.getenv('PINECONE_API_KEY', '')
os.environ['NEO4J_URI'] = os.getenv('NEO4J_URI', '')
os.environ['NEO4J_USER'] = os.getenv('NEO4J_USER', '')
os.environ['NEO4J_PASSWORD'] = os.getenv('NEO4J_PASSWORD', '')

from hybridrag_engine_pinecone import HybridRAGEnginePinecone

# Initialize engine
print("Initializing engine...")
engine = HybridRAGEnginePinecone(
    pinecone_api_key=os.environ['PINECONE_API_KEY'],
    pinecone_index_name="netflix-mandate-wizard",
    neo4j_uri=os.environ['NEO4J_URI'],
    neo4j_user=os.environ['NEO4J_USER'],
    neo4j_password=os.environ['NEO4J_PASSWORD']
)

# Test query
question = "What are Netflix recent greenlights in crime thriller?"
print(f"\n=== Testing Query ===")
print(f"Question: {question}\n")

# Test individual components
print("1. Classifying intent...")
intent = engine.classify_intent(question)
print(f"   Intent: {intent}\n")

print("2. Extracting attributes...")
attributes = engine.extract_attributes(question)
print(f"   Attributes: {attributes}\n")

print("3. Querying Neo4j greenlights...")
neo4j_greenlights = engine.query_greenlights_from_neo4j(genre=attributes.get('genre'), limit=10)
print(f"   Found {len(neo4j_greenlights)} greenlights")
if neo4j_greenlights:
    print(f"   First greenlight: {neo4j_greenlights[0].get('title', 'N/A')}\n")

print("4. Running graph search...")
graph_results = engine.graph_search(question, attributes, intent=intent)
print(f"   Found {len(graph_results)} graph results\n")

print("5. Running vector search...")
vector_results = engine.vector_search(question, top_k=10)
print(f"   Found {len(vector_results['documents'])} vector results\n")

print("6. Fusing context...")
context = engine.fuse_context(graph_results, vector_results, intent, neo4j_greenlights=neo4j_greenlights)
print(f"   Context length: {len(context)} characters")
print(f"   Context preview (first 500 chars):\n{context[:500]}\n")

print("7. Generating answer...")
answer = engine.generate_answer(question, context, intent, session_id="test")
print(f"   Answer: {answer}\n")

