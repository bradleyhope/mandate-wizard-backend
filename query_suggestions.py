"""
Query Suggestions
Auto-suggest queries as user types for better UX
"""

from typing import List, Dict, Any
from collections import Counter
import re


class QuerySuggestionEngine:
    """
    Generate query suggestions based on:
    1. Popular queries from analytics
    2. Template-based suggestions
    3. Autocomplete from partial queries
    """

    def __init__(self):
        """Initialize suggestion engine"""

        # Template suggestions by category
        self.templates = {
            'routing': [
                "Who should I pitch {genre} to?",
                "Who handles {genre} content at Netflix?",
                "Who should I contact about {genre} in {region}?",
                "Who greenlit {show_name}?",
                "Who is responsible for {format} content?",
            ],
            'strategic': [
                "What is {executive}'s mandate?",
                "What does {executive} look for in content?",
                "What are Netflix's priorities for {region}?",
                "What {genre} content does Netflix want?",
                "What's the strategy for {region} content?",
            ],
            'factual': [
                "Recent {genre} greenlights",
                "Latest {format} projects",
                "What {genre} shows greenlit in {year}?",
                "Recent greenlights from {executive}",
                "{region} content greenlights",
            ],
            'examples': [
                "Show me examples of {genre} pitches",
                "Examples of successful {region} shows",
                "What {genre} content works for Netflix?",
            ],
            'process': [
                "How do I pitch to {executive}?",
                "What's the pitch process for {region}?",
                "How to package a {genre} project",
            ]
        }

        # Common substitutions
        self.genres = ['thriller', 'comedy', 'drama', 'horror', 'sci-fi', 'documentary', 'romance', 'action']
        self.regions = ['UK', 'MENA', 'Korea', 'India', 'Japan', 'France', 'Nordics', 'Germany', 'Spain']
        self.formats = ['series', 'film', 'limited series', 'documentary', 'unscripted']
        self.executives = ['Brandon Riegg', 'Kennedy Corrin', 'Peter Friedlander', 'Bela Bajaria']

        # Popular queries (would be loaded from analytics)
        self.popular_queries = []

    def get_suggestions(
        self,
        partial_query: str,
        max_suggestions: int = 5,
        context: Dict[str, Any] = None
    ) -> List[Dict[str, str]]:
        """
        Get query suggestions based on partial input

        Args:
            partial_query: User's partial query
            max_suggestions: Maximum number of suggestions
            context: Context about user (tier, history, etc.)

        Returns:
            List of suggestion dicts with 'query' and 'type'
        """
        suggestions = []
        partial_lower = partial_query.lower().strip()

        # Empty or very short query - show popular/template suggestions
        if len(partial_lower) < 3:
            suggestions = self._get_starter_suggestions()
        else:
            # Match against templates
            suggestions.extend(self._match_templates(partial_lower))

            # Match against popular queries
            suggestions.extend(self._match_popular(partial_lower))

            # Generate contextual suggestions
            suggestions.extend(self._generate_contextual(partial_lower))

        # Deduplicate and limit
        seen = set()
        unique_suggestions = []
        for sugg in suggestions:
            if sugg['query'].lower() not in seen:
                seen.add(sugg['query'].lower())
                unique_suggestions.append(sugg)

        return unique_suggestions[:max_suggestions]

    def _get_starter_suggestions(self) -> List[Dict[str, str]]:
        """Get starter suggestions when query is empty"""
        return [
            {'query': 'Who should I pitch to?', 'type': 'template', 'category': 'routing'},
            {'query': 'Recent crime thriller greenlights', 'type': 'template', 'category': 'factual'},
            {'query': "What is Brandon Riegg's mandate?", 'type': 'template', 'category': 'strategic'},
            {'query': 'What does Netflix want in UK?', 'type': 'template', 'category': 'strategic'},
            {'query': 'How do I pitch to Netflix?', 'type': 'template', 'category': 'process'},
        ]

    def _match_templates(self, partial_query: str) -> List[Dict[str, str]]:
        """Match partial query against templates"""
        suggestions = []

        # Detect intent from keywords
        if any(word in partial_query for word in ['who', 'pitch', 'contact']):
            category = 'routing'
        elif any(word in partial_query for word in ['mandate', 'strategy', 'want', 'look for', 'priority']):
            category = 'strategic'
        elif any(word in partial_query for word in ['recent', 'latest', 'greenlight', 'show']):
            category = 'factual'
        elif any(word in partial_query for word in ['example', 'samples']):
            category = 'examples'
        elif any(word in partial_query for word in ['how', 'process', 'steps']):
            category = 'process'
        else:
            category = 'routing'  # Default

        # Get templates for category
        templates = self.templates.get(category, [])

        # Try to fill in templates
        for template in templates[:3]:
            filled = self._fill_template(template, partial_query)
            if filled:
                suggestions.append({
                    'query': filled,
                    'type': 'template',
                    'category': category
                })

        return suggestions

    def _fill_template(self, template: str, partial_query: str) -> str:
        """Fill template placeholders with detected values"""
        filled = template

        # Detect genre
        detected_genre = None
        for genre in self.genres:
            if genre in partial_query:
                detected_genre = genre
                break

        # Detect region
        detected_region = None
        for region in self.regions:
            if region.lower() in partial_query:
                detected_region = region
                break

        # Detect format
        detected_format = None
        for fmt in self.formats:
            if fmt in partial_query:
                detected_format = fmt
                break

        # Detect executive
        detected_exec = None
        for exec_name in self.executives:
            if exec_name.lower() in partial_query:
                detected_exec = exec_name
                break

        # Fill placeholders
        if '{genre}' in filled:
            if detected_genre:
                filled = filled.replace('{genre}', detected_genre)
            else:
                filled = filled.replace('{genre}', 'thriller')  # Default

        if '{region}' in filled:
            if detected_region:
                filled = filled.replace('{region}', detected_region)
            else:
                filled = filled.replace('{region}', 'UK')  # Default

        if '{format}' in filled:
            if detected_format:
                filled = filled.replace('{format}', detected_format)
            else:
                filled = filled.replace('{format}', 'series')

        if '{executive}' in filled:
            if detected_exec:
                filled = filled.replace('{executive}', detected_exec)
            else:
                filled = filled.replace('{executive}', 'Brandon Riegg')

        if '{year}' in filled:
            filled = filled.replace('{year}', '2024')

        if '{show_name}' in filled:
            filled = filled.replace('{show_name}', 'The Diplomat')

        return filled

    def _match_popular(self, partial_query: str) -> List[Dict[str, str]]:
        """Match against popular queries"""
        suggestions = []

        for query in self.popular_queries:
            if partial_query in query.lower():
                suggestions.append({
                    'query': query,
                    'type': 'popular',
                    'category': 'popular'
                })

        return suggestions[:2]

    def _generate_contextual(self, partial_query: str) -> List[Dict[str, str]]:
        """Generate contextual suggestions based on partial query"""
        suggestions = []

        # If mentions genre, suggest related queries
        for genre in self.genres:
            if genre in partial_query:
                suggestions.append({
                    'query': f"Recent {genre} greenlights",
                    'type': 'contextual',
                    'category': 'factual'
                })
                suggestions.append({
                    'query': f"Who handles {genre} at Netflix?",
                    'type': 'contextual',
                    'category': 'routing'
                })
                break

        # If mentions region, suggest related queries
        for region in self.regions:
            if region.lower() in partial_query:
                suggestions.append({
                    'query': f"What does Netflix want in {region}?",
                    'type': 'contextual',
                    'category': 'strategic'
                })
                break

        # If mentions executive, suggest related queries
        for exec_name in self.executives:
            if exec_name.lower() in partial_query:
                suggestions.append({
                    'query': f"What is {exec_name}'s mandate?",
                    'type': 'contextual',
                    'category': 'strategic'
                })
                suggestions.append({
                    'query': f"Recent greenlights from {exec_name}",
                    'type': 'contextual',
                    'category': 'factual'
                })
                break

        return suggestions

    def update_popular_queries(self, queries: List[str]):
        """Update popular queries from analytics"""
        self.popular_queries = queries[:20]  # Keep top 20

    def add_custom_template(self, category: str, template: str):
        """Add custom template"""
        if category not in self.templates:
            self.templates[category] = []
        self.templates[category].append(template)


# Global instance
_suggestion_engine = None


def get_suggestion_engine() -> QuerySuggestionEngine:
    """Get or create global suggestion engine"""
    global _suggestion_engine
    if _suggestion_engine is None:
        _suggestion_engine = QuerySuggestionEngine()
    return _suggestion_engine


# Example usage
if __name__ == '__main__':
    engine = QuerySuggestionEngine()

    test_queries = [
        "",
        "who",
        "who should i pitch",
        "recent crime",
        "brandon riegg",
        "uk drama",
    ]

    print("Query Suggestion Examples:\n" + "="*70)

    for partial in test_queries:
        print(f"\nPartial: '{partial}'")
        suggestions = engine.get_suggestions(partial, max_suggestions=3)

        for i, sugg in enumerate(suggestions, 1):
            print(f"  {i}. {sugg['query']}")
            print(f"     (type: {sugg['type']}, category: {sugg['category']})")
