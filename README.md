> # Mandate Wizard V5
> 
> Your expert guide to pitching film & TV projects at Netflix. V5 introduces a high-performance streaming architecture to handle complex, long-running queries with a seamless user experience.

---

## Overview

Mandate Wizard is a sophisticated RAG (Retrieval-Augmented Generation) application designed to provide producers, writers, and development executives with instant, accurate, and actionable insights into Netflix's content needs. By leveraging a hybrid search system combining vector, graph, and full-text search, it delivers precise answers to complex queries about executive mandates, regional strategies, and content acquisition priorities.

Version 5 marks a significant architectural enhancement, replacing the traditional request-response model with a high-performance streaming backend. This ensures that the application remains responsive and provides continuous feedback to the user, even when handling complex queries that require significant processing time.

### Key Features

- **Hybrid RAG Engine:** Combines Pinecone vector search for semantic understanding, Neo4j graph search for relationship mapping, and full-text search for keyword precision.
- **Streaming Responses:** Real-time, chunk-by-chunk answer generation for a seamless, interactive user experience.
- **Comprehensive Persona Testing:** Validated against 12 distinct user personas to ensure accuracy and relevance across a wide range of query types.
- **Task 1A/1B Data Integration:** Enriches answers with executive quotes and recently greenlit projects for deeper context.
- **Dynamic Follow-up Questions:** Provides contextual suggestions to guide users toward deeper insights.
- **External Resource Links:** Connects users with LinkedIn profiles and industry coverage for further research.

---

## V5 Streaming Architecture

The core innovation in V5 is the migration to a streaming architecture using Server-Sent Events (SSE). This was implemented to address potential timeouts and provide a more interactive user experience for queries that take longer than 30 seconds to process.

### How It Works

1.  **Frontend Request:** The user's query is sent to the `/ask_stream` endpoint.
2.  **Backend Processing:** The Flask backend initiates the Hybrid RAG Engine's `query_with_streaming` method.
3.  **Real-time Status Updates:** The backend immediately begins sending `status` events to the frontend, indicating the current processing stage (e.g., "Classifying intent...", "Searching graph database...").
4.  **Chunk-by-Chunk Answer Streaming:** As the language model generates the answer, it is broken down into `chunk` events and streamed to the frontend, where it is progressively rendered.
5.  **Enriched Data Events:** Follow-up questions (`followups`) and external resource links (`resources`) are sent as separate events.
6.  **Completion Signal:** A `done` event is sent to signal the end of the stream.

This architecture ensures that the user receives immediate feedback and sees the answer appear in real-time, dramatically improving the perceived performance and user experience.

---

## Getting Started

### Prerequisites

- Python 3.11+
- Pip for package management
- Access to a Neo4j database
- Pinecone API key
- OpenAI API key

### Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd mandate_wizard_web_app
    ```

2.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Set environment variables:**

    Create a `.env` file in the root directory and add the following:

    ```
    PINECONE_API_KEY=your_pinecone_api_key
    PINECONE_INDEX_NAME=your_pinecone_index_name
    NEO4J_URI=your_neo4j_uri
    NEO4J_USER=your_neo4j_user
    NEO4J_PASSWORD=your_neo4j_password
    OPENAI_API_KEY=your_openai_api_key
    ```

### Running the Application

To start the Flask development server:

```bash
python3 app.py
```

The application will be available at `http://localhost:5000`.

---

## Testing

A comprehensive testing framework is included to validate the application's functionality across 12 user personas.

To run the tests:

```bash
python3 test_comprehensive.py
```

Test results are saved to `/home/ubuntu/mandate_wizard_test_results.json`.

---

*Mandate Wizard V5 - Your expert guide to pitching Netflix.*
