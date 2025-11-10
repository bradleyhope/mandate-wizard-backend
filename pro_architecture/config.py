import os

class Settings:
    # External services
    PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
    PINECONE_INDEX   = os.environ.get("PINECONE_INDEX", "mandate-wizard")  # Default to mandate-wizard
    PINECONE_REGION  = os.environ.get("PINECONE_REGION", "us-east-1")

    NEO4J_URI        = os.environ["NEO4J_URI"]
    NEO4J_USER       = os.environ.get("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD   = os.environ["NEO4J_PASSWORD"]

    OPENAI_API_KEY   = os.environ.get("OPENAI_API_KEY", "")
    COHERE_API_KEY   = os.environ.get("COHERE_API_KEY", "")

    # Embeddings
    EMBEDDER         = os.environ.get("EMBEDDER", "openai")  # openai | local
    EMBEDDING_MODEL  = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")

    # Reranker
    RERANKER         = os.environ.get("RERANKER", "cohere")  # none | cohere | local | onnx
    RERANK_TOP_K     = int(os.environ.get("RERANK_TOP_K", "40"))  # top-K before rerank
    RERANK_RETURN    = int(os.environ.get("RERANK_RETURN", "12")) # final K after rerank

    # Retrieval
    TOP_K_VECTOR     = int(os.environ.get("TOP_K_VECTOR", "30"))
    M_Q_EXPANSIONS   = int(os.environ.get("M_Q_EXPANSIONS", "2"))  # multi-query expansion count
    USE_MMR          = os.environ.get("USE_MMR", "1") == "1"

    # Caching
    QUERY_CACHE_TTL  = int(os.environ.get("QUERY_CACHE_TTL", "1800"))
    QUERY_CACHE_MAX  = int(os.environ.get("QUERY_CACHE_MAX", "500"))
    EMBED_CACHE_TTL  = int(os.environ.get("EMBED_CACHE_TTL", "3600"))
    EMBED_CACHE_MAX  = int(os.environ.get("EMBED_CACHE_MAX", "2000"))

    # Synthesis
    COMPLETIONS_MODEL = os.environ.get("COMPLETIONS_MODEL", "gpt-4o-mini")
    MAX_TOKENS        = int(os.environ.get("MAX_TOKENS", "750"))

S = Settings()
