"""
Data Integration Module for Netflix Mandate Wizard
Loads and indexes Task 1A (executive quotes) and Task 1B (project greenlights) data
"""

import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

class DataIntegration:
    """Load and index executive quotes and project data"""
    
    def __init__(self, quotes_dir: str = "/tmp/executive_quotes", 
                 projects_file: str = "/tmp/netflix_greenlights_master_database.json"):
        """Initialize data integration with file paths"""
        self.quotes_dir = Path(quotes_dir)
        self.projects_file = Path(projects_file)
        
        # Data stores
        self.executives = {}  # exec_name -> executive data
        self.quotes = {}  # exec_name -> list of quotes
        self.projects = []  # list of all projects
        self.projects_by_exec = {}  # exec_name -> list of projects
        
        # Load data
        self._load_executive_quotes()
        self._load_projects()
        self._build_indexes()
    
    def _load_executive_quotes(self):
        """Load all executive quote files from Task 1A with validation and error handling"""
        if not self.quotes_dir.exists():
            print(f"Warning: Quotes directory not found: {self.quotes_dir}")
            return

        loaded_count = 0
        error_count = 0

        for quote_file in self.quotes_dir.glob("*.json"):
            retry_count = 0
            max_retries = 3

            while retry_count < max_retries:
                try:
                    with open(quote_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # Validate required fields
                    exec_name = data.get('name') or data.get('executive_name', '')
                    if not exec_name:
                        print(f"Warning: No executive name in {quote_file}")
                        break

                    # Validate data types
                    if not isinstance(data, dict):
                        print(f"Warning: Invalid data format in {quote_file}")
                        break

                    # Store executive data with safe defaults
                    self.executives[exec_name.lower()] = {
                        'name': exec_name,
                        'title': str(data.get('title', '')),
                        'org': str(data.get('org', 'Netflix')),
                        'mandate_summary': str(data.get('mandate_summary', '')),
                        'key_projects': list(data.get('key_projects', [])),
                        'what_works': list(data.get('what_works', [])),
                        'what_doesnt_work': list(data.get('what_doesnt_work', [])),
                        'pitch_approach': str(data.get('pitch_approach', '')),
                    }

                    # Store quotes (handle both 'quotes' and 'direct_quotes' keys)
                    quotes_list = data.get('direct_quotes') or data.get('quotes', [])
                    if not isinstance(quotes_list, list):
                        quotes_list = []
                    self.quotes[exec_name.lower()] = quotes_list

                    loaded_count += 1
                    break  # Success, exit retry loop

                except json.JSONDecodeError as e:
                    print(f"Error: Invalid JSON in {quote_file}: {e}")
                    error_count += 1
                    break  # Don't retry JSON errors

                except Exception as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        print(f"Error loading {quote_file} after {max_retries} attempts: {e}")
                        error_count += 1
                    else:
                        print(f"Retry {retry_count}/{max_retries} for {quote_file}: {e}")

        print(f"✓ Loaded {loaded_count} executive profiles, {error_count} errors")
    
    def _load_projects(self):
        """Load all project data from Task 1B with validation and retry logic"""
        if not self.projects_file.exists():
            print(f"Warning: Projects file not found: {self.projects_file}")
            return

        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                with open(self.projects_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Validate data structure
                if not isinstance(data, dict):
                    print(f"Error: Projects file contains invalid data structure")
                    return

                # Load projects from all year-based keys (projects_2018, projects_2020, etc.)
                self.projects = []
                loaded_by_year = {}

                for key, value in data.items():
                    if key.startswith('projects_') and isinstance(value, list):
                        # Validate each project entry
                        valid_projects = []
                        for proj in value:
                            if isinstance(proj, dict) and proj.get('title'):
                                valid_projects.append(proj)
                        self.projects.extend(valid_projects)
                        year = key.replace('projects_', '')
                        loaded_by_year[year] = len(valid_projects)

                # Also check for a direct 'projects' key (fallback)
                if 'projects' in data and isinstance(data['projects'], list):
                    valid_projects = [p for p in data['projects'] if isinstance(p, dict) and p.get('title')]
                    self.projects.extend(valid_projects)
                    loaded_by_year['direct'] = len(valid_projects)

                print(f"✓ Loaded {len(self.projects)} projects from {len(loaded_by_year)} sources")
                return  # Success

            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON in projects file: {e}")
                return  # Don't retry JSON errors

            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    print(f"Error loading projects after {max_retries} attempts: {e}")
                else:
                    print(f"Retry {retry_count}/{max_retries} loading projects: {e}")
    
    def _build_indexes(self):
        """Build lookup indexes for fast access"""
        # Index projects by executive
        for project in self.projects:
            exec_name = project.get('executive', '').lower()
            if exec_name:
                if exec_name not in self.projects_by_exec:
                    self.projects_by_exec[exec_name] = []
                self.projects_by_exec[exec_name].append(project)
    
    def get_executive_quotes(self, exec_name: str, limit: int = 3) -> List[Dict]:
        """Get quotes for an executive"""
        exec_key = exec_name.lower()
        
        # Try exact match first
        if exec_key in self.quotes:
            return self.quotes[exec_key][:limit]
        
        # Try partial match
        for key, quotes in self.quotes.items():
            if exec_name.lower() in key or key in exec_name.lower():
                return quotes[:limit]
        
        return []
    
    def get_executive_projects(self, exec_name: str, limit: int = 5) -> List[Dict]:
        """Get projects greenlit by an executive"""
        exec_key = exec_name.lower()
        
        # Try exact match first
        if exec_key in self.projects_by_exec:
            return self.projects_by_exec[exec_key][:limit]
        
        # Try partial match
        for key, projects in self.projects_by_exec.items():
            if exec_name.lower() in key or key in exec_name.lower():
                return projects[:limit]
        
        return []
    
    def get_executive_data(self, exec_name: str) -> Optional[Dict]:
        """Get complete executive data"""
        exec_key = exec_name.lower()
        
        # Try exact match first
        if exec_key in self.executives:
            return self.executives[exec_key]
        
        # Try partial match
        for key, data in self.executives.items():
            if exec_name.lower() in key or key in exec_name.lower():
                return data
        
        return None
    
    def search_quotes(self, keyword: str, limit: int = 5) -> List[Dict]:
        """Search for quotes containing a keyword"""
        results = []
        keyword_lower = keyword.lower()
        
        for exec_name, quotes in self.quotes.items():
            for quote in quotes:
                quote_text = quote.get('quote', '') or quote.get('text', '')
                if keyword_lower in quote_text.lower():
                    results.append({
                        'executive': exec_name,
                        'quote': quote_text,
                        'source': quote.get('source', ''),
                        'date': quote.get('date', ''),
                        'url': quote.get('url', ''),
                        'context': quote.get('context', '')
                    })
                    
                    if len(results) >= limit:
                        return results
        
        return results
    
    def search_projects(self, keyword: str = None, region: str = None, 
                       genre: str = None, year: int = None, limit: int = 10) -> List[Dict]:
        """Search for projects by various criteria"""
        results = []
        
        for project in self.projects:
            # Apply filters
            if keyword:
                keyword_lower = keyword.lower()
                title = project.get('title', '').lower()
                description = project.get('description', '').lower()
                if keyword_lower not in title and keyword_lower not in description:
                    continue
            
            if region:
                project_region = project.get('region', '').lower()
                if region.lower() not in project_region:
                    continue
            
            if genre:
                project_genre = project.get('genre', '').lower()
                if genre.lower() not in project_genre:
                    continue
            
            if year:
                greenlight_year = project.get('greenlight_year')
                if greenlight_year != year:
                    continue
            
            results.append(project)
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about loaded data"""
        total_quotes = sum(len(quotes) for quotes in self.quotes.values())
        
        return {
            'executives': len(self.executives),
            'total_quotes': total_quotes,
            'total_projects': len(self.projects),
            'executives_with_projects': len(self.projects_by_exec)
        }
    
    def format_quote_for_answer(self, quote: Dict) -> str:
        """Format a quote for inclusion in an answer"""
        quote_text = quote.get('quote', '') or quote.get('text', '')
        source = quote.get('source', '')
        date = quote.get('date', '')
        
        # Build citation
        citation_parts = []
        if source:
            citation_parts.append(source)
        if date:
            citation_parts.append(date)
        
        citation = f" ({', '.join(citation_parts)})" if citation_parts else ""
        
        return f'> "{quote_text}"{citation}'
    
    def format_project_for_answer(self, project: Dict) -> str:
        """Format a project for inclusion in an answer"""
        title = project.get('title', 'Untitled')
        project_type = project.get('type', '')
        greenlight_date = project.get('greenlight_date', '')
        description = project.get('description', '')
        
        # Build project line
        parts = [f"**{title}**"]
        if project_type:
            parts.append(f"({project_type})")
        if greenlight_date:
            parts.append(f"- Greenlit {greenlight_date}")
        
        result = ' '.join(parts)
        
        if description and len(description) < 150:
            result += f"\n  {description}"
        
        return result
    
    def enhance_answer_with_data(self, answer: str, exec_name: str = None, 
                                 include_quotes: bool = True, 
                                 include_projects: bool = True) -> str:
        """Enhance an answer with quotes and project examples"""
        if not exec_name:
            return answer
        
        enhancements = []
        
        # Add quotes
        if include_quotes:
            quotes = self.get_executive_quotes(exec_name, limit=2)
            if quotes:
                enhancements.append("\n\n**Recent Quotes:**")
                for quote in quotes:
                    enhancements.append(self.format_quote_for_answer(quote))
        
        # Add projects
        if include_projects:
            projects = self.get_executive_projects(exec_name, limit=3)
            if projects:
                enhancements.append("\n\n**Recent Projects:**")
                for project in projects:
                    enhancements.append(self.format_project_for_answer(project))
        
        if enhancements:
            return answer + '\n'.join(enhancements)
        
        return answer
    
    def get_quote_cards(self, exec_name: str, limit: int = 2, question: str = None) -> List[Dict]:
        """
        Get structured quote card data for an executive with semantic ranking
        Returns list of quote cards with all metadata for beautiful rendering
        
        Args:
            exec_name: Executive name
            limit: Max number of quotes to return
            question: User's question for semantic ranking (if None, returns most recent)
        
        Returns:
            List of quote card dictionaries with quote, source, url, date, context
        """
        quotes = self.get_executive_quotes(exec_name, limit=10)  # Get more for ranking
        
        if not quotes:
            return []
        
        # Use semantic ranking if question provided
        if question:
            try:
                from semantic_quote_ranker import get_semantic_ranker
                ranker = get_semantic_ranker()
                quotes = ranker.rank_quotes(question, quotes, top_k=limit)
            except Exception as e:
                print(f"Semantic ranking failed, using most recent: {e}")
                # Fallback to most recent
                quotes = sorted(quotes, key=lambda q: q.get('date', ''), reverse=True)[:limit]
        else:
            # No question provided, use most recent
            quotes = sorted(quotes, key=lambda q: q.get('date', ''), reverse=True)[:limit]
        
        # Format as cards
        cards = []
        for quote in quotes:
            card = {
                'type': 'quote',
                'quote': quote.get('quote', ''),
                'source': quote.get('source', 'Unknown'),
                'url': quote.get('url', ''),
                'date': quote.get('date', ''),
                'context': quote.get('context', ''),
                'executive': exec_name
            }
            cards.append(card)
        
        return cards

# Global instance (lazy loaded)
_data_integration = None

def get_data_integration() -> DataIntegration:
    """Get or create global DataIntegration instance"""
    global _data_integration
    if _data_integration is None:
        _data_integration = DataIntegration()
    return _data_integration
