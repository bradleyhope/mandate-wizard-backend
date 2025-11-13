"""
Conversational RAG - Main orchestrator
Phase 1: Gemini-optimized gold standard
"""

from typing import Dict, Optional
from .conversation_store import ConversationStore
from .conversation_manager import ConversationManager
from .progressive_engine import ProgressiveEngine, ResponseQuality


class ConversationalRAG:
    """Main interface for conversational RAG system"""
    
    def __init__(self, pg_client, rag_engine, llm_client, embedding_client):
        """
        Initialize conversational RAG
        
        Args:
            pg_client: PostgreSQL client
            rag_engine: RAG retrieval engine
            llm_client: LLM client for generation
            embedding_client: Embedding client for semantic similarity
        """
        self.store = ConversationStore(pg_client)
        self.manager = ConversationManager(self.store, llm_client)
        self.engine = ProgressiveEngine(self.store, rag_engine, llm_client, embedding_client)
    
    # ========================================================================
    # PUBLIC API
    # ========================================================================
    
    def start_conversation(
        self,
        user_id: str,
        session_id: str,
        initial_goal: Optional[str] = None
    ) -> str:
        """
        Start a new conversation
        
        Returns:
            conversation_id
        """
        conversation_id = self.store.create_conversation(user_id, session_id, initial_goal)
        return conversation_id
    
    def process_query(
        self,
        conversation_id: str,
        user_query: str
    ) -> Dict:
        """
        Process user query and generate progressively better answer
        
        Returns:
            {
                'answer': str,
                'turn_number': int,
                'quality': dict,
                'repetition_score': float,
                'metadata': dict
            }
        """
        # Create turn context
        context = self.manager.process_user_query(conversation_id, user_query)
        
        # Generate answer
        answer, quality, repetition_score = self.engine.generate_answer(context)
        
        return {
            'answer': answer,
            'turn_number': context.turn_number,
            'quality': quality.to_dict(),
            'repetition_score': repetition_score,
            'metadata': {
                'question_type': context.question_type.value,
                'response_strategy': context.response_strategy.value,
                'rewritten_query': context.rewritten_query,
                'entities_excluded': context.entities_to_exclude,
                'entities_included': context.entities_to_include
            }
        }
    
    def add_feedback(
        self,
        conversation_id: str,
        turn_number: Optional[int],
        feedback_type: str,
        feedback_value: float,
        comment: Optional[str] = None,
        implicit_signals: Optional[Dict] = None
    ):
        """
        Add user feedback
        
        Args:
            conversation_id: Conversation ID
            turn_number: Turn number (None for conversation-level feedback)
            feedback_type: 'thumbs_up', 'thumbs_down', 'rating', 'comment'
            feedback_value: 1.0 for positive, 0.0 for negative, 1-5 for rating
            comment: Optional comment
            implicit_signals: Optional dict of implicit signals (dwell_time, etc.)
        """
        self.store.add_feedback(
            conversation_id,
            turn_number,
            feedback_type,
            feedback_value,
            comment,
            implicit_signals
        )
    
    def end_conversation(
        self,
        conversation_id: str,
        goal_achieved: bool = False
    ):
        """Mark conversation as ended"""
        self.store.end_conversation(conversation_id, goal_achieved)
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Get full conversation with all turns"""
        return self.store.get_conversation(conversation_id)
    
    def get_conversation_stats(self, conversation_id: str) -> Dict:
        """Get conversation statistics"""
        conversation = self.store.get_conversation(conversation_id)
        if not conversation:
            return {}
        
        feedback_stats = self.store.get_feedback_stats(conversation_id)
        entity_coverage = self.store.get_entity_coverage(conversation_id)
        
        return {
            'total_turns': conversation['total_turns'],
            'avg_quality_score': conversation['avg_quality_score'],
            'goal_achieved': conversation.get('goal_achieved', False),
            'feedback': feedback_stats,
            'unique_entities_covered': len(entity_coverage),
            'top_entities': [
                {'name': e['entity_name'], 'mentions': e['mention_count']}
                for e in entity_coverage[:10]
            ]
        }
