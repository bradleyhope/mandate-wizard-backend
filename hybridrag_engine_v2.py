"""
Mandate Wizard HybridRAG Engine V2
First Principles Redesign - Intent-Based Query Processing
"""

from typing import Dict, List, Any, Optional
import re

class IntentClassifier:
    """
    Classifies user questions into specific intent categories based on first principles.
    
    Intent Categories:
    1. PERSON_FINDING - User wants to know WHO to contact
    2. STRATEGIC_INFO - User wants to know WHAT Netflix wants/priorities
    3. PROCESS_GUIDANCE - User wants to know HOW to do something
    4. MARKET_INFO - User wants to know WHERE/WHICH markets/regions
    5. CLARIFICATION - User is clarifying or correcting previous context
    """
    
    def __init__(self):
        # Intent patterns with priority (higher number = higher priority)
        self.intent_patterns = {
            'PERSON_FINDING': {
                'priority': 10,
                'patterns': [
                    r'\bwho (do i|should i|to) (pitch|contact|talk to|approach)',
                    r'\bwho handles\b',
                    r'\bwho is (on|in charge of|responsible for)',
                    r'\bwho are (on|in charge of)',
                    r'\bwho to (pitch|contact|talk to)',
                    r'\bwhere (do i go|to go)\b',  # "where to go" often means "who to contact"
                    r'\bwhat (do i|should i) do\b',  # "what should i do" with project = who to contact
                ],
                'keywords': ['who', 'contact', 'pitch to', 'approach']
            },
            
            'STRATEGIC_INFO': {
                'priority': 9,
                'patterns': [
                    r'\bwhat (kind of|type of|does .* want)',
                    r'\bwhat are (recent )?mandates?\b',
                    r'\bwhat are .* (priorities|looking for)',
                    r'\bwhat is .* (strategy|mandate|priority)',
                    r'\bdoes .* want\b',
                    r'\bis .* looking for\b',
                    r'\bwhat matters to\b',
                ],
                'keywords': ['mandate', 'priority', 'strategy', 'want', 'looking for']
            },
            
            'MARKET_INFO': {
                'priority': 8,
                'patterns': [
                    r'\bwhat (countries|markets|regions)',
                    r'\bwhich (countries|markets|regions)',
                    r'\bwhere does .* operate\b',
                    r'\bwhat territories\b',
                    r'\bi mean what (countries|markets)',
                ],
                'keywords': ['countries', 'markets', 'regions', 'territories', 'where']
            },
            
            'PROCESS_GUIDANCE': {
                'priority': 7,
                'patterns': [
                    r'\bhow (do i|to|should i) (pitch|submit|approach)',
                    r'\bwhat is the process\b',
                    r'\bhow does .* work\b',
                    r'\bwhat steps\b',
                ],
                'keywords': ['how', 'process', 'steps', 'procedure']
            },
            
            'CLARIFICATION': {
                'priority': 11,  # Highest priority for single-word corrections
                'patterns': [
                    r'^[a-z]+$',  # Single word (e.g., "norway")
                    r'^i mean\b',
                    r'^actually\b',
                    r'^no,?\s',
                ],
                'keywords': []
            }
        }
    
    def classify(self, question: str, conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Classify the user's question intent.
        
        Returns:
            {
                'intent': str,  # Primary intent
                'confidence': float,  # 0-1
                'sub_intent': str,  # Secondary intent if applicable
                'needs_context': bool  # Whether this needs conversation history
            }
        """
        question_lower = question.lower().strip()
        
        # Score each intent
        scores = {}
        for intent, config in self.intent_patterns.items():
            score = 0
            
            # Check regex patterns
            for pattern in config['patterns']:
                if re.search(pattern, question_lower):
                    score += config['priority'] * 2  # Pattern match is strong signal
            
            # Check keywords
            for keyword in config['keywords']:
                if keyword in question_lower:
                    score += config['priority']
            
            scores[intent] = score
        
        # Get top intent
        if max(scores.values()) == 0:
            # No clear intent, default based on question structure
            if 'i have' in question_lower or 'my' in question_lower:
                primary_intent = 'PERSON_FINDING'
            else:
                primary_intent = 'STRATEGIC_INFO'
            confidence = 0.5
        else:
            primary_intent = max(scores, key=scores.get)
            confidence = min(scores[primary_intent] / 20.0, 1.0)  # Normalize
        
        # Check if this is a clarification that needs context
        needs_context = primary_intent == 'CLARIFICATION' or len(question_lower.split()) <= 2
        
        return {
            'intent': primary_intent,
            'confidence': confidence,
            'needs_context': needs_context,
            'scores': scores
        }


class DataSourceSelector:
    """
    Determines which data sources to query based on intent and question attributes.
    """
    
    @staticmethod
    def select_sources(intent: str, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Select data sources and query strategies based on intent.
        
        Returns:
            {
                'neo4j': {
                    'enabled': bool,
                    'query_type': str,  # 'person_search', 'regional_structure', etc.
                    'filters': dict
                },
                'pinecone': {
                    'enabled': bool,
                    'query_type': str,  # 'semantic_search', 'mandate_search', etc.
                    'top_k': int
                },
                'answer_format': str  # 'person_routing', 'strategic_info', 'market_list', etc.
            }
        """
        
        if intent == 'PERSON_FINDING':
            return {
                'neo4j': {
                    'enabled': True,
                    'query_type': 'person_search',
                    'filters': {
                        'region': attributes.get('region'),
                        'format': attributes.get('format'),
                        'genre': attributes.get('genre')
                    }
                },
                'pinecone': {
                    'enabled': True,
                    'query_type': 'context_search',
                    'top_k': 5
                },
                'answer_format': 'person_routing'
            }
        
        elif intent == 'STRATEGIC_INFO':
            return {
                'neo4j': {
                    'enabled': True,
                    'query_type': 'vp_mandates',  # Get VP-level strategic info
                    'filters': {
                        'seniority': 'VP',
                        'region': attributes.get('region'),
                        'genre': attributes.get('genre')
                    }
                },
                'pinecone': {
                    'enabled': True,
                    'query_type': 'mandate_search',  # Focus on mandate documents
                    'top_k': 10
                },
                'answer_format': 'strategic_info'
            }
        
        elif intent == 'MARKET_INFO':
            return {
                'neo4j': {
                    'enabled': True,
                    'query_type': 'regional_structure',  # Get all regions/countries
                    'filters': {}
                },
                'pinecone': {
                    'enabled': True,
                    'query_type': 'market_intelligence',
                    'top_k': 10
                },
                'answer_format': 'market_list'
            }
        
        elif intent == 'PROCESS_GUIDANCE':
            return {
                'neo4j': {
                    'enabled': False,
                    'query_type': None,
                    'filters': {}
                },
                'pinecone': {
                    'enabled': True,
                    'query_type': 'process_search',
                    'top_k': 10
                },
                'answer_format': 'process_steps'
            }
        
        elif intent == 'CLARIFICATION':
            return {
                'neo4j': {
                    'enabled': True,
                    'query_type': 'person_search',
                    'filters': {
                        'region': attributes.get('region'),
                        'format': attributes.get('format'),
                        'genre': attributes.get('genre')
                    }
                },
                'pinecone': {
                    'enabled': True,
                    'query_type': 'context_search',
                    'top_k': 5
                },
                'answer_format': 'person_routing'  # Usually clarifying who to contact
            }
        
        else:
            # Default: hybrid approach
            return {
                'neo4j': {
                    'enabled': True,
                    'query_type': 'person_search',
                    'filters': {}
                },
                'pinecone': {
                    'enabled': True,
                    'query_type': 'semantic_search',
                    'top_k': 10
                },
                'answer_format': 'hybrid'
            }


class AnswerFormatter:
    """
    Generates system prompts and formats answers based on intent and data sources.
    """
    
    @staticmethod
    def get_system_prompt(intent: str, answer_format: str) -> str:
        """Get the appropriate system prompt for the intent."""
        
        if answer_format == 'person_routing':
            return """You are an expert Netflix pitch advisor. The user wants to know WHO to contact.

CRITICAL RULES:
1. ALWAYS provide a specific person's name and title
2. Explain WHY this person is the right contact
3. Provide context about their mandate and what they're looking for
4. Include reporting structure (who they report to)
5. Give pitch positioning advice

ANSWER FORMAT:
Paragraph 1: "Pitch to [Name], [Title]. [Why they're the right contact]"
Paragraph 2: "[Their mandate and what they're looking for]"
Paragraph 3: "[How to position your pitch effectively]"

Keep it concise (3 paragraphs, 300-400 words)."""

        elif answer_format == 'strategic_info':
            return """You are an expert Netflix strategy analyst. The user wants to know WHAT Netflix wants (strategic information).

CRITICAL RULES:
1. DO NOT route to a specific person unless explicitly asked
2. Provide strategic information about mandates, priorities, content needs
3. If asked "what are recent mandates", list 3-5 key mandates from different VPs
4. Focus on WHAT they want, not WHO to contact
5. Include context about why these priorities matter

ANSWER FORMAT:
For "what are recent mandates":
- List 3-5 key strategic priorities
- For each: VP name, what they want, why it matters
- Keep it informative and strategic

For "what does Netflix want in X":
- Explain the strategic mandate for that genre/format
- Include recent successes and priorities
- Mention what makes content successful in this area

Keep it concise but comprehensive (300-500 words)."""

        elif answer_format == 'market_list':
            return """You are an expert on Netflix's global operations. The user wants to know WHICH countries/markets/regions matter.

CRITICAL RULES:
1. Provide a clear list of countries/regions
2. Group by region if appropriate (e.g., "Nordics: Norway, Sweden, Denmark, Finland")
3. Mention which regions have dedicated teams/executives
4. Explain why these markets matter strategically
5. DO NOT route to specific people unless asked

ANSWER FORMAT:
Paragraph 1: Overview of Netflix's key markets
Paragraph 2-3: List of regions/countries with context
Paragraph 4: Strategic importance and priorities

Keep it clear and list-focused (300-400 words)."""

        elif answer_format == 'process_steps':
            return """You are an expert on Netflix's pitch and acquisition process. The user wants to know HOW to do something.

CRITICAL RULES:
1. Provide clear, actionable steps
2. Explain the process flow
3. Include best practices and timing
4. Mention what to include in materials
5. Be practical and specific

ANSWER FORMAT:
Step-by-step guidance with context and best practices.

Keep it practical and actionable (300-400 words)."""

        else:  # hybrid
            return """You are an expert Netflix pitch advisor. Provide helpful, accurate information based on the user's question.

Use the context provided to give specific, actionable advice. Be concise and professional."""

    @staticmethod
    def should_include_person(intent: str, answer_format: str) -> bool:
        """Determine if the answer should include a specific person to contact."""
        return answer_format in ['person_routing', 'clarification']
    
    @staticmethod
    def format_context_for_llm(intent: str, neo4j_results: List[Dict], pinecone_results: List[Dict]) -> str:
        """Format the retrieved context appropriately for the intent."""
        
        context_parts = []
        
        if intent == 'PERSON_FINDING':
            # Focus on person details
            if neo4j_results:
                context_parts.append("=== RELEVANT EXECUTIVES ===")
                for person in neo4j_results[:3]:
                    context_parts.append(f"""
Name: {person.get('name')}
Title: {person.get('current_title')}
Region: {person.get('region', 'US')}
Bio: {person.get('bio', 'N/A')}
Mandate: {person.get('mandate', 'N/A')}
Reports to: {person.get('reports_to', 'N/A')}
""")
        
        elif intent == 'STRATEGIC_INFO':
            # Focus on mandates and strategies
            context_parts.append("=== STRATEGIC MANDATES & PRIORITIES ===")
            for result in pinecone_results[:8]:
                if 'mandate' in result.get('entity_type', '') or 'VP' in result.get('text', ''):
                    context_parts.append(result.get('text', ''))
        
        elif intent == 'MARKET_INFO':
            # Focus on regional structure
            if neo4j_results:
                regions = set()
                for person in neo4j_results:
                    region = person.get('region')
                    if region:
                        regions.add(region)
                context_parts.append(f"=== REGIONS WITH DEDICATED TEAMS ===\n{', '.join(sorted(regions))}")
        
        # Add pinecone context
        if pinecone_results and intent != 'MARKET_INFO':
            context_parts.append("\n=== ADDITIONAL CONTEXT ===")
            for result in pinecone_results[:5]:
                context_parts.append(result.get('text', ''))
        
        return "\n\n".join(context_parts)


# Export classes
__all__ = ['IntentClassifier', 'DataSourceSelector', 'AnswerFormatter']

