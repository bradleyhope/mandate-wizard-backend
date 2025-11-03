"""
Comparison Engine for Netflix Mandate Wizard
Enables side-by-side comparison of executives, regions, genres, etc.
"""

from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase
from openai import OpenAI
import os

class ComparisonEngine:
    """Compare executives, regions, genres, and other entities"""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        """Initialize comparison engine with Neo4j connection"""
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        # Initialize OpenAI client
        openai_api_key = os.environ.get('MY_OPENAI_API_KEY') or os.environ.get('OPENAI_API_KEY')
        self.llm = OpenAI(api_key=openai_api_key)
    
    def compare_executives(self, exec1_name: str, exec2_name: str) -> Dict[str, Any]:
        """Compare two executives side-by-side"""
        
        # Get data for both executives from Neo4j
        exec1_data = self._get_executive_data(exec1_name)
        exec2_data = self._get_executive_data(exec2_name)
        
        if not exec1_data or not exec2_data:
            return {
                'error': 'One or both executives not found',
                'exec1_found': bool(exec1_data),
                'exec2_found': bool(exec2_data)
            }
        
        # Generate comparison using LLM
        comparison = self._generate_executive_comparison(exec1_data, exec2_data)
        
        return {
            'exec1': exec1_data,
            'exec2': exec2_data,
            'comparison': comparison,
            'comparison_type': 'executives'
        }
    
    def compare_regions(self, region1: str, region2: str) -> Dict[str, Any]:
        """Compare two regions' content strategies"""
        
        # Get regional data from Neo4j
        region1_data = self._get_region_data(region1)
        region2_data = self._get_region_data(region2)
        
        if not region1_data or not region2_data:
            return {
                'error': 'One or both regions not found',
                'region1_found': bool(region1_data),
                'region2_found': bool(region2_data)
            }
        
        # Generate comparison
        comparison = self._generate_region_comparison(region1_data, region2_data)
        
        return {
            'region1': region1_data,
            'region2': region2_data,
            'comparison': comparison,
            'comparison_type': 'regions'
        }
    
    def compare_genres(self, genre1: str, genre2: str) -> Dict[str, Any]:
        """Compare two genres' mandates and executives"""
        
        # Get genre data from Neo4j
        genre1_data = self._get_genre_data(genre1)
        genre2_data = self._get_genre_data(genre2)
        
        if not genre1_data or not genre2_data:
            return {
                'error': 'One or both genres not found',
                'genre1_found': bool(genre1_data),
                'genre2_found': bool(genre2_data)
            }
        
        # Generate comparison
        comparison = self._generate_genre_comparison(genre1_data, genre2_data)
        
        return {
            'genre1': genre1_data,
            'genre2': genre2_data,
            'comparison': comparison,
            'comparison_type': 'genres'
        }
    
    def _get_executive_data(self, exec_name: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive data for an executive from Neo4j"""
        with self.driver.session() as session:
            query = """
            MATCH (p:Person)
            WHERE toLower(p.full_name) CONTAINS toLower($name) 
               OR toLower(p.name) CONTAINS toLower($name)
            OPTIONAL MATCH (p)-[:HAS_MANDATE]->(m:Mandate)
            OPTIONAL MATCH (p)-[:COMMISSIONED]->(proj:Project)
            OPTIONAL MATCH (p)-[:WORKS_IN]->(r:Region)
            RETURN p, 
                   collect(DISTINCT m) as mandates,
                   collect(DISTINCT proj) as projects,
                   collect(DISTINCT r) as regions
            LIMIT 1
            """
            
            result = session.run(query, name=exec_name)
            record = result.single()
            
            if not record:
                return None
            
            person = dict(record['p'])
            mandates = [dict(m) for m in record['mandates'] if m]
            projects = [dict(p) for p in record['projects'] if p]
            regions = [dict(r) for r in record['regions'] if r]
            
            return {
                'name': person.get('full_name') or person.get('name', 'Unknown'),
                'title': person.get('title', 'Unknown'),
                'org': person.get('org', 'Netflix'),
                'mandate_summary': person.get('mandate_summary', ''),
                'mandates': mandates,
                'projects': projects,
                'regions': regions,
                'seniority': person.get('seniority', 'Unknown')
            }
    
    def _get_region_data(self, region_name: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive data for a region from Neo4j"""
        with self.driver.session() as session:
            query = """
            MATCH (r:Region)
            WHERE toLower(r.name) CONTAINS toLower($region)
            OPTIONAL MATCH (p:Person)-[:WORKS_IN]->(r)
            OPTIONAL MATCH (proj:Project)-[:TARGETS_REGION]->(r)
            OPTIONAL MATCH (m:Mandate)-[:APPLIES_TO_REGION]->(r)
            RETURN r,
                   collect(DISTINCT p) as executives,
                   collect(DISTINCT proj) as projects,
                   collect(DISTINCT m) as mandates
            LIMIT 1
            """
            
            result = session.run(query, region=region_name)
            record = result.single()
            
            if not record:
                return None
            
            region = dict(record['r'])
            executives = [dict(p) for p in record['executives'] if p]
            projects = [dict(p) for p in record['projects'] if p]
            mandates = [dict(m) for m in record['mandates'] if m]
            
            return {
                'name': region.get('name', region_name),
                'description': region.get('description', ''),
                'executives': executives,
                'projects': projects,
                'mandates': mandates,
                'investment_level': region.get('investment_level', 'Unknown')
            }
    
    def _get_genre_data(self, genre_name: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive data for a genre from Neo4j"""
        with self.driver.session() as session:
            query = """
            MATCH (g:Genre)
            WHERE toLower(g.name) CONTAINS toLower($genre)
            OPTIONAL MATCH (p:Person)-[:HANDLES_GENRE]->(g)
            OPTIONAL MATCH (proj:Project)-[:HAS_GENRE]->(g)
            OPTIONAL MATCH (m:Mandate)-[:APPLIES_TO_GENRE]->(g)
            RETURN g,
                   collect(DISTINCT p) as executives,
                   collect(DISTINCT proj) as projects,
                   collect(DISTINCT m) as mandates
            LIMIT 1
            """
            
            result = session.run(query, genre=genre_name)
            record = result.single()
            
            if not record:
                return None
            
            genre = dict(record['g'])
            executives = [dict(p) for p in record['executives'] if p]
            projects = [dict(p) for p in record['projects'] if p]
            mandates = [dict(m) for m in record['mandates'] if m]
            
            return {
                'name': genre.get('name', genre_name),
                'description': genre.get('description', ''),
                'executives': executives,
                'projects': projects,
                'mandates': mandates
            }
    
    def _generate_executive_comparison(self, exec1: Dict, exec2: Dict) -> str:
        """Generate natural language comparison of two executives"""
        
        prompt = f"""Compare these two Netflix executives in a clear, structured way:

**Executive 1: {exec1['name']}**
- Title: {exec1['title']}
- Mandate: {exec1.get('mandate_summary', 'Not available')}
- Projects: {len(exec1.get('projects', []))} projects
- Regions: {', '.join([r.get('name', '') for r in exec1.get('regions', [])])}

**Executive 2: {exec2['name']}**
- Title: {exec2['title']}
- Mandate: {exec2.get('mandate_summary', 'Not available')}
- Projects: {len(exec2.get('projects', []))} projects
- Regions: {', '.join([r.get('name', '') for r in exec2.get('regions', [])])}

Provide a structured comparison covering:
1. **Scope & Seniority**: Who has broader authority?
2. **Content Focus**: What types of content does each handle?
3. **Regional Coverage**: Geographic differences
4. **When to Pitch Each**: Clear guidance on which exec for which type of project

Keep it concise and actionable. Use bullet points."""

        response = self.llm.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are an expert on Netflix's executive structure. Provide clear, actionable comparisons."},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=800
        )
        
        return response.choices[0].message.content
    
    def _generate_region_comparison(self, region1: Dict, region2: Dict) -> str:
        """Generate natural language comparison of two regions"""
        
        prompt = f"""Compare Netflix's content strategy in these two regions:

**Region 1: {region1['name']}**
- Executives: {len(region1.get('executives', []))} executives
- Projects: {len(region1.get('projects', []))} projects
- Investment: {region1.get('investment_level', 'Unknown')}

**Region 2: {region2['name']}**
- Executives: {len(region2.get('executives', []))} executives
- Projects: {len(region2.get('projects', []))} projects
- Investment: {region2.get('investment_level', 'Unknown')}

Provide a structured comparison covering:
1. **Investment Level**: Which region gets more resources?
2. **Content Strategy**: Different approaches or priorities
3. **Market Maturity**: Established vs emerging
4. **Opportunities**: Which region might be better for new creators?

Keep it concise and actionable."""

        response = self.llm.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are an expert on Netflix's global content strategy."},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=800
        )
        
        return response.choices[0].message.content
    
    def _generate_genre_comparison(self, genre1: Dict, genre2: Dict) -> str:
        """Generate natural language comparison of two genres"""
        
        prompt = f"""Compare Netflix's approach to these two genres:

**Genre 1: {genre1['name']}**
- Executives: {len(genre1.get('executives', []))} executives
- Projects: {len(genre1.get('projects', []))} projects

**Genre 2: {genre2['name']}**
- Executives: {len(genre2.get('executives', []))} executives
- Projects: {len(genre2.get('projects', []))} projects

Provide a structured comparison covering:
1. **Priority Level**: Which genre is Netflix investing in more?
2. **Competition**: Which is more saturated?
3. **Success Patterns**: What works in each genre?
4. **Pitch Guidance**: Tips for each genre

Keep it concise and actionable."""

        response = self.llm.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are an expert on Netflix's content mandates and genre strategies."},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=800
        )
        
        return response.choices[0].message.content
    
    def detect_comparison_intent(self, question: str) -> Optional[Dict[str, Any]]:
        """Detect if a question is asking for a comparison"""
        
        question_lower = question.lower()
        
        # Comparison keywords
        comparison_keywords = [
            'compare', 'comparison', 'difference between', 'vs', 'versus',
            'which is better', 'should i pitch to', 'or', 'between'
        ]
        
        if not any(kw in question_lower for kw in comparison_keywords):
            return None
        
        # Try to extract entities being compared
        # This is a simple heuristic - could be improved with NER
        
        # Pattern: "compare X and Y" or "X vs Y"
        import re
        
        # Try various patterns
        patterns = [
            r'compare\s+([^and]+)\s+and\s+([^?]+)',
            r'([^vs]+)\s+vs\.?\s+([^?]+)',
            r'difference between\s+([^and]+)\s+and\s+([^?]+)',
            r'([^or]+)\s+or\s+([^?]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, question_lower, re.IGNORECASE)
            if match:
                entity1 = match.group(1).strip()
                entity2 = match.group(2).strip()
                
                # Determine comparison type
                comparison_type = self._determine_comparison_type(entity1, entity2, question)
                
                return {
                    'is_comparison': True,
                    'entity1': entity1,
                    'entity2': entity2,
                    'comparison_type': comparison_type
                }
        
        return None
    
    def _determine_comparison_type(self, entity1: str, entity2: str, question: str) -> str:
        """Determine if comparing executives, regions, or genres"""
        
        question_lower = question.lower()
        
        # Check for executive indicators
        exec_indicators = ['executive', 'vp', 'director', 'manager', 'who', 'pitch to']
        if any(ind in question_lower for ind in exec_indicators):
            return 'executives'
        
        # Check for region indicators
        region_indicators = ['region', 'country', 'market', 'korea', 'uk', 'us', 'japan', 'india']
        if any(ind in question_lower for ind in region_indicators):
            return 'regions'
        
        # Check for genre indicators
        genre_indicators = ['genre', 'comedy', 'drama', 'thriller', 'action', 'horror']
        if any(ind in question_lower for ind in genre_indicators):
            return 'genres'
        
        # Default to executives
        return 'executives'
    
    def close(self):
        """Close Neo4j connection"""
        self.driver.close()

