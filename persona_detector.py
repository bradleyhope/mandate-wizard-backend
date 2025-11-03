"""
Persona Detection System
Detects user sophistication level and persona type from query patterns
"""

from typing import Dict, List, Literal
import re

PersonaType = Literal['screenwriter', 'producer', 'executive', 'agent', 'business_affairs', 'director', 'talent', 'documentary']
SophisticationLevel = Literal['novice', 'mid-level', 'advanced']

class PersonaDetector:
    """Detects user persona and sophistication level from queries"""
    
    def __init__(self):
        """Initialize detection patterns"""
        
        # Novice signals - educational questions, basic inquiries
        self.novice_signals = [
            'how do i', 'where do i start', 'new to', 'first time',
            'beginner', 'help me understand', 'what is', 'explain',
            'i don\'t know', 'i\'m not sure', 'can you tell me',
            'basic', 'introduction', 'getting started'
        ]
        
        # Advanced signals - insider knowledge, strategic questions
        self.advanced_signals = [
            'competitive intelligence', 'recent greenlights', 'pipeline',
            'what has [name] greenlit', 'slate', 'positioning',
            'deal structure', 'package', 'attach', 'talent',
            'who reports to', 'org chart', 'internal', 'strategy',
            'competitive landscape', 'market positioning'
        ]
        
        # Crisis signals - time-sensitive, urgent
        self.crisis_signals = [
            'urgent', 'deadline', 'asap', 'need to decide',
            'days', 'hours', 'by [date]', 'time-sensitive',
            'quickly', 'immediately', 'tomorrow', 'this week',
            'running out of time', 'need answer now'
        ]
        
        # Persona signals - role-specific language
        self.persona_signals = {
            'screenwriter': [
                'my script', 'i wrote', 'my story', 'pitch my',
                'first screenplay', 'spec script', 'writing',
                'screenplay', 'pilot', 'treatment'
            ],
            'producer': [
                'producing', 'package', 'attach', 'financing',
                'production company', 'my project', 'develop',
                'greenlight', 'budget', 'production'
            ],
            'executive': [
                'competitive', 'slate', 'pipeline', 'greenlit',
                'development', 'our company', 'strategy',
                'portfolio', 'acquisition', 'content strategy'
            ],
            'agent': [
                'my client', 'talent', 'actor', 'represent',
                'availability', 'booking', 'roster', 'clients',
                'representation', 'agency'
            ],
            'business_affairs': [
                'deal', 'budget', 'terms', 'contract', 'negotiation',
                'financial', 'roi', 'cost', 'revenue', 'valuation',
                'economics', 'deal structure'
            ],
            'director': [
                'directing', 'my vision', 'visual', 'helming',
                'direct', 'filmmaker', 'my film', 'my show',
                'creative control'
            ],
            'talent': [
                'my role', 'acting', 'starring', 'cast',
                'audition', 'my agent', 'my manager',
                'booking', 'availability'
            ],
            'documentary': [
                'documentary', 'doc', 'nonfiction', 'real story',
                'true story', 'investigative', 'docuseries',
                'factual', 'real-life'
            ]
        }
        
        # Experience level indicators
        self.experience_indicators = {
            'novice': [
                'first', 'new', 'never', 'beginner', 'learning',
                'trying to understand', 'just starting'
            ],
            'mid-level': [
                'have experience', 'previously', 'worked on',
                'familiar with', 'some success', 'developing'
            ],
            'advanced': [
                'extensive experience', 'track record', 'portfolio',
                'previously sold', 'credits include', 'veteran',
                'established', 'successful'
            ]
        }
    
    def detect_sophistication(self, query: str, conversation_history: List[str] = None) -> SophisticationLevel:
        """
        Detect user sophistication level from query and history
        
        Args:
            query: Current user query
            conversation_history: List of previous queries
            
        Returns:
            Sophistication level: 'novice', 'mid-level', or 'advanced'
        """
        query_lower = query.lower()
        conversation_history = conversation_history or []
        
        # Check for explicit experience indicators
        for level, indicators in self.experience_indicators.items():
            if any(indicator in query_lower for indicator in indicators):
                return level
        
        # Check for novice signals
        novice_score = sum(1 for signal in self.novice_signals if signal in query_lower)
        
        # Check for advanced signals
        advanced_score = sum(1 for signal in self.advanced_signals if signal in query_lower)
        
        # Analyze conversation history if available
        if len(conversation_history) > 5:
            # Count sophisticated questions in history
            advanced_count = sum(
                1 for msg in conversation_history[-10:]
                if any(signal in msg.lower() for signal in self.advanced_signals)
            )
            if advanced_count >= 3:
                return 'advanced'
        
        # Decision logic
        if novice_score >= 2:
            return 'novice'
        elif advanced_score >= 2:
            return 'advanced'
        elif novice_score > advanced_score:
            return 'novice'
        elif advanced_score > novice_score:
            return 'advanced'
        else:
            # Default to mid-level
            return 'mid-level'
    
    def detect_persona(self, query: str, conversation_history: List[str] = None) -> PersonaType:
        """
        Detect user persona type from query patterns
        
        Args:
            query: Current user query
            conversation_history: List of previous queries
            
        Returns:
            Persona type
        """
        query_lower = query.lower()
        conversation_history = conversation_history or []
        
        # Score each persona
        scores = {}
        for persona, signals in self.persona_signals.items():
            scores[persona] = sum(1 for signal in signals if signal in query_lower)
        
        # Also check conversation history
        if conversation_history:
            for persona, signals in self.persona_signals.items():
                history_score = sum(
                    1 for msg in conversation_history[-5:]
                    if any(signal in msg.lower() for signal in signals)
                )
                scores[persona] += history_score * 0.5  # Weight history less than current query
        
        # Return persona with highest score
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        # Default to producer (most common use case)
        return 'producer'
    
    def detect_crisis_mode(self, query: str) -> bool:
        """
        Detect if user is in crisis/time-sensitive mode
        
        Args:
            query: User query
            
        Returns:
            True if crisis mode detected
        """
        query_lower = query.lower()
        return any(signal in query_lower for signal in self.crisis_signals)
    
    def extract_timeline(self, query: str) -> Dict[str, any]:
        """
        Extract timeline information from query
        
        Args:
            query: User query
            
        Returns:
            Dictionary with timeline info
        """
        query_lower = query.lower()
        
        timeline = {
            'has_deadline': False,
            'urgency': 'normal',
            'timeframe': None
        }
        
        # Check for explicit deadlines
        deadline_patterns = [
            r'(\d+)\s*(day|days|hour|hours|week|weeks)',
            r'by\s+(\w+day)',  # by Monday, Tuesday, etc.
            r'by\s+(\w+\s+\d+)',  # by October 25
            r'(tomorrow|today|tonight)',
            r'(this|next)\s+(week|month)'
        ]
        
        for pattern in deadline_patterns:
            match = re.search(pattern, query_lower)
            if match:
                timeline['has_deadline'] = True
                timeline['timeframe'] = match.group(0)
                
                # Determine urgency
                if any(word in query_lower for word in ['hour', 'hours', 'today', 'tonight', 'urgent', 'asap']):
                    timeline['urgency'] = 'critical'
                elif any(word in query_lower for word in ['day', 'days', 'tomorrow', 'this week']):
                    timeline['urgency'] = 'high'
                else:
                    timeline['urgency'] = 'medium'
                break
        
        return timeline
    
    def get_user_profile(self, query: str, conversation_history: List[str] = None) -> Dict:
        """
        Get complete user profile from query and history
        
        Args:
            query: Current user query
            conversation_history: List of previous queries
            
        Returns:
            Complete user profile dictionary
        """
        conversation_history = conversation_history or []
        
        return {
            'sophistication_level': self.detect_sophistication(query, conversation_history),
            'persona': self.detect_persona(query, conversation_history),
            'crisis_mode': self.detect_crisis_mode(query),
            'timeline': self.extract_timeline(query),
            'query_count': len(conversation_history) + 1,
            'query': query
        }
    
    def get_response_strategy(self, profile: Dict) -> Dict:
        """
        Get recommended response strategy based on user profile
        
        Args:
            profile: User profile from get_user_profile()
            
        Returns:
            Response strategy recommendations
        """
        strategy = {
            'tone': 'professional',
            'detail_level': 'medium',
            'include_education': False,
            'include_context': True,
            'include_next_steps': True,
            'prioritize_speed': False
        }
        
        # Adjust based on sophistication
        if profile['sophistication_level'] == 'novice':
            strategy['tone'] = 'educational'
            strategy['detail_level'] = 'high'
            strategy['include_education'] = True
            strategy['include_context'] = True
        elif profile['sophistication_level'] == 'advanced':
            strategy['tone'] = 'insider'
            strategy['detail_level'] = 'high'
            strategy['include_education'] = False
            strategy['include_context'] = False  # They know the context
        
        # Adjust based on crisis mode
        if profile['crisis_mode']:
            strategy['prioritize_speed'] = True
            strategy['detail_level'] = 'medium'
            strategy['include_education'] = False
            
            if profile['timeline']['urgency'] == 'critical':
                strategy['tone'] = 'direct'
                strategy['detail_level'] = 'low'  # Just the essentials
        
        # Adjust based on persona
        if profile['persona'] == 'business_affairs':
            strategy['include_numbers'] = True
            strategy['include_financials'] = True
        elif profile['persona'] == 'screenwriter':
            strategy['include_process'] = True
            strategy['include_examples'] = True
        
        return strategy


# Example usage and testing
if __name__ == "__main__":
    detector = PersonaDetector()
    
    # Test cases from the testing framework
    test_queries = [
        # Novice screenwriter
        "How do I pitch my Korean thriller series to Netflix?",
        
        # Mid-level producer
        "What production companies in Korea work with Netflix?",
        
        # Advanced executive
        "What has Don Kang greenlit in Q4 2024? I need competitive intelligence.",
        
        # Crisis mode
        "I have 72 hours to decide if I should pitch to Don Kang or Francisco Ramos. Which one?",
        
        # Business affairs
        "What are typical overall deal terms for showrunners at Netflix?",
        
        # Agent
        "My client is perfect for Netflix's Korean content. Who should I approach?"
    ]
    
    print("=== Persona Detection Tests ===\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"Test {i}: {query}")
        profile = detector.get_user_profile(query)
        strategy = detector.get_response_strategy(profile)
        
        print(f"  Sophistication: {profile['sophistication_level']}")
        print(f"  Persona: {profile['persona']}")
        print(f"  Crisis Mode: {profile['crisis_mode']}")
        print(f"  Timeline: {profile['timeline']}")
        print(f"  Response Strategy: {strategy['tone']}, {strategy['detail_level']} detail")
        print()

