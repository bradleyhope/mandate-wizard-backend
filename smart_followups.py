"""
Smart Follow-up Generator for Netflix Mandate Wizard
Generates context-aware, intelligent follow-up suggestions based on conversation history
"""

import re
from typing import List, Dict, Any

class SmartFollowupGenerator:
    """Generate intelligent, context-aware follow-up suggestions"""
    
    def __init__(self):
        """Initialize the follow-up generator"""
        pass
    
    def extract_entities_from_answer(self, answer: str) -> Dict[str, List[str]]:
        """Extract mentioned entities from the answer"""
        entities = {
            'executives': [],
            'regions': [],
            'genres': [],
            'formats': [],
            'projects': []
        }
        
        # Extract executive names (pattern: **Name, Title** or **Name**)
        exec_patterns = [
            r'\*\*([A-Z][a-z]+ [A-Z][a-z]+),\s*([^\*]+)\*\*',  # **Name, Title**
            r'\*\*([A-Z][a-z]+ [A-Z][a-z]+)\*\*',  # **Name**
        ]
        for pattern in exec_patterns:
            matches = re.findall(pattern, answer)
            for match in matches:
                name = match[0] if isinstance(match, tuple) else match
                if name and name not in entities['executives']:
                    entities['executives'].append(name)
        
        # Extract regions (common Netflix regions)
        region_keywords = {
            'Korea': ['korea', 'korean'],
            'Japan': ['japan', 'japanese'],
            'India': ['india', 'indian'],
            'UK': ['uk', 'british', 'britain'],
            'France': ['france', 'french'],
            'Germany': ['germany', 'german'],
            'Spain': ['spain', 'spanish'],
            'Italy': ['italy', 'italian'],
            'Nordics': ['nordic', 'nordics', 'scandinavia'],
            'Latin America': ['latin america', 'latam'],
            'MENA': ['mena', 'middle east'],
            'Africa': ['africa', 'african']
        }
        
        answer_lower = answer.lower()
        for region, keywords in region_keywords.items():
            if any(kw in answer_lower for kw in keywords):
                if region not in entities['regions']:
                    entities['regions'].append(region)
        
        # Extract genres
        genre_keywords = ['comedy', 'drama', 'thriller', 'action', 'sci-fi', 'horror', 
                         'romance', 'documentary', 'crime', 'family', 'animation']
        for genre in genre_keywords:
            if genre in answer_lower:
                entities['genres'].append(genre.title())
        
        # Extract formats
        format_keywords = {
            'series': ['series', 'show', 'tv'],
            'film': ['film', 'movie'],
            'documentary': ['documentary', 'doc'],
            'unscripted': ['unscripted', 'reality', 'dating', 'competition']
        }
        for fmt, keywords in format_keywords.items():
            if any(kw in answer_lower for kw in keywords):
                entities['formats'].append(fmt.title())
        
        return entities
    
    def generate_smart_followups(self, question: str, answer: str, intent: str, 
                                 attributes: Dict[str, Any], conversation_history: List = None) -> List[str]:
        """Generate 3-5 smart, context-aware follow-up suggestions"""
        followups = []
        
        # Extract entities from the answer
        entities = self.extract_entities_from_answer(answer)
        
        # Get attributes from current query
        region = attributes.get('region', '')
        genre = attributes.get('genre', '')
        fmt = attributes.get('format', '')
        
        # Generate follow-ups based on intent
        if intent == 'ROUTING':
            # User just found out WHO to pitch to
            # Suggest: Learn more about that person, their mandates, how to pitch
            
            if entities['executives']:
                exec_name = entities['executives'][0]
                followups.append(f"What are {exec_name}'s recent mandates?")
                followups.append(f"What projects has {exec_name} greenlit recently?")
                followups.append(f"How do I get a meeting with {exec_name}?")
            
            if genre:
                followups.append(f"What are examples of successful {genre} projects at Netflix?")
            
            if region and region.lower() != 'us':
                followups.append(f"What's Netflix's content strategy in {region}?")
            
            # Always useful after routing
            followups.append("What production companies work with Netflix?")
            followups.append("What's the typical pitch process?")
        
        elif intent == 'STRATEGIC':
            # User just learned WHAT Netflix wants
            # Suggest: WHO handles this, examples, other mandates
            
            if entities['executives']:
                exec_name = entities['executives'][0]
                followups.append(f"Tell me more about {exec_name}")
                followups.append(f"Who else works on {genre or fmt or 'similar content'}?")
            
            if genre:
                followups.append(f"Who should I pitch a {genre} project to?")
                followups.append(f"What are examples of successful {genre} shows?")
            
            if region:
                followups.append(f"What other mandates exist in {region}?")
            
            # Drill deeper
            followups.append("What are the most recent mandate changes?")
            followups.append("How do these mandates compare to other streamers?")
        
        elif intent == 'MARKET_INFO':
            # User just learned about markets/regions
            # Suggest: Specific region deep dives, WHO handles each region
            
            if entities['regions']:
                for region in entities['regions'][:2]:  # Top 2 regions mentioned
                    followups.append(f"Who handles content in {region}?")
                    followups.append(f"What does Netflix want in {region}?")
            
            followups.append("Which region has the biggest investment?")
            followups.append("What are the emerging markets for Netflix?")
        
        elif intent == 'FACTUAL_QUERY':
            # User asked for specific facts (greenlights, budgets, etc.)
            # Suggest: Related facts, WHO makes decisions, process questions
            
            followups.append("Who makes greenlight decisions?")
            followups.append("What's the typical development timeline?")
            
            if genre or fmt:
                followups.append(f"What are recent {genre or fmt} greenlights?")
            
            followups.append("What are the budget ranges for different formats?")
        
        elif intent == 'EXAMPLE_QUERY':
            # User wanted examples
            # Suggest: More examples, WHO commissioned them, similar projects
            
            if entities['projects']:
                followups.append("Who greenlit these projects?")
                followups.append("What made these projects successful?")
            
            if genre:
                followups.append(f"What are other successful {genre} examples?")
            
            followups.append("How can I make my project similar to these successes?")
        
        elif intent == 'PROCESS_QUERY':
            # User asked HOW to do something
            # Suggest: Related process questions, WHO to contact, specific steps
            
            followups.append("What materials do I need for a pitch?")
            followups.append("How long does the pitch process typically take?")
            followups.append("What are common reasons pitches get rejected?")
            
            if entities['executives']:
                exec_name = entities['executives'][0]
                followups.append(f"What's {exec_name}'s preferred pitch format?")
        
        elif intent == 'COMPARATIVE':
            # User is comparing things
            # Suggest: Other comparisons, deeper dives on each option
            
            if len(entities['executives']) >= 2:
                exec1, exec2 = entities['executives'][:2]
                followups.append(f"Tell me more about {exec1}")
                followups.append(f"Tell me more about {exec2}")
                followups.append("Who else works in this area?")
            
            if len(entities['regions']) >= 2:
                region1, region2 = entities['regions'][:2]
                followups.append(f"What are recent successes in {region1}?")
                followups.append(f"What are recent successes in {region2}?")
        
        else:  # HYBRID, CLARIFICATION, or other
            # Generic but useful follow-ups
            
            if entities['executives']:
                exec_name = entities['executives'][0]
                followups.append(f"Tell me more about {exec_name}")
            
            followups.append("What are Netflix's top priorities right now?")
            followups.append("Who should I pitch my project to?")
            followups.append("What markets is Netflix investing in?")
        
        # Add action-oriented suggestions if we have executives
        if entities['executives'] and len(followups) < 5:
            followups.append("How do I get an introduction to Netflix?")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_followups = []
        for f in followups:
            if f not in seen:
                seen.add(f)
                unique_followups.append(f)
        
        # Return top 5 most relevant follow-ups
        return unique_followups[:5]
    
    def generate_drill_down_questions(self, entities: Dict[str, List[str]]) -> List[str]:
        """Generate drill-down questions based on extracted entities"""
        drilldowns = []
        
        if entities['executives']:
            for exec_name in entities['executives'][:2]:
                drilldowns.append(f"What are {exec_name}'s recent projects?")
                drilldowns.append(f"What's {exec_name}'s pitch process?")
        
        if entities['regions']:
            for region in entities['regions'][:2]:
                drilldowns.append(f"What's the content strategy in {region}?")
        
        if entities['genres']:
            for genre in entities['genres'][:2]:
                drilldowns.append(f"What are successful {genre} examples?")
        
        return drilldowns[:3]

