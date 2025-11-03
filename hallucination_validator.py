"""
Hallucination Validator
Post-processing layer to detect and remove hallucinated executive names from AI responses
"""

import re
from typing import Dict, List, Tuple

class HallucinationValidator:
    """Validates AI responses to prevent hallucinated executive names"""
    
    def __init__(self):
        pass
    
    def extract_names_from_context(self, context: str) -> List[str]:
        """Extract all executive names that appear in the context"""
        names = []
        
        # Look for "Executive:" field specifically
        exec_names = re.findall(r'Executive:\s*([A-Z][^\n]+)', context)
        for name in exec_names:
            # Clean up the name (remove roles like "(Co-EP)")
            name = re.sub(r'\([^)]+\)', '', name).strip()
            # Split on commas to get individual names
            for individual_name in name.split(','):
                individual_name = individual_name.strip()
                if individual_name and len(individual_name.split()) >= 2:
                    names.append(individual_name)
        
        # Look for "Talent:" field
        talent_names = re.findall(r'Talent:\s*([A-Z][^\n]+)', context)
        for name in talent_names:
            # Clean and split
            name = re.sub(r'\([^)]+\)', '', name).strip()
            for individual_name in name.split(','):
                individual_name = individual_name.strip()
                if individual_name and len(individual_name.split()) >= 2:
                    names.append(individual_name)
        
        # Look for "Name, Title" patterns (e.g., "Ryan Murphy, Producer")
        title_patterns = re.findall(r'([A-Z][a-z]+\s+[A-Z][a-z]+),\s+(?:Producer|Director|Executive|Writer|Creator|Showrunner)', context)
        names.extend(title_patterns)
        
        # Deduplicate and clean
        names = [n.strip() for n in names if n.strip()]
        return list(set(names))
    
    def extract_names_from_answer(self, answer: str) -> List[Tuple[str, int, int]]:
        """Extract all names mentioned in the answer with their positions"""
        names_with_positions = []
        
        # Expanded list of non-person phrases to skip
        skip_phrases = [
            'Netflix US', 'Amazon Studios', 'Apple TV', 'India Unscripted', 
            'Original Documentary', 'Crime Thriller', 'Limited Series', 'Crime Drama',
            'United States', 'New York', 'Los Angeles', 'United Kingdom',
            'Untitled Charlie', 'Charlie Brooker', 'Brooker Project',
            'The Beast', 'The Shards', 'Bad Influencer', 'Nobody Wants',
            'Good Thing', 'Thing Going'
        ]
        
        # Look for names in patterns like "Name, Title" or "Name (Title)"
        # This is more specific than just any two capitalized words
        for match in re.finditer(r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)(?:,\s+(?:Producer|Director|Executive|Writer|Creator|Showrunner)|\s+\((?:Producer|Director|Executive|Writer|Creator|Showrunner))', answer):
            name = match.group(1)
            if name not in skip_phrases:
                names_with_positions.append((name, match.start(), match.end()))
        
        return names_with_positions
    
    def validate_answer(self, answer: str, context: str) -> Dict:
        """
        Validate an AI answer against the provided context
        Returns dict with:
        - is_valid: bool
        - hallucinated_names: List[str]
        - cleaned_answer: str (with hallucinations removed)
        """
        context_names = self.extract_names_from_context(context)
        answer_names = self.extract_names_from_answer(answer)
        
        hallucinated_names = []
        hallucinated_last_names = []
        cleaned_answer = answer
        
        # Check each name in the answer
        for name, start, end in sorted(answer_names, key=lambda x: x[1], reverse=True):
            # Check if this name appears in the context
            if name not in context_names:
                hallucinated_names.append(name)
                # Extract last name for additional filtering
                parts = name.split()
                if len(parts) >= 2:
                    hallucinated_last_names.append(parts[-1])
                
                # Remove the hallucinated name and its surrounding sentence
                # Find the sentence boundaries
                sentence_start = answer.rfind('.', 0, start) + 1
                sentence_end = answer.find('.', end)
                if sentence_end == -1:
                    sentence_end = len(answer)
                else:
                    sentence_end += 1
                
                # Extract the sentence
                sentence = answer[sentence_start:sentence_end].strip()
                
                # Replace the sentence with a disclaimer
                disclaimer = f" [Note: Specific executive information for this area is not available in the database.] "
                
                # Only replace if the sentence heavily features the hallucinated name
                if name in sentence and sentence.count(name) >= 1:
                    cleaned_answer = cleaned_answer[:sentence_start] + disclaimer + cleaned_answer[sentence_end:]
        
        # Now remove any remaining references to hallucinated last names
        for last_name in hallucinated_last_names:
            # Replace standalone last name references with generic term
            cleaned_answer = re.sub(r'\b' + re.escape(last_name) + r"'s\b", "the executive's", cleaned_answer)
            cleaned_answer = re.sub(r'\b' + re.escape(last_name) + r'\b', "the executive", cleaned_answer)
        
        # Deduplicate hallucinated names
        hallucinated_names = list(set(hallucinated_names))
        
        # If we found hallucinations, add a general disclaimer at the end
        if hallucinated_names:
            cleaned_answer += "\n\n**Note:** This response has been filtered to remove potentially inaccurate executive names. For the most current executive contacts, please verify through industry databases or direct outreach to the company."
        
        return {
            'is_valid': len(hallucinated_names) == 0,
            'hallucinated_names': hallucinated_names,
            'cleaned_answer': cleaned_answer,
            'context_names': context_names
        }


def get_validator():
    """Get singleton validator instance"""
    if not hasattr(get_validator, '_instance'):
        get_validator._instance = HallucinationValidator()
    return get_validator._instance

