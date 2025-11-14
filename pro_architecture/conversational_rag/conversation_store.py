"""
Conversation Store - Database access layer for conversational RAG
Phase 1: Gemini-optimized version with semantic similarity
"""

import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import numpy as np

@dataclass
class ConversationTurn:
    """Represents a single turn in a conversation"""
    turn_number: int
    user_query: str
    answer: str
    question_type: Optional[str] = None
    rewritten_query: Optional[str] = None
    response_strategy: Optional[str] = None
    quality_score: Optional[float] = None
    repetition_score: Optional[float] = None
    entities_mentioned: List[str] = None
    new_entities_count: int = 0
    response_time_ms: Optional[int] = None
    
    def __post_init__(self):
        if self.entities_mentioned is None:
            self.entities_mentioned = []

@dataclass
class ConversationState:
    """Multi-layer conversation memory"""
    working_memory: Dict = None  # Last 1-2 turns
    short_term_memory: List[Dict] = None  # Last 3-5 turns
    long_term_memory: Dict = None  # Entire conversation
    covered_entities: List[str] = None
    covered_topics: List[str] = None
    entity_graph: Dict = None
    current_depth: int = 1
    
    def __post_init__(self):
        if self.working_memory is None:
            self.working_memory = {}
        if self.short_term_memory is None:
            self.short_term_memory = []
        if self.long_term_memory is None:
            self.long_term_memory = {}
        if self.covered_entities is None:
            self.covered_entities = []
        if self.covered_topics is None:
            self.covered_topics = []
        if self.entity_graph is None:
            self.entity_graph = {}


class ConversationStore:
    """Database access layer for conversational RAG"""
    
    def __init__(self, pg_client):
        self.pg = pg_client
    
    # ========================================================================
    # CONVERSATION MANAGEMENT
    # ========================================================================
    
    def create_conversation(self, user_id: str, session_id: str, user_goal: Optional[str] = None) -> str:
        """Create a new conversation"""
        query = """
            INSERT INTO conversations (user_id, session_id, user_goal)
            VALUES (%s, %s, %s)
            RETURNING id::text
        """
        result = self.pg.execute(query, (user_id, session_id, user_goal))
        conversation_id = result[0]['id']
        
        # Initialize conversation state
        self._initialize_state(conversation_id)
        
        return conversation_id
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Get conversation with all turns"""
        query = """
            SELECT c.*,
                   COALESCE(json_agg(
                       json_build_object(
                           'turn_number', ct.turn_number,
                           'user_query', ct.user_query,
                           'answer', ct.answer,
                           'question_type', ct.question_type,
                           'response_strategy', ct.response_strategy,
                           'quality_score', ct.quality_score,
                           'repetition_score', ct.repetition_score,
                           'entities_mentioned', ct.entities_mentioned
                       ) ORDER BY ct.turn_number
                   ) FILTER (WHERE ct.id IS NOT NULL), '[]') AS turns
            FROM conversations c
            LEFT JOIN conversation_turns ct ON c.id = ct.conversation_id
            WHERE c.id = %s::uuid
            GROUP BY c.id
        """
        result = self.pg.execute(query, (conversation_id,))
        
        if not result:
            return None
        
        row = result[0]
        return {
            'id': str(row[0]),
            'user_id': row[1],
            'session_id': row[2],
            'user_goal': row[3],
            'inferred_goal': row[4],
            'started_at': row[6],
            'last_active_at': row[7],
            'status': row[9],
            'total_turns': row[10],
            'avg_quality_score': row[11],
            'turns': json.loads(row[14]) if isinstance(row[14], str) else row[14]
        }
    
    def update_conversation_goal(self, conversation_id: str, inferred_goal: str, confidence: float):
        """Update inferred goal"""
        query = """
            UPDATE conversations
            SET inferred_goal = %s, goal_confidence = %s, updated_at = NOW()
            WHERE id = %s::uuid
        """
        self.pg.execute(query, (inferred_goal, confidence, conversation_id))
    
    def end_conversation(self, conversation_id: str, goal_achieved: bool = False):
        """Mark conversation as ended"""
        query = """
            UPDATE conversations
            SET ended_at = NOW(), status = 'completed', goal_achieved = %s, updated_at = NOW()
            WHERE id = %s::uuid
        """
        self.pg.execute(query, (goal_achieved, conversation_id))
    
    # ========================================================================
    # TURN MANAGEMENT
    # ========================================================================
    
    def add_turn(
        self,
        conversation_id: str,
        turn: ConversationTurn,
        query_embedding: Optional[List[float]] = None,
        answer_embedding: Optional[List[float]] = None
    ) -> int:
        """Add a new turn to the conversation"""
        query = """
            INSERT INTO conversation_turns (
                conversation_id, turn_number, user_query, user_query_embedding,
                answer, answer_embedding, question_type, rewritten_query,
                response_strategy, quality_score, repetition_score,
                entities_mentioned, new_entities_count, response_time_ms
            ) VALUES (
                %s::uuid, %s, %s, %s::vector,
                %s, %s::vector, %s, %s,
                %s, %s, %s,
                %s::jsonb, %s, %s
            )
            RETURNING id
        """
        
        result = self.pg.execute(query, (
            conversation_id,
            turn.turn_number,
            turn.user_query,
            json.dumps(query_embedding) if query_embedding else None,
            turn.answer,
            json.dumps(answer_embedding) if answer_embedding else None,
            turn.question_type,
            turn.rewritten_query,
            turn.response_strategy,
            turn.quality_score,
            turn.repetition_score,
            json.dumps(turn.entities_mentioned),
            turn.new_entities_count,
            turn.response_time_ms
        ))
        
        return result[0]['id']
    
    def get_recent_turns(self, conversation_id: str, limit: int = 5) -> List[ConversationTurn]:
        """Get recent turns for context"""
        query = """
            SELECT turn_number, user_query, answer, question_type, rewritten_query,
                   response_strategy, quality_score, repetition_score,
                   entities_mentioned, new_entities_count, response_time_ms
            FROM conversation_turns
            WHERE conversation_id = %s::uuid
            ORDER BY turn_number DESC
            LIMIT %s
        """
        result = self.pg.execute(query, (conversation_id, limit))
        
        turns = []
        for row in result:
            turns.append(ConversationTurn(
                turn_number=row[0],
                user_query=row[1],
                answer=row[2],
                question_type=row[3],
                rewritten_query=row[4],
                response_strategy=row[5],
                quality_score=row[6],
                repetition_score=row[7],
                entities_mentioned=row[8] if row[8] else [],
                new_entities_count=row[9] or 0,
                response_time_ms=row[10]
            ))
        
        return list(reversed(turns))  # Return in chronological order
    
    def get_previous_answer_embeddings(self, conversation_id: str, limit: int = 5) -> List[List[float]]:
        """Get embeddings of previous answers for semantic similarity"""
        query = """
            SELECT answer_embedding
            FROM conversation_turns
            WHERE conversation_id = %s::uuid
            AND answer_embedding IS NOT NULL
            ORDER BY turn_number DESC
            LIMIT %s
        """
        result = self.pg.execute(query, (conversation_id, limit))
        
        embeddings = []
        for row in result:
            if row[0]:
                # Parse vector string to list of floats
                embedding_str = row[0].strip('[]')
                embedding = [float(x) for x in embedding_str.split(',')]
                embeddings.append(embedding)
        
        return embeddings
    
    # ========================================================================
    # STATE MANAGEMENT (Multi-Layer Memory)
    # ========================================================================
    
    def _initialize_state(self, conversation_id: str):
        """Initialize conversation state"""
        query = """
            INSERT INTO conversation_state (conversation_id)
            VALUES (%s::uuid)
            ON CONFLICT (conversation_id) DO NOTHING
        """
        self.pg.execute(query, (conversation_id,))
    
    def get_state(self, conversation_id: str) -> ConversationState:
        """Get conversation state"""
        query = """
            SELECT working_memory, short_term_memory, long_term_memory,
                   covered_entities, covered_topics, entity_graph, current_depth
            FROM conversation_state
            WHERE conversation_id = %s::uuid
        """
        result = self.pg.execute(query, (conversation_id,))
        
        if not result:
            self._initialize_state(conversation_id)
            return ConversationState()
        
        row = result[0]
        return ConversationState(
            working_memory=row[0] or {},
            short_term_memory=row[1] or [],
            long_term_memory=row[2] or {},
            covered_entities=row[3] or [],
            covered_topics=row[4] or [],
            entity_graph=row[5] or {},
            current_depth=row[6] or 1
        )
    
    def update_state(self, conversation_id: str, state: ConversationState):
        """Update conversation state"""
        query = """
            UPDATE conversation_state
            SET working_memory = %s::jsonb,
                short_term_memory = %s::jsonb,
                long_term_memory = %s::jsonb,
                covered_entities = %s::jsonb,
                covered_topics = %s::jsonb,
                entity_graph = %s::jsonb,
                current_depth = %s,
                updated_at = NOW()
            WHERE conversation_id = %s::uuid
        """
        self.pg.execute(query, (
            json.dumps(state.working_memory),
            json.dumps(state.short_term_memory),
            json.dumps(state.long_term_memory),
            json.dumps(state.covered_entities),
            json.dumps(state.covered_topics),
            json.dumps(state.entity_graph),
            state.current_depth,
            conversation_id
        ))
    
    # ========================================================================
    # ENTITY COVERAGE TRACKING
    # ========================================================================
    
    def track_entity_mention(
        self,
        conversation_id: str,
        entity_id: str,
        entity_name: str,
        entity_type: str,
        turn_number: int,
        facts: List[str] = None,
        relationships: Dict = None
    ):
        """Track entity mention"""
        query = """
            INSERT INTO entity_coverage (
                conversation_id, entity_id, entity_name, entity_type,
                first_mentioned_turn, last_mentioned_turn, mention_count,
                facts_covered, relationship_context
            ) VALUES (
                %s::uuid, %s, %s, %s, %s, %s, 1,
                %s::jsonb, %s::jsonb
            )
            ON CONFLICT (conversation_id, entity_id) DO UPDATE
            SET last_mentioned_turn = %s,
                mention_count = entity_coverage.mention_count + 1,
                facts_covered = %s::jsonb,
                relationship_context = %s::jsonb,
                updated_at = NOW()
        """
        facts_json = json.dumps(facts or [])
        relationships_json = json.dumps(relationships or {})
        
        self.pg.execute(query, (
            conversation_id, entity_id, entity_name, entity_type,
            turn_number, turn_number,
            facts_json, relationships_json,
            turn_number, facts_json, relationships_json
        ))
    
    def get_entity_coverage(self, conversation_id: str) -> List[Dict]:
        """Get all entities covered in conversation"""
        query = """
            SELECT entity_id, entity_name, entity_type, mention_count,
                   first_mentioned_turn, last_mentioned_turn,
                   facts_covered, relationship_context
            FROM entity_coverage
            WHERE conversation_id = %s::uuid
            ORDER BY mention_count DESC
        """
        result = self.pg.execute(query, (conversation_id,))
        
        entities = []
        for row in result:
            entities.append({
                'entity_id': row[0],
                'entity_name': row[1],
                'entity_type': row[2],
                'mention_count': row[3],
                'first_mentioned_turn': row[4],
                'last_mentioned_turn': row[5],
                'facts_covered': row[6] or [],
                'relationships': row[7] or {}
            })
        
        return entities
    
    # ========================================================================
    # USER FEEDBACK
    # ========================================================================
    
    def add_feedback(
        self,
        conversation_id: str,
        turn_number: Optional[int],
        feedback_type: str,
        feedback_value: float,
        comment: Optional[str] = None,
        implicit_signals: Optional[Dict] = None,
        action_taken: Optional[str] = None
    ):
        """Add user feedback"""
        query = """
            INSERT INTO user_feedback (
                conversation_id, turn_number, feedback_type, feedback_value,
                feedback_comment, implicit_signals, action_taken
            ) VALUES (
                %s::uuid, %s, %s, %s, %s, %s::jsonb, %s
            )
        """
        self.pg.execute(query, (
            conversation_id, turn_number, feedback_type, feedback_value,
            comment, json.dumps(implicit_signals or {}), action_taken
        ))
    
    def get_feedback_stats(self, conversation_id: str) -> Dict:
        """Get feedback statistics for conversation"""
        query = """
            SELECT
                COUNT(*) AS total_feedback,
                AVG(CASE WHEN feedback_value > 0.5 THEN 1.0 ELSE 0.0 END) AS positive_rate,
                AVG(feedback_value) AS avg_rating
            FROM user_feedback
            WHERE conversation_id = %s::uuid
        """
        result = self.pg.execute(query, (conversation_id,))
        
        if not result:
            return {'total_feedback': 0, 'positive_rate': 0.0, 'avg_rating': 0.0}
        
        row = result[0]
        return {
            'total_feedback': row[0] or 0,
            'positive_rate': float(row[1] or 0.0),
            'avg_rating': float(row[2] or 0.0)
        }
    
    # ========================================================================
    # SEMANTIC SIMILARITY HELPERS
    # ========================================================================
    
    @staticmethod
    def cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def calculate_semantic_repetition(
        self,
        current_embedding: List[float],
        previous_embeddings: List[List[float]]
    ) -> float:
        """Calculate semantic repetition score"""
        if not previous_embeddings:
            return 0.0
        
        similarities = [
            self.cosine_similarity(current_embedding, prev_emb)
            for prev_emb in previous_embeddings
        ]
        
        return max(similarities) if similarities else 0.0
