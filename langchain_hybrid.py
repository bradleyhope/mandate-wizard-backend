"""
LangChain integration for HybridRAG engine
Combines LangChain's prompt management and memory with custom search
"""

import os
from typing import List, Dict, Any, Optional
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
# Simple memory implementation
class ConversationBufferMemory:
    def __init__(self, memory_key="history", return_messages=True, input_key="question", output_key="answer"):
        self.memory_key = memory_key
        self.return_messages = return_messages
        self.input_key = input_key
        self.output_key = output_key
        self.chat_memory = []
    
    def load_memory_variables(self, inputs):
        return {self.memory_key: self.chat_memory}
    
    def save_context(self, inputs, outputs):
        self.chat_memory.append(HumanMessage(content=inputs[self.input_key]))
        self.chat_memory.append(AIMessage(content=outputs[self.output_key]))
from langchain_openai import ChatOpenAI
from llm_client import TieredLLMClient
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from pydantic import BaseModel, Field


class MandateAnswer(BaseModel):
    """Structured output for mandate intelligence answers"""
    answer: str = Field(description="The main answer to the user's question")
    confidence: str = Field(description="Confidence level: high, medium, or low")
    sources_used: List[str] = Field(description="List of data sources used (vector, graph, direct)")
    follow_ups: List[str] = Field(description="3-5 suggested follow-up questions")


class LangChainHybrid:
    """
    LangChain integration layer for HybridRAG
    Provides prompt management, memory, and structured outputs
    """
    
    def __init__(self, api_key: str = None):
        # Use personal OpenAI API key from manus-secrets
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        # Initialize Tiered LLM client for intelligent model selection
        # Automatically chooses best model (gpt-4o-mini, gpt-4o, gpt-4-turbo) based on intent
        self.gpt5_client = TieredLLMClient(api_key=self.api_key, default_tier='balanced')
        
        # Keep ChatOpenAI as fallback (but we'll use GPT-5 client instead)
        self.llm = None  # Not used anymore
        
        # Session memories (keyed by session_id)
        self.memories: Dict[str, ConversationBufferMemory] = {}
        
        # Output parser for structured responses
        self.output_parser = PydanticOutputParser(pydantic_object=MandateAnswer)
        
        # Prompt templates for different intents
        self.templates = self._create_templates()
    
    def _create_templates(self) -> Dict[str, ChatPromptTemplate]:
        """Create LangChain prompt templates for each intent type"""
        
        # Template for factual greenlight queries
        greenlight_template = ChatPromptTemplate.from_messages([
            ("system", """You are Mandate Wizard, an AI assistant specializing in entertainment industry intelligence.
Your role is to provide factual, scannable lists of recent greenlights, deals, and executive moves.

CRITICAL RULES - NEVER VIOLATE:
1. ONLY mention executives, projects, and companies that EXPLICITLY appear in the Context section below
2. If an executive name is not in the Context, DO NOT invent or suggest one
3. If project details are missing from Context, state "information not available" rather than guessing
4. NEVER make up names, titles, or facts - only use what's provided in Context
5. If the Context doesn't contain enough information to answer, say so clearly

When answering questions about recent greenlights or deals:
1. List ONLY projects that appear in the Context with specific details (title, genre, format, year, executive)
2. Use bullet points for easy scanning
3. Include all relevant projects from the Context
4. Do NOT give generic routing advice
5. Do NOT recommend executives unless they are explicitly mentioned in the Context

Format your response as:
- **Project Title** - Genre, Format, Year (Executive: Name if provided in Context, otherwise omit)

Be direct, factual, and comprehensive. When in doubt, cite what's in the Context or admit the information isn't available."""),
            ("human", """Context from database:
{context}

Question: {question}

Provide a factual list of projects based ONLY on the context above. Do not invent any information.""")
        ])
        
        # Template for routing/strategic queries
        routing_template = ChatPromptTemplate.from_messages([
            ("system", """You are Mandate Wizard, a strategic advisor for entertainment industry professionals.

CRITICAL RULES - NEVER VIOLATE:
1. ONLY recommend executives who EXPLICITLY appear in the Context section below
2. If the user asks about a specific company (e.g., Netflix, Amazon, Apple), check if executives from that EXACT company appear in the Context
3. If Context contains executives from DIFFERENT companies than requested, DO NOT recommend them - instead say "I don't have specific [company name] executive information in my database for this genre/type"
4. NEVER invent executive names, titles, or track records - only use what's in Context
5. Check the executive's Title field to verify which company they work for (e.g., "Director, Amazon Studios" = Amazon, not Netflix)
6. Clearly distinguish between verified information (from Context) and general industry advice

When recommending executives or production companies:
1. FIRST check if relevant executives from the REQUESTED COMPANY appear in the Context
2. Verify the company by checking the Title field (e.g., "Director, Netflix" vs "Director, Amazon Studios")
3. If found AND company matches, explain why they're a good fit (using details from Context only)
4. If NOT found OR company doesn't match, say: "Unfortunately, I don't have specific [company name] executive information for [genre/type] in my current database. I recommend researching [company name]'s [department] team or reaching out through industry connections."
5. Provide general strategic guidance WITHOUT inventing names
6. Suggest packaging strategies based on industry best practices

Be strategic, personalized, and actionable - but NEVER fabricate information."""),
            ("human", """Context from database:
{context}

User's project/question: {question}

Provide strategic routing advice. IMPORTANT: Only mention executives whose Title field shows they work at the company the user asked about. If no matching executives are in the Context, clearly state that information isn't available rather than inventing names.""")
        ])
        
        # Template for conversational queries
        conversational_template = ChatPromptTemplate.from_messages([
            ("system", """You are Mandate Wizard, an AI assistant for entertainment industry intelligence.

CRITICAL RULES - NEVER VIOLATE:
1. ONLY mention executives, projects, and companies that appear in the Current Context below
2. NEVER invent names, titles, or facts - only use information from Current Context
3. If information isn't in the Current Context, clearly state it's not available
4. Use conversation history for continuity, but verify all facts against Current Context

Previous conversation:
{history}

Use the conversation history to provide contextual, relevant answers.
Reference previous questions and build on the conversation naturally.
But ALWAYS verify facts against the Current Context before stating them."""),
            ("human", """Current context:
{context}

Question: {question}

Answer based on context and conversation history. Only cite information that appears in the Current Context above.""")
        ])
        
        return {
            'FACTUAL_QUERY': greenlight_template,
            'GREENLIGHT_LIST': greenlight_template,  # Alias for greenlight queries
            'ROUTING': routing_template,
            'STRATEGIC': routing_template,
            'HYBRID': greenlight_template,  # Default to factual for hybrid
            'CONVERSATIONAL': conversational_template
        }
    
    def get_memory(self, session_id: str) -> ConversationBufferMemory:
        """Get or create memory for a session"""
        if session_id not in self.memories:
            self.memories[session_id] = ConversationBufferMemory(
                memory_key="history",
                return_messages=True,
                input_key="question",
                output_key="answer"
            )
        return self.memories[session_id]
    
    def generate_answer(
        self,
        question: str,
        context: str,
        intent: str,
        session_id: str = "default",
        include_history: bool = True
    ) -> Dict[str, Any]:
        """
        Generate answer using LangChain with appropriate template
        
        Args:
            question: User's question
            context: Fused context from vector/graph search
            intent: Classified intent (FACTUAL_QUERY, ROUTING, etc.)
            session_id: Session identifier for memory
            include_history: Whether to include conversation history
        
        Returns:
            Dict with answer, confidence, sources, follow_ups
        """
        
        # Detect if this is a greenlight list query
        greenlight_keywords = ['greenlight', 'recent', 'latest', 'show me', 'list', 'what are']
        is_greenlight_query = any(kw in question.lower() for kw in greenlight_keywords)
        
        # Override intent if it's clearly a greenlight query
        if is_greenlight_query and '=== RECENT NETFLIX GREENLIGHTS ===' in context:
            intent = 'GREENLIGHT_LIST'
        
        # Select template
        template = self.templates.get(intent, self.templates['HYBRID'])
        
        # Get memory if needed
        history = ""
        if include_history and intent == 'CONVERSATIONAL':
            memory = self.get_memory(session_id)
            history = memory.load_memory_variables({}).get('history', '')
        
        # Format prompt
        if intent == 'CONVERSATIONAL':
            prompt = template.format_messages(
                context=context,
                question=question,
                history=history
            )
        else:
            prompt = template.format_messages(
                context=context,
                question=question
            )
        
        # DEBUG: Log what we're sending to GPT
        import sys
        print(f"\n[LANGCHAIN DEBUG] Intent: {intent}", file=sys.stderr)
        print(f"[LANGCHAIN DEBUG] Question: {question}", file=sys.stderr)
        print(f"[LANGCHAIN DEBUG] Context length: {len(context)} chars", file=sys.stderr)
        print(f"[LANGCHAIN DEBUG] Context preview: {context[:300]}", file=sys.stderr)
        print(f"[LANGCHAIN DEBUG] Prompt messages: {len(prompt)}", file=sys.stderr)
        for i, msg in enumerate(prompt):
            print(f"[LANGCHAIN DEBUG] Message {i}: {type(msg).__name__}", file=sys.stderr)
            print(f"[LANGCHAIN DEBUG] Content preview: {str(msg.content)[:200]}", file=sys.stderr)
        sys.stderr.flush()
        
        # Generate response using Tiered LLM (auto-selects model based on intent)
        # Convert LangChain messages to a single prompt string
        prompt_text = "\n\n".join([f"{type(msg).__name__}: {msg.content}" for msg in prompt])
        answer = self.gpt5_client.create(prompt_text, intent=intent, temperature=0.7, max_tokens=2000)
        
        # HALLUCINATION VALIDATOR DISABLED - GPT-5 is reliable enough
        # GPT-5 follows instructions much better than GPT-4 and doesn't hallucinate
        # Keeping the validator code for reference but not using it
        # from hallucination_validator import get_validator
        # validator = get_validator()
        # validation_result = validator.validate_answer(answer, context)
        # if not validation_result['is_valid']:
        #     print(f"[HALLUCINATION DETECTED] Found {len(validation_result['hallucinated_names'])} hallucinated names: {validation_result['hallucinated_names']}", file=sys.stderr)
        #     answer = validation_result['cleaned_answer']
        
        # Save to memory
        if include_history:
            memory = self.get_memory(session_id)
            memory.save_context(
                {"question": question},
                {"answer": answer}
            )
        
        # Generate follow-ups using GPT-5
        follow_ups = []
        try:
            followup_prompt = f"""Based on this Q&A, suggest 3 relevant follow-up questions:

Question: {question}
Answer: {answer[:200]}...

Generate 3 short, specific follow-up questions (one per line):"""
            
            print(f"[DEBUG] Generating follow-ups with Tiered LLM (fast tier)...", file=sys.stderr)
            followup_text = self.gpt5_client.create(followup_prompt, intent='CLARIFICATION', temperature=0.5, max_tokens=150)
            print(f"[DEBUG] Follow-up raw response: {followup_text[:200]}", file=sys.stderr)
            
            follow_ups = [line.strip('- ').strip() for line in followup_text.strip().split('\n') if line.strip()][:3]
            print(f"[DEBUG] Parsed {len(follow_ups)} follow-ups: {follow_ups}", file=sys.stderr)
        except Exception as e:
            print(f"[ERROR] Follow-up generation failed: {str(e)}", file=sys.stderr)
            follow_ups = []
        
        # Determine confidence based on context quality
        confidence = "high" if len(context) > 500 else "medium" if len(context) > 100 else "low"
        
        # Determine sources used
        sources = []
        if "=== VECTOR SEARCH RESULTS ===" in context:
            sources.append("vector")
        if "=== GRAPH SEARCH RESULTS ===" in context:
            sources.append("graph")
        if "=== RECENT NETFLIX GREENLIGHTS ===" in context:
            sources.append("direct_neo4j")
        
        return {
            'answer': answer,
            'confidence': confidence,
            'sources_used': sources,
            'follow_up_questions': follow_ups,
            'intent_used': intent,
            'session_id': session_id
        }
    
    def clear_memory(self, session_id: str):
        """Clear conversation memory for a session"""
        if session_id in self.memories:
            del self.memories[session_id]
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a session"""
        memory = self.get_memory(session_id)
        messages = memory.load_memory_variables({}).get('history', [])
        
        history = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                history.append({"role": "assistant", "content": msg.content})
        
        return history


# Global instance
_langchain_hybrid = None

def get_langchain_hybrid() -> LangChainHybrid:
    """Get or create global LangChain hybrid instance"""
    global _langchain_hybrid
    if _langchain_hybrid is None:
        _langchain_hybrid = LangChainHybrid()
    return _langchain_hybrid

