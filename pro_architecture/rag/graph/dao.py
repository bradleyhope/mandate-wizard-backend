from __future__ import annotations
from typing import Optional, Dict, Any
from infra.neo4j_client import get_driver

class Neo4jDAO:
    def __init__(self):
        self.driver = get_driver()

    def get_person_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a person node by entity_id."""
        query = """
        MATCH (p:Person {entity_id: $entity_id})
        RETURN p.name AS name, p.title AS title, p.company AS company, p.region AS region
        LIMIT 1
        """
        with self.driver.session() as session:
            result = session.run(query, entity_id=entity_id)
            record = result.single()
            if record:
                return dict(record)
        return None

    def get_project_by_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a project node by ID."""
        query = """
        MATCH (proj:Project {id: $project_id})
        OPTIONAL MATCH (proj)-[:HAS_GENRE]->(g:Genre)
        OPTIONAL MATCH (proj)-[:HAS_FORMAT]->(f:Format)
        OPTIONAL MATCH (proj)-[:ON_PLATFORM]->(p:Platform)
        RETURN proj.title AS title, proj.description AS description,
               collect(DISTINCT g.name) AS genres,
               collect(DISTINCT f.name) AS formats,
               collect(DISTINCT p.name) AS platforms
        LIMIT 1
        """
        with self.driver.session() as session:
            result = session.run(query, project_id=project_id)
            record = result.single()
            if record:
                return dict(record)
        return None

    def get_deals_by_platform(self, platform_name: str) -> list[Dict[str, Any]]:
        """Retrieve all deals associated with a platform."""
        query = """
        MATCH (d:Deal)-[:WITH_PLATFORM]->(p:Platform {name: $platform_name})
        OPTIONAL MATCH (d)-[:INVOLVES_TALENT]->(t:Talent)
        OPTIONAL MATCH (d)-[:WITH_COMPANY]->(c:ProductionCompany)
        RETURN d.deal_type AS deal_type, d.value AS value,
               t.name AS talent_name, c.name AS company_name
        LIMIT 20
        """
        with self.driver.session() as session:
            result = session.run(query, platform_name=platform_name)
            return [dict(record) for record in result]
