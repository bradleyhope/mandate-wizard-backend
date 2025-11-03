"""
Source Tracker - Track and format source citations for AI responses
"""

from typing import List, Dict, Any
from datetime import datetime

class SourceTracker:
    """Track sources used in AI responses and format them for frontend display"""
    
    def __init__(self):
        self.sources = []
        self.source_map = {}  # Map citation numbers to source details
        self.citation_counter = 0
    
    def add_vector_source(self, metadata: Dict[str, Any], text: str, score: float) -> int:
        """Add a vector database source and return its citation number"""
        self.citation_counter += 1
        citation_num = self.citation_counter
        
        source = {
            'citation_number': citation_num,
            'source_type': 'vector',
            'entity_type': metadata.get('entity_type', 'unknown'),
            'title': metadata.get('name', 'Unknown'),
            'platform': metadata.get('platform', 'Unknown'),
            'date': metadata.get('date', metadata.get('year', 'Unknown')),
            'genre': metadata.get('genre'),
            'executive': metadata.get('executive'),
            'text_preview': text[:200] if text else '',
            'relevance_score': round(score, 2),
            'metadata': metadata
        }
        
        self.sources.append(source)
        self.source_map[citation_num] = source
        return citation_num
    
    def add_graph_source(self, person: Dict[str, Any]) -> int:
        """Add a graph database (executive) source and return its citation number"""
        self.citation_counter += 1
        citation_num = self.citation_counter
        
        source = {
            'citation_number': citation_num,
            'source_type': 'graph',
            'entity_type': 'executive',
            'title': person.get('name', 'Unknown Executive'),
            'platform': 'Netflix',  # Currently only Netflix executives in graph
            'position': person.get('current_title', 'Unknown'),
            'region': person.get('region'),
            'mandate': person.get('mandate', '')[:200] if person.get('mandate') else '',
            'metadata': person
        }
        
        self.sources.append(source)
        self.source_map[citation_num] = source
        return citation_num
    
    def add_greenlight_source(self, greenlight: Dict[str, Any]) -> int:
        """Add a Neo4j greenlight source and return its citation number"""
        self.citation_counter += 1
        citation_num = self.citation_counter
        
        source = {
            'citation_number': citation_num,
            'source_type': 'greenlight',
            'entity_type': 'greenlight',
            'title': greenlight.get('title', 'Untitled Project'),
            'platform': 'Netflix',
            'genre': greenlight.get('genre'),
            'format': greenlight.get('format'),
            'year': greenlight.get('year'),
            'date': greenlight.get('date'),
            'executive': greenlight.get('executive'),
            'talent': greenlight.get('talent'),
            'description': greenlight.get('description', '')[:200] if greenlight.get('description') else '',
            'metadata': greenlight
        }
        
        self.sources.append(source)
        self.source_map[citation_num] = source
        return citation_num
    
    def get_all_sources(self) -> List[Dict[str, Any]]:
        """Get all tracked sources"""
        return self.sources
    
    def get_source_by_citation(self, citation_num: int) -> Dict[str, Any]:
        """Get a specific source by its citation number"""
        return self.source_map.get(citation_num)
    
    def format_for_frontend(self) -> List[Dict[str, Any]]:
        """Format sources for frontend display"""
        formatted = []
        
        for source in self.sources:
            formatted_source = {
                'id': source['citation_number'],
                'type': source['entity_type'],
                'title': source['title'],
                'platform': source.get('platform', 'Unknown'),
                'metadata': {}
            }
            
            # Add type-specific metadata
            if source['source_type'] == 'vector':
                formatted_source['metadata'] = {
                    'date': source.get('date'),
                    'genre': source.get('genre'),
                    'executive': source.get('executive'),
                    'preview': source.get('text_preview'),
                    'relevance': source.get('relevance_score')
                }
            elif source['source_type'] == 'graph':
                formatted_source['metadata'] = {
                    'position': source.get('position'),
                    'region': source.get('region'),
                    'mandate': source.get('mandate')
                }
            elif source['source_type'] == 'greenlight':
                formatted_source['metadata'] = {
                    'genre': source.get('genre'),
                    'format': source.get('format'),
                    'year': source.get('year'),
                    'date': source.get('date'),
                    'executive': source.get('executive'),
                    'talent': source.get('talent'),
                    'description': source.get('description')
                }
            
            # Remove None values
            formatted_source['metadata'] = {k: v for k, v in formatted_source['metadata'].items() if v is not None}
            
            formatted.append(formatted_source)
        
        return formatted
    
    def reset(self):
        """Reset the tracker for a new query"""
        self.sources = []
        self.source_map = {}
        self.citation_counter = 0


# Global instance for easy access
_source_tracker = None

def get_source_tracker() -> SourceTracker:
    """Get or create the global source tracker instance"""
    global _source_tracker
    if _source_tracker is None:
        _source_tracker = SourceTracker()
    return _source_tracker

