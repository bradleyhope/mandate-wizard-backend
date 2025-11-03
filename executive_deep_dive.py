"""
Executive Deep Dive Module for Netflix Mandate Wizard
Generates comprehensive executive profile pages
"""

from typing import Dict, List, Any, Optional
from data_integration import get_data_integration
from neo4j import GraphDatabase

class ExecutiveDeepDive:
    """Generate comprehensive executive profiles"""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        """Initialize with Neo4j connection"""
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.data_integration = get_data_integration()
    
    def generate_profile(self, exec_name: str) -> Dict[str, Any]:
        """Generate a comprehensive executive profile"""
        
        # Get data from multiple sources
        neo4j_data = self._get_neo4j_data(exec_name)
        task_data = self.data_integration.get_executive_data(exec_name)
        quotes = self.data_integration.get_executive_quotes(exec_name, limit=10)
        projects = self.data_integration.get_executive_projects(exec_name, limit=15)
        
        if not neo4j_data and not task_data:
            return {'error': 'Executive not found'}
        
        # Merge data from all sources
        profile = self._merge_data(neo4j_data, task_data)
        
        # Add quotes and projects
        profile['quotes'] = quotes
        profile['projects'] = projects
        
        # Generate formatted profile
        profile['formatted_profile'] = self._format_profile(profile)
        
        return profile
    
    def _get_neo4j_data(self, exec_name: str) -> Optional[Dict]:
        """Get executive data from Neo4j"""
        with self.driver.session() as session:
            query = """
            MATCH (p:Person)
            WHERE toLower(p.full_name) CONTAINS toLower($name) 
               OR toLower(p.name) CONTAINS toLower($name)
            OPTIONAL MATCH (p)-[:HAS_MANDATE]->(m:Mandate)
            OPTIONAL MATCH (p)-[:COMMISSIONED]->(proj:Project)
            OPTIONAL MATCH (p)-[:WORKS_IN]->(r:Region)
            OPTIONAL MATCH (p)-[:REPORTS_TO]->(boss:Person)
            OPTIONAL MATCH (direct:Person)-[:REPORTS_TO]->(p)
            RETURN p,
                   collect(DISTINCT m) as mandates,
                   collect(DISTINCT proj) as neo4j_projects,
                   collect(DISTINCT r) as regions,
                   boss,
                   collect(DISTINCT direct) as direct_reports
            LIMIT 1
            """
            
            result = session.run(query, name=exec_name)
            record = result.single()
            
            if not record:
                return None
            
            person = dict(record['p'])
            mandates = [dict(m) for m in record['mandates'] if m]
            neo4j_projects = [dict(p) for p in record['neo4j_projects'] if p]
            regions = [dict(r) for r in record['regions'] if r]
            boss = dict(record['boss']) if record['boss'] else None
            direct_reports = [dict(d) for d in record['direct_reports'] if d]
            
            return {
                'name': person.get('full_name') or person.get('name', 'Unknown'),
                'title': person.get('title', 'Unknown'),
                'org': person.get('org', 'Netflix'),
                'seniority': person.get('seniority', 'Unknown'),
                'mandate_summary': person.get('mandate_summary', ''),
                'mandates': mandates,
                'neo4j_projects': neo4j_projects,
                'regions': regions,
                'boss': boss,
                'direct_reports': direct_reports
            }
    
    def _merge_data(self, neo4j_data: Optional[Dict], task_data: Optional[Dict]) -> Dict:
        """Merge data from Neo4j and Task 1A/1B"""
        profile = {}
        
        # Start with Neo4j data if available
        if neo4j_data:
            profile.update(neo4j_data)
        
        # Override/enhance with Task data if available
        if task_data:
            for key, value in task_data.items():
                if value and (key not in profile or not profile[key]):
                    profile[key] = value
        
        return profile
    
    def _format_profile(self, profile: Dict) -> str:
        """Format profile as markdown"""
        lines = []
        
        # Header
        name = profile.get('name', 'Unknown Executive')
        title = profile.get('title', '')
        org = profile.get('org', 'Netflix')
        
        lines.append(f"# {name}")
        if title:
            lines.append(f"## {title}")
        if org and org != 'Netflix':
            lines.append(f"### {org}")
        
        lines.append("")
        
        # Mandate Summary
        mandate = profile.get('mandate_summary', '')
        if mandate:
            lines.append("## 📋 Mandate")
            lines.append(mandate)
            lines.append("")
        
        # Reporting Structure
        boss = profile.get('boss')
        direct_reports = profile.get('direct_reports', [])
        
        if boss or direct_reports:
            lines.append("## 👥 Reporting Structure")
            
            if boss:
                boss_name = boss.get('full_name') or boss.get('name', 'Unknown')
                boss_title = boss.get('title', '')
                lines.append(f"**Reports to:** {boss_name}")
                if boss_title:
                    lines.append(f"  ({boss_title})")
            
            if direct_reports:
                lines.append(f"\n**Direct Reports:** {len(direct_reports)}")
                for dr in direct_reports[:5]:  # Show first 5
                    dr_name = dr.get('full_name') or dr.get('name', 'Unknown')
                    dr_title = dr.get('title', '')
                    lines.append(f"- {dr_name}" + (f" ({dr_title})" if dr_title else ""))
            
            lines.append("")
        
        # Regional Coverage
        regions = profile.get('regions', [])
        if regions:
            lines.append("## 🌍 Regional Coverage")
            region_names = [r.get('name', '') for r in regions if r.get('name')]
            lines.append(", ".join(region_names))
            lines.append("")
        
        # What Works / What Doesn't
        what_works = profile.get('what_works', [])
        what_doesnt = profile.get('what_doesnt_work', [])
        
        if what_works:
            lines.append("## ✅ What Works")
            for item in what_works:
                lines.append(f"- {item}")
            lines.append("")
        
        if what_doesnt:
            lines.append("## ❌ What Doesn't Work")
            for item in what_doesnt:
                lines.append(f"- {item}")
            lines.append("")
        
        # Recent Quotes
        quotes = profile.get('quotes', [])
        if quotes:
            lines.append("## 💬 Recent Quotes")
            for quote in quotes[:5]:  # Show first 5
                quote_text = quote.get('quote', '') or quote.get('text', '')
                source = quote.get('source', '')
                date = quote.get('date', '')
                url = quote.get('url', '')
                
                lines.append(f"\n> \"{quote_text}\"")
                
                citation_parts = []
                if source:
                    citation_parts.append(source)
                if date:
                    citation_parts.append(date)
                
                if citation_parts:
                    citation = ", ".join(citation_parts)
                    if url:
                        lines.append(f">\n> — [{citation}]({url})")
                    else:
                        lines.append(f">\n> — {citation}")
            
            lines.append("")
        
        # Recent Projects
        projects = profile.get('projects', [])
        if projects:
            lines.append("## 🎬 Recent Projects")
            
            # Group by year
            by_year = {}
            for project in projects:
                year = project.get('greenlight_year', 'Unknown')
                if year not in by_year:
                    by_year[year] = []
                by_year[year].append(project)
            
            # Sort years descending
            for year in sorted(by_year.keys(), reverse=True):
                if year != 'Unknown':
                    lines.append(f"\n### {year}")
                
                for project in by_year[year][:10]:  # Max 10 per year
                    title = project.get('title', 'Untitled')
                    project_type = project.get('type', '')
                    description = project.get('description', '')
                    
                    line = f"- **{title}**"
                    if project_type:
                        line += f" ({project_type})"
                    
                    lines.append(line)
                    
                    if description and len(description) < 200:
                        lines.append(f"  {description}")
            
            lines.append("")
        
        # Pitch Approach
        pitch_approach = profile.get('pitch_approach', '')
        if pitch_approach:
            lines.append("## 🎯 Pitch Approach")
            lines.append(pitch_approach)
            lines.append("")
        
        # Key Projects (from Task data)
        key_projects = profile.get('key_projects', [])
        if key_projects and not projects:  # Only show if we don't have recent projects
            lines.append("## 🌟 Key Projects")
            for project in key_projects:
                if isinstance(project, str):
                    lines.append(f"- {project}")
                elif isinstance(project, dict):
                    lines.append(f"- **{project.get('title', 'Unknown')}**")
                    if project.get('description'):
                        lines.append(f"  {project['description']}")
            lines.append("")
        
        return "\n".join(lines)
    
    def list_all_executives(self) -> List[Dict[str, str]]:
        """List all executives with basic info"""
        executives = []
        
        # Get from Task 1A data
        for exec_name, exec_data in self.data_integration.executives.items():
            executives.append({
                'name': exec_data.get('name', exec_name),
                'title': exec_data.get('title', ''),
                'org': exec_data.get('org', 'Netflix')
            })
        
        # Sort by name
        executives.sort(key=lambda x: x['name'])
        
        return executives
    
    def close(self):
        """Close Neo4j connection"""
        self.driver.close()

