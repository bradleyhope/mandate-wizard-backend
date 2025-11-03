"""
LangGraph Workflow for 8-Layer Pathway Navigation
Stateful navigation through intelligence layers based on user persona and needs
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List, Dict, Any
from typing_extensions import TypedDict
import operator

from user_memory import UserMemoryManager
from persona_detector import PersonaDetector


class PathwayState(TypedDict):
    """State that persists across the pathway"""
    # Input
    query: str
    user_id: str
    
    # User profile
    user_profile: Dict
    project_details: Dict
    conversation_history: List[str]
    
    # Pathway navigation
    current_layer: int
    layers_needed: List[int]
    
    # Intelligence gathered
    executive_name: str
    executive_context: Dict
    production_companies: List[Dict]
    recent_greenlights: List[Dict]
    pitch_requirements: Dict
    packaging_intel: Dict
    timing_strategy: Dict
    
    # Output
    answer: str
    follow_ups: List[str]
    confidence_score: float
    sources: List[Dict]
    response_strategy: Dict


class MandateWizardPathway:
    """LangGraph workflow for persona-based pathway navigation"""
    
    def __init__(self, rag_engine):
        """
        Initialize pathway with RAG engine
        
        Args:
            rag_engine: Existing HybridRAGEngine instance
        """
        self.rag_engine = rag_engine
        self.memory = UserMemoryManager()
        self.persona_detector = PersonaDetector()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the 8-layer pathway graph"""
        workflow = StateGraph(PathwayState)
        
        # Add nodes for each layer
        workflow.add_node("detect_persona", self.detect_persona_node)
        workflow.add_node("determine_layers", self.determine_layers_node)
        workflow.add_node("layer1_routing", self.layer1_executive_routing)
        workflow.add_node("layer2_mandate", self.layer2_executive_mandate)
        workflow.add_node("layer3_prodco", self.layer3_production_companies)
        workflow.add_node("layer4_greenlights", self.layer4_recent_greenlights)
        workflow.add_node("layer5_pitch", self.layer5_pitch_requirements)
        workflow.add_node("layer6_packaging", self.layer6_packaging_intelligence)
        workflow.add_node("layer7_timing", self.layer7_timing_strategy)
        workflow.add_node("generate_answer", self.generate_answer_node)
        workflow.add_node("generate_followups", self.generate_followups_node)
        
        # Define edges (pathway flow)
        workflow.set_entry_point("detect_persona")
        workflow.add_edge("detect_persona", "determine_layers")
        
        # Conditional routing through layers
        # route_to_next_layer returns full node names like "layer1_routing", "layer2_mandate", etc.
        # Each node needs to be able to jump to ANY future layer, not just adjacent ones
        
        # All possible layer destinations
        all_layer_edges = {
            "layer1_routing": "layer1_routing",
            "layer2_mandate": "layer2_mandate",
            "layer3_prodco": "layer3_prodco",
            "layer4_greenlights": "layer4_greenlights",
            "layer5_pitch": "layer5_pitch",
            "layer6_packaging": "layer6_packaging",
            "layer7_timing": "layer7_timing",
            "generate_answer": "generate_answer"
        }
        
        workflow.add_conditional_edges(
            "determine_layers",
            self.route_to_next_layer,
            all_layer_edges
        )
        
        workflow.add_conditional_edges(
            "layer1_routing",
            self.route_to_next_layer,
            all_layer_edges
        )
        
        workflow.add_conditional_edges(
            "layer2_mandate",
            self.route_to_next_layer,
            all_layer_edges
        )
        
        workflow.add_conditional_edges(
            "layer3_prodco",
            self.route_to_next_layer,
            all_layer_edges
        )
        
        workflow.add_conditional_edges(
            "layer4_greenlights",
            self.route_to_next_layer,
            all_layer_edges
        )
        
        workflow.add_conditional_edges(
            "layer5_pitch",
            self.route_to_next_layer,
            all_layer_edges
        )
        
        workflow.add_conditional_edges(
            "layer6_packaging",
            self.route_to_next_layer,
            all_layer_edges
        )
        
        workflow.add_edge("layer7_timing", "generate_answer")
        workflow.add_edge("generate_answer", "generate_followups")
        workflow.add_edge("generate_followups", END)
        
        return workflow.compile()
    
    def detect_persona_node(self, state: PathwayState) -> PathwayState:
        """Node 0: Detect user persona and sophistication"""
        # Get user memories
        memories = self.memory.get_user_context(state['user_id'], state['query'])
        
        # Detect persona
        profile = self.persona_detector.get_user_profile(
            state['query'],
            conversation_history=state.get('conversation_history', [])
        )
        
        # Get response strategy
        response_strategy = self.persona_detector.get_response_strategy(profile)
        
        # Detect project details
        project_details = self.memory.detect_project_details(state['query'])
        
        # Store in memory for future sessions
        self.memory.add_user_context(state['user_id'], {
            'persona': profile['persona'],
            'sophistication': profile['sophistication_level'],
            **project_details
        })
        
        return {
            **state,
            'user_profile': profile,
            'project_details': project_details,
            'response_strategy': response_strategy,
            'current_layer': 0,
            'layers_needed': []
        }
    
    def determine_layers_node(self, state: PathwayState) -> PathwayState:
        """Determine which layers are needed based on query and persona"""
        query_lower = state['query'].lower()
        profile = state['user_profile']
        layers_needed = []
        
        # Layer 1 (Executive Routing) - Always needed if asking "who"
        if any(word in query_lower for word in ['who', 'which executive', 'who handles']):
            layers_needed.append(1)
        
        # Layer 2 (Mandate) - Needed for "what does X want" or novice users
        if any(phrase in query_lower for phrase in ['what does', 'what is', 'mandate', 'looking for', 'wants']):
            layers_needed.append(2)
        elif profile['sophistication_level'] == 'novice':
            layers_needed.append(2)  # Novices need mandate education
        
        # Layer 3 (Production Companies) - Needed for "how to pitch" or access questions
        if any(phrase in query_lower for phrase in ['how to pitch', 'how do i', 'production company', 'access']):
            layers_needed.append(3)
        
        # Layer 4 (Recent Greenlights) - Needed for competitive intelligence
        if any(phrase in query_lower for phrase in ['recent', 'greenlit', 'what has', 'competitive', 'pipeline']):
            layers_needed.append(4)
        
        # Layer 5 (Pitch Requirements) - Needed for pitch preparation
        if any(phrase in query_lower for phrase in ['pitch', 'format', 'requirements', 'how to present']):
            layers_needed.append(5)
        
        # Layer 6 (Packaging) - Needed for advanced users or package questions
        if any(phrase in query_lower for phrase in ['package', 'attach', 'talent', 'casting']):
            layers_needed.append(6)
        elif profile['sophistication_level'] == 'advanced' and profile['persona'] == 'producer':
            layers_needed.append(6)
        
        # Layer 7 (Timing) - Needed for strategy or crisis mode
        if profile['crisis_mode'] or any(phrase in query_lower for phrase in ['when', 'timing', 'strategy']):
            layers_needed.append(7)
        
        # If no specific layers identified, default to Layer 1 + 2
        if not layers_needed:
            layers_needed = [1, 2]
        
        # Sort layers
        layers_needed = sorted(set(layers_needed))
        
        return {
            **state,
            'layers_needed': layers_needed
        }
    
    def route_to_next_layer(self, state: PathwayState) -> str:
        """Determine which layer to visit next"""
        current = state['current_layer']
        needed = state['layers_needed']
        
        # Find next layer to visit
        next_layers = [l for l in needed if l > current]
        
        if not next_layers:
            # No more layers needed, generate answer
            return "generate_answer"
        
        next_layer = min(next_layers)
        
        # Map layer numbers to node names
        layer_map = {
            1: "layer1_routing",
            2: "layer2_mandate",
            3: "layer3_prodco",
            4: "layer4_greenlights",
            5: "layer5_pitch",
            6: "layer6_packaging",
            7: "layer7_timing"
        }
        
        return layer_map.get(next_layer, "generate_answer")
    
    def layer1_executive_routing(self, state: PathwayState) -> PathwayState:
        """Layer 1: Route to correct executive"""
        # Use existing RAG engine query method
        results = self.rag_engine.query(
            state['query'],
            conversation_history=[]
        )
        
        # Extract executive name from results
        executive_name = self._extract_executive_name(results)
        
        # Combine resources and quote cards as sources
        sources = results.get('resources', [])
        
        # Get quotes directly from data_integration if we have an executive name
        if executive_name and executive_name != "Unknown":
            try:
                # Get quotes from data integration
                quotes = self.rag_engine.data_integration.get_executive_quotes(executive_name, limit=3)
                
                # Add quotes as sources
                for quote in quotes:
                    sources.append({
                        'type': 'quote',
                        'executive': quote.get('executive', executive_name),
                        'text': quote.get('text', ''),
                        'source': quote.get('source', ''),
                        'date': quote.get('date', ''),
                        'url': quote.get('url', '')
                    })
            except Exception as e:
                # If quote retrieval fails, continue without quotes
                pass
        
        return {
            **state,
            'executive_name': executive_name,
            'executive_context': results,
            'current_layer': 1,
            'sources': sources
        }
    
    def layer2_executive_mandate(self, state: PathwayState) -> PathwayState:
        """Layer 2: Get executive mandate and taste"""
        # Executive context already retrieved in Layer 1
        # This layer would enhance with additional mandate-specific queries
        # Sources are already in state from Layer 1, just preserve them
        
        return {
            **state,
            'current_layer': 2
        }
    
    def layer3_production_companies(self, state: PathwayState) -> PathwayState:
        """Layer 3: Get production company pathway"""
        # Extract production companies from executive context
        production_companies = self._extract_production_companies(
            state.get('executive_context', {})
        )
        
        return {
            **state,
            'production_companies': production_companies,
            'current_layer': 3
        }
    
    def layer4_recent_greenlights(self, state: PathwayState) -> PathwayState:
        """Layer 4: Get recent greenlights (placeholder - database not built yet)"""
        # TODO: Query greenlights database when available
        recent_greenlights = []
        
        return {
            **state,
            'recent_greenlights': recent_greenlights,
            'current_layer': 4
        }
    
    def layer5_pitch_requirements(self, state: PathwayState) -> PathwayState:
        """Layer 5: Get pitch requirements (placeholder)"""
        # TODO: Extract pitch requirements from executive context
        pitch_requirements = {}
        
        return {
            **state,
            'pitch_requirements': pitch_requirements,
            'current_layer': 5
        }
    
    def layer6_packaging_intelligence(self, state: PathwayState) -> PathwayState:
        """Layer 6: Get packaging intelligence (placeholder)"""
        # TODO: Extract packaging patterns from successful projects
        packaging_intel = {}
        
        return {
            **state,
            'packaging_intel': packaging_intel,
            'current_layer': 6
        }
    
    def layer7_timing_strategy(self, state: PathwayState) -> PathwayState:
        """Layer 7: Get timing and strategy (placeholder)"""
        # TODO: Add timing intelligence
        timing_strategy = {}
        
        return {
            **state,
            'timing_strategy': timing_strategy,
            'current_layer': 7
        }
    
    def generate_answer_node(self, state: PathwayState) -> PathwayState:
        """Generate final answer based on collected context and user profile"""
        # Build instruction based on user profile
        profile = state['user_profile']
        strategy = state['response_strategy']
        
        # Adapt instruction based on sophistication
        if profile['sophistication_level'] == 'novice':
            instruction = """Provide an educational answer with:
1. Clear explanation of who the executive is
2. What they're looking for (mandate)
3. Step-by-step guidance on how to approach them
4. Context about the process
Use simple language and explain industry terms."""
        
        elif profile['sophistication_level'] == 'advanced':
            instruction = """Provide insider intelligence with:
1. Direct answer to the question
2. Competitive context and positioning
3. Strategic insights
4. Actionable next steps
Skip basic explanations - assume expert knowledge."""
        
        else:  # mid-level
            instruction = """Provide strategic guidance with:
1. Clear answer to the question
2. Relevant context and background
3. Practical next steps
4. Key considerations
Balance detail with actionability."""
        
        # Add crisis mode instruction
        if profile['crisis_mode']:
            instruction += f"\n\nIMPORTANT: User has a {profile['timeline']['urgency']} deadline. Prioritize speed and clarity. Give direct, actionable answer first, then supporting details."
        
        # Generate answer using existing RAG engine
        # For now, use the existing answer from executive_context
        answer = state.get('executive_context', {}).get('answer', '')
        
        # If no answer yet, this means we need to generate one
        if not answer:
            answer = "Answer generation placeholder - integrate with RAG engine"
        
        return {
            **state,
            'answer': answer,
            'confidence_score': 0.85,  # TODO: Calculate actual confidence
            'current_layer': 8
        }
    
    def generate_followups_node(self, state: PathwayState) -> PathwayState:
        """Generate pathway-based follow-ups"""
        # Use existing smart followups system
        from smart_followups import SmartFollowupGenerator
        
        generator = SmartFollowupGenerator()
        follow_ups = generator.generate_smart_followups(
            question=state['query'],
            answer=state['answer'],
            intent='ROUTING',
            attributes={}
        )
        
        return {
            **state,
            'follow_ups': follow_ups
        }
    
    def _extract_executive_name(self, results: dict) -> str:
        """Extract executive name from search results"""
        answer = results.get('answer', '')
        
        import re
        
        # Try multiple patterns in order of specificity
        # GPT-5 uses varied formats, so we need comprehensive patterns
        patterns = [
            # GPT-5 common patterns - try most specific first
            r'([A-Z][a-z]+ [A-Z][a-z]+) is your point person',     # "Don Kang is your point person"
            r'([A-Z][a-z]+ [A-Z][a-z]+) is your Korea touchpoint', # "Don Kang is your Korea touchpoint"
            r'([A-Z][a-z]+ [A-Z][a-z]+) is your lane into',        # "Don Kang is your lane into"
            r'([A-Z][a-z]+ [A-Z][a-z]+) is your path in',          # "Brandon Riegg is your path in"
            r'([A-Z][a-z]+ [A-Z][a-z]+) is your person',           # "Don Kang is your person"
            r'([A-Z][a-z]+ [A-Z][a-z]+) is your touchpoint',       # "Don Kang is your touchpoint"
            r'([A-Z][a-z]+ [A-Z][a-z]+)—[^—]+—is the Netflix',    # "Don Kang—Kang Dong-han—is the Netflix exec"
            r'([A-Z][a-z]+ [A-Z][a-z]+) is the VP',                # "Don Kang is the VP"
            r'([A-Z][a-z]+ [A-Z][a-z]+) is the Director',          # "Gabe Spitzer is the Director"
            r'([A-Z][a-z]+ [A-Z][a-z]+) oversees',                 # "Francisco Ramos oversees"
            r'([A-Z][a-z]+ [A-Z][a-z]+) leads',                    # "Francisco Ramos leads"
            r'([A-Z][a-z]+ [A-Z][a-z]+) handles',                  # "Francisco Ramos handles"
            r'([A-Z][a-z]+ [A-Z][a-z]+) manages',                  # "Francisco Ramos manages"
            r'([A-Z][a-z]+ [A-Z][a-z]+) champions',                # "Brandon Riegg champions"
            r'go to ([A-Z][a-z]+ [A-Z][a-z]+)',                    # "go to Kaata Sakamoto"
            r'connect with ([A-Z][a-z]+ [A-Z][a-z]+)',             # "connect with Don Kang"
            r'reach out to ([A-Z][a-z]+ [A-Z][a-z]+)',             # "reach out to Don Kang"
            r'contact ([A-Z][a-z]+ [A-Z][a-z]+)',                  # "contact Don Kang"
            r'\*\*([A-Z][a-z]+ [A-Z][a-z]+),',                    # "**Don Kang,"
            # Fallback: First capitalized name in answer
            r'^([A-Z][a-z]+ [A-Z][a-z]+)',                         # Name at very start
        ]
        
        for pattern in patterns:
            match = re.search(pattern, answer)
            if match:
                name = match.group(1).strip()
                # Filter out common false positives
                false_positives = [
                    'recent', 'quote', 'one of', 'the main', 'you definitely', 
                    'you want', 'your point', 'the netflix', 'the vp', 'the director',
                    'higher ground', 'analog inc', 'studio dragon', 'siren pictures'
                ]
                if not any(word in name.lower() for word in false_positives):
                    return name
        
        return "Unknown"
    
    def _extract_production_companies(self, context: dict) -> List[Dict]:
        """Extract production companies from executive context"""
        # TODO: Implement extraction logic
        # For now, return empty list
        return []
    
    def run(self, query: str, user_id: str = "anonymous") -> Dict:
        """
        Run the pathway workflow
        
        Args:
            query: User query
            user_id: User identifier
            
        Returns:
            Final state with answer and follow-ups
        """
        # Initialize state
        initial_state = {
            'query': query,
            'user_id': user_id,
            'user_profile': {},
            'project_details': {},
            'conversation_history': [],
            'current_layer': 0,
            'layers_needed': [],
            'executive_name': '',
            'executive_context': {},
            'production_companies': [],
            'recent_greenlights': [],
            'pitch_requirements': {},
            'packaging_intel': {},
            'timing_strategy': {},
            'answer': '',
            'follow_ups': [],
            'confidence_score': 0.0,
            'sources': [],
            'response_strategy': {}
        }
        
        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        return final_state


# Testing
if __name__ == "__main__":
    print("LangGraph pathway system created successfully!")
    print("\nTo test, integrate with hybridrag_engine_pinecone.py")

