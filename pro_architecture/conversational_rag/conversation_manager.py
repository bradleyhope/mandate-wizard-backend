"""
Conversation Manager - Handles conversation flow, query classification, and strategy planning
Phase 1: Gemini-optimized with semantic similarity and comparative question handling
"""

from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import re

from .conversation_store import ConversationStore, ConversationState, ConversationTurn


class QuestionType(Enum):
    """Types of follow-up questions"""
    DRILL_DOWN = "drill_down"  # "Tell me more about X"
    EXPLORE_MORE = "explore_more"  # "What other options?"
    COMPARE = "compare"  # "How does X compare to Y?"
    CLARIFY = "clarify"  # "What do you mean by X?"
    ACTION = "action"  # "How do I do X?"
    INITIAL = "initial"  # First question in conversation


class ResponseStrategy(Enum):
    """Response strategies"""
    BREADTH = "breadth"  # Wide coverage, multiple entities
    DEPTH = "depth"  # Deep dive on single entity/topic
    COMPARE = "compare"  # Side-by-side comparison
    STRATEGIC_ADVICE = "strategic_advice"  # High-level guidance
    ACTIONABLE_STEPS = "actionable_steps"  # Tactical next steps


@dataclass
class TurnContext:
    """Context for generating a response"""
    conversation_id: str
    turn_number: int
    user_query: str
    rewritten_query: str
    question_type: QuestionType
    response_strategy: ResponseStrategy
    
    # Entities to handle
    entities_to_exclude: List[str]
    entities_to_include: List[str]  # For comparative questions
    
    # Conversation state
    state: ConversationState
    recent_turns: List[ConversationTurn]
    
    # Targets
    target_depth: int
    novelty_target: float


class ConversationManager:
    """Manages conversation flow and strategy"""
    
    def __init__(self, store: ConversationStore, llm_client):
        self.store = store
        self.llm = llm_client
    
    # ========================================================================
    # MAIN ORCHESTRATION
    # ========================================================================
    
    def process_user_query(
        self,
        conversation_id: str,
        user_query: str
    ) -> TurnContext:
        """Process user query and create turn context"""
        
        # Get conversation state
        state = self.store.get_state(conversation_id)
        recent_turns = self.store.get_recent_turns(conversation_id, limit=5)
        turn_number = len(recent_turns) + 1
        
        # Classify question type
        question_type = self.infer_question_type(user_query, recent_turns)
        
        # Infer/update user goal
        if turn_number <= 3:  # Update goal in early turns
            self._update_user_goal(conversation_id, user_query, recent_turns, state)
        
        # Plan response strategy
        response_strategy, target_depth = self._plan_response_strategy(
            question_type, state, recent_turns
        )
        
        # Handle entity filtering (with comparative question support)
        entities_to_exclude, entities_to_include = self._plan_entity_filtering(
            user_query, question_type, state
        )
        
        # Rewrite query with context
        rewritten_query = self._rewrite_query_with_context(
            user_query, recent_turns, question_type
        )
        
        # Calculate novelty target
        novelty_target = self._calculate_novelty_target(turn_number, state)
        
        return TurnContext(
            conversation_id=conversation_id,
            turn_number=turn_number,
            user_query=user_query,
            rewritten_query=rewritten_query,
            question_type=question_type,
            response_strategy=response_strategy,
            entities_to_exclude=entities_to_exclude,
            entities_to_include=entities_to_include,
            state=state,
            recent_turns=recent_turns,
            target_depth=target_depth,
            novelty_target=novelty_target
        )
    
    # ========================================================================
    # QUESTION TYPE INFERENCE
    # ========================================================================
    
    def infer_question_type(
        self,
        query: str,
        recent_turns: List[ConversationTurn]
    ) -> QuestionType:
        """Infer question type from query"""
        
        if not recent_turns:
            return QuestionType.INITIAL
        
        query_lower = query.lower()
        
        # Comparative questions
        compare_patterns = [
            r'\bcompare\b', r'\bvs\b', r'\bversus\b', r'\bdifference\b',
            r'\bhow does .+ compare\b', r'\bwhich is better\b',
            r'\b(better|worse) than\b'
        ]
        if any(re.search(pattern, query_lower) for pattern in compare_patterns):
            return QuestionType.COMPARE
        
        # Drill-down questions
        drilldown_patterns = [
            r'\btell me more\b', r'\bmore about\b', r'\bdetails\b',
            r'\bspecifically\b', r'\bwhat about (his|her|their)\b',
            r'\bgo deeper\b', r'\belaborate\b'
        ]
        if any(re.search(pattern, query_lower) for pattern in drilldown_patterns):
            return QuestionType.DRILL_DOWN
        
        # Exploration questions
        explore_patterns = [
            r'\bwhat (other|else)\b', r'\bany other\b', r'\bmore options\b',
            r'\balternatives\b', r'\bbesides\b', r'\bapart from\b',
            r'\bwho else\b', r'\bother (platforms|companies|people)\b'
        ]
        if any(re.search(pattern, query_lower) for pattern in explore_patterns):
            return QuestionType.EXPLORE_MORE
        
        # Action questions
        action_patterns = [
            r'\bhow (do|can) i\b', r'\bwhat should i\b', r'\bsteps\b',
            r'\bhow to\b', r'\bprocess\b', r'\bapproach\b'
        ]
        if any(re.search(pattern, query_lower) for pattern in action_patterns):
            return QuestionType.ACTION
        
        # Clarification questions
        clarify_patterns = [
            r'\bwhat (do you mean|does that mean)\b', r'\bexplain\b',
            r'\bwhat is\b', r'\bdefine\b', r'\bclarify\b'
        ]
        if any(re.search(pattern, query_lower) for pattern in clarify_patterns):
            return QuestionType.CLARIFY
        
        # Default: if short and vague, likely drill-down; if longer, likely explore
        if len(query.split()) < 5:
            return QuestionType.DRILL_DOWN
        else:
            return QuestionType.EXPLORE_MORE
    
    # ========================================================================
    # RESPONSE STRATEGY PLANNING
    # ========================================================================
    
    def _plan_response_strategy(
        self,
        question_type: QuestionType,
        state: ConversationState,
        recent_turns: List[ConversationTurn]
    ) -> Tuple[ResponseStrategy, int]:
        """Plan response strategy and target depth"""
        
        current_depth = state.current_depth
        
        # Comparative questions always use COMPARE strategy
        if question_type == QuestionType.COMPARE:
            return (ResponseStrategy.COMPARE, current_depth)
        
        # Drill-down increases depth
        if question_type == QuestionType.DRILL_DOWN:
            target_depth = min(current_depth + 1, 5)
            return (ResponseStrategy.DEPTH, target_depth)
        
        # Exploration stays at current depth but goes broad
        if question_type == QuestionType.EXPLORE_MORE:
            return (ResponseStrategy.BREADTH, current_depth)
        
        # Action questions get tactical steps
        if question_type == QuestionType.ACTION:
            return (ResponseStrategy.ACTIONABLE_STEPS, current_depth)
        
        # Clarification maintains depth
        if question_type == QuestionType.CLARIFY:
            return (ResponseStrategy.DEPTH, current_depth)
        
        # Initial questions get strategic overview
        if question_type == QuestionType.INITIAL:
            return (ResponseStrategy.STRATEGIC_ADVICE, 1)
        
        # Default
        return (ResponseStrategy.BREADTH, current_depth)
    
    # ========================================================================
    # ENTITY FILTERING (with Comparative Question Support)
    # ========================================================================
    
    def _plan_entity_filtering(
        self,
        query: str,
        question_type: QuestionType,
        state: ConversationState
    ) -> Tuple[List[str], List[str]]:
        """
        Plan entity filtering with support for comparative questions.
        Returns: (entities_to_exclude, entities_to_include)
        
        Gemini's key insight: Don't just exclude - also include for comparisons!
        """
        
        entities_to_exclude = []
        entities_to_include = []
        
        # For comparative questions, extract entities being compared
        if question_type == QuestionType.COMPARE:
            # Extract entity names from query
            entities_in_query = self._extract_entities_from_query(query, state)
            entities_to_include = entities_in_query
            
            # Exclude other covered entities (but not the ones being compared)
            entities_to_exclude = [
                e for e in state.covered_entities
                if e not in entities_to_include
            ]
        
        # For drill-down, don't exclude the entity being drilled into
        elif question_type == QuestionType.DRILL_DOWN:
            # Try to identify which entity user is drilling into
            drill_entity = self._identify_drill_target(query, state, recent_turns=[])
            if drill_entity:
                entities_to_include = [drill_entity]
                entities_to_exclude = [
                    e for e in state.covered_entities
                    if e != drill_entity
                ]
            else:
                # If can't identify, exclude all covered entities
                entities_to_exclude = state.covered_entities
        
        # For exploration, exclude all covered entities
        elif question_type == QuestionType.EXPLORE_MORE:
            entities_to_exclude = state.covered_entities
        
        # For other question types, moderate exclusion
        else:
            # Exclude entities mentioned in last 2 turns (not entire history)
            recent_entities = []
            entity_coverage = self.store.get_entity_coverage(state.conversation_id) if hasattr(state, 'conversation_id') else []
            for entity in entity_coverage:
                if entity['last_mentioned_turn'] >= max(1, state.current_depth - 2):
                    recent_entities.append(entity['entity_name'])
            
            entities_to_exclude = recent_entities
        
        return (entities_to_exclude, entities_to_include)
    
    def _extract_entities_from_query(self, query: str, state: ConversationState) -> List[str]:
        """Extract entity names mentioned in query"""
        entities_in_query = []
        
        # Check if any covered entities are mentioned in the query
        for entity in state.covered_entities:
            # Simple substring match (case-insensitive)
            if entity.lower() in query.lower():
                entities_in_query.append(entity)
        
        return entities_in_query
    
    def _identify_drill_target(
        self,
        query: str,
        state: ConversationState,
        recent_turns: List[ConversationTurn]
    ) -> Optional[str]:
        """Identify which entity user wants to drill into"""
        
        # Check if query mentions a specific entity
        entities_in_query = self._extract_entities_from_query(query, state)
        if entities_in_query:
            return entities_in_query[0]  # Return first match
        
        # If no explicit mention, assume last mentioned entity
        if recent_turns and recent_turns[-1].entities_mentioned:
            return recent_turns[-1].entities_mentioned[0]
        
        return None
    
    # ========================================================================
    # QUERY REWRITING
    # ========================================================================
    
    def _rewrite_query_with_context(
        self,
        query: str,
        recent_turns: List[ConversationTurn],
        question_type: QuestionType
    ) -> str:
        """Rewrite vague follow-ups into self-contained queries"""
        
        # If initial question or already specific, no rewriting needed
        if question_type == QuestionType.INITIAL or len(query.split()) > 10:
            return query
        
        # If no context, return as-is
        if not recent_turns:
            return query
        
        # Build context from recent turns
        context_parts = []
        for turn in recent_turns[-2:]:  # Last 2 turns
            context_parts.append(f"Q: {turn.user_query}\nA: {turn.answer[:200]}...")
        
        context = "\n\n".join(context_parts)
        
        # Use LLM to rewrite query
        prompt = f"""Given this conversation context:

{context}

The user now asks: "{query}"

Rewrite this as a self-contained question that includes necessary context from the conversation.
Keep it concise (1-2 sentences max).

Rewritten question:"""
        
        try:
            response = self.llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a query rewriting assistant. Rewrite queries to be clearer and more specific based on conversation context."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.3
            )
            rewritten = response.choices[0].message.content
            return rewritten.strip()
        except Exception as e:
            # If rewriting fails, return original
            print(f"Query rewriting failed: {e}")
            return query
    
    # ========================================================================
    # GOAL INFERENCE
    # ========================================================================
    
    def _update_user_goal(
        self,
        conversation_id: str,
        query: str,
        recent_turns: List[ConversationTurn],
        state: ConversationState
    ):
        """Infer and update user's goal"""
        
        # Build conversation history
        history = "\n".join([
            f"User: {turn.user_query}\nAssistant: {turn.answer[:150]}..."
            for turn in recent_turns
        ])
        history += f"\nUser: {query}"
        
        # Use LLM to infer goal
        prompt = f"""Based on this conversation, infer the user's main goal in 1-2 sentences.

Conversation:
{history}

User's goal:"""
        
        try:
            response = self.llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a goal inference assistant. Infer the user's overall goal from their conversation history."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.3
            )
            inferred_goal = response.choices[0].message.content
            self.store.update_conversation_goal(
                conversation_id,
                inferred_goal.strip(),
                confidence=0.7  # Fixed confidence for Phase 1
            )
        except Exception as e:
            print(f"Goal inference failed: {e}")
    
    # ========================================================================
    # NOVELTY TARGET
    # ========================================================================
    
    def _calculate_novelty_target(self, turn_number: int, state: ConversationState) -> float:
        """Calculate target novelty score for this turn"""
        
        # Early turns should be highly novel
        if turn_number <= 2:
            return 0.9
        
        # Middle turns should balance novelty with depth
        if turn_number <= 5:
            return 0.7
        
        # Later turns can have lower novelty (deepening existing topics)
        return 0.5
    
    # ========================================================================
    # STATE UPDATES
    # ========================================================================
    
    def update_state_after_turn(
        self,
        context: TurnContext,
        answer: str,
        entities_mentioned: List[str],
        quality_score: float
    ):
        """Update conversation state after generating answer"""
        
        state = context.state
        
        # Update working memory (last 1-2 turns)
        state.working_memory = {
            'last_query': context.user_query,
            'last_answer': answer[:500],  # Truncate for storage
            'last_entities': entities_mentioned,
            'last_strategy': context.response_strategy.value
        }
        
        # Update short-term memory (last 3-5 turns)
        state.short_term_memory.append({
            'turn': context.turn_number,
            'query': context.user_query,
            'entities': entities_mentioned,
            'quality': quality_score
        })
        if len(state.short_term_memory) > 5:
            state.short_term_memory = state.short_term_memory[-5:]
        
        # Update long-term memory (key facts)
        for entity in entities_mentioned:
            if entity not in state.long_term_memory:
                state.long_term_memory[entity] = {
                    'first_turn': context.turn_number,
                    'mentions': 0
                }
            state.long_term_memory[entity]['mentions'] += 1
            state.long_term_memory[entity]['last_turn'] = context.turn_number
        
        # Update covered entities
        for entity in entities_mentioned:
            if entity not in state.covered_entities:
                state.covered_entities.append(entity)
        
        # Update depth
        if context.response_strategy == ResponseStrategy.DEPTH:
            state.current_depth = context.target_depth
            state.max_depth_reached = max(state.max_depth_reached, context.target_depth)
        
        # Save state
        self.store.update_state(context.conversation_id, state)
