"""
Answer Enhancement Module

Enhances database answers with search guidance when confidence is low.
"""

def enhance_answer_with_search_guidance(answer: str, question_analysis: dict, search_tactics: list) -> str:
    """
    Enhance a database answer with specific search guidance when we lack information.
    
    Args:
        answer: Original answer from database
        question_analysis: Analysis from IntelligentSearch
        search_tactics: Search tactics from IntelligentSearch
    
    Returns:
        Enhanced answer with search guidance
    """
    
    # Extract key information
    core_intent = question_analysis.get('core_intent', '')
    info_needed = question_analysis.get('information_needed', [])
    can_answer = question_analysis.get('can_answer_from_database', True)
    
    # If we can't answer at all, provide search guidance
    if not can_answer:
        enhanced = f"{answer}\n\n"
        enhanced += "**To find this information, I recommend searching:**\n\n"
        
        # Add specific search queries
        for i, tactic in enumerate(search_tactics[:2], 1):
            queries = tactic.get('queries', [])[:2]
            if queries:
                enhanced += f"{i}. **{tactic.get('description', 'Search')}:**\n"
                for query in queries:
                    enhanced += f"   • `{query}`\n"
                enhanced += "\n"
        
        enhanced += "**Recommended sources:**\n"
        enhanced += "• [Variety](https://variety.com) - Industry news and executive interviews\n"
        enhanced += "• [Deadline](https://deadline.com) - Greenlight announcements and deals\n"
        enhanced += "• [The Hollywood Reporter](https://hollywoodreporter.com) - Deep dives and analysis\n"
        enhanced += "• [Netflix Blog](https://about.netflix.com/en/news) - Official announcements\n"
        
        return enhanced
    
    # If we have a partial answer but low confidence, acknowledge limitations
    if "I don't have" in answer or "limited information" in answer.lower():
        enhanced = f"{answer}\n\n"
        enhanced += "**For more specific information:**\n\n"
        
        # Add targeted search suggestions
        for tactic in search_tactics[:1]:
            queries = tactic.get('queries', [])[:2]
            if queries:
                enhanced += f"Search for: `{queries[0]}`\n\n"
        
        enhanced += "This will give you recent quotes, specific examples, and detailed mandates.\n"
        
        return enhanced
    
    # Otherwise, return original answer
    return answer

