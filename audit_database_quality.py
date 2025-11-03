"""
Database Quality Audit Script
Measures current database against defined quality standards
"""

import os
import json
from datetime import datetime, timedelta
from neo4j import GraphDatabase
from pinecone import Pinecone

# Database connections
NEO4J_URI = 'neo4j+s://0dd3462a.databases.neo4j.io'
NEO4J_USER = 'neo4j'
NEO4J_PASSWORD = 'cH-Jo3f9mcbbOr9ov-x22V7AQB3kOxxV42JJR55ZbMg'

neo4j_driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)

PINECONE_API_KEY = 'pcsk_2kvuLD_NLVH2XehCeitZUi3VCUJVkeH3KaceWniEE59Nh8f7GucxBNJDdg2eedfTaeYiD1'
PINECONE_INDEX_NAME = 'netflix-mandate-wizard'

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

class DatabaseAuditor:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "greenlights": {},
            "quotes": {},
            "deals": {},
            "people": {},
            "overall": {}
        }
        
    def calculate_greenlight_score(self, record):
        """Calculate completeness score for a greenlight"""
        score = 0
        field_status = {}
        
        # Required fields (100% total)
        weights = {
            "title": 20,
            "genre": 15,
            "format": 15,
            "streamer": 10,  # Adjusted from schema
            "executive": 20,
            "talent": 15,
            "production_company": 10,
            "date": 5
        }
        
        for field, weight in weights.items():
            value = record.get(field, "")
            is_valid = value and value not in ["", "Unknown", "None", "null"]
            if is_valid:
                score += weight
                field_status[field] = "✅"
            else:
                field_status[field] = "❌"
        
        # Bonus fields
        bonus_weights = {
            "logline": 10,
            "description": 10,
            "episode_count": 5
        }
        
        for field, weight in bonus_weights.items():
            value = record.get(field, "")
            is_valid = value and value not in ["", "Unknown", "None", "null", 0]
            if is_valid:
                score += weight
                field_status[field] = "✅ (bonus)"
        
        # Determine tier
        if score < 50:
            tier = "Critical"
        elif score < 80:
            tier = "Incomplete"
        elif score < 95:
            tier = "Complete"
        else:
            tier = "High-Quality"
        
        return {
            "score": score,
            "tier": tier,
            "field_status": field_status
        }
    
    def calculate_quote_score(self, record):
        """Calculate completeness score for a quote"""
        score = 0
        field_status = {}
        
        weights = {
            "quote": 40,
            "executive": 30,
            "context": 20,
            "source": 10
        }
        
        for field, weight in weights.items():
            value = record.get(field, "")
            is_valid = value and value not in ["", "Unknown", "None", "null", '"None"']
            if is_valid:
                score += weight
                field_status[field] = "✅"
            else:
                field_status[field] = "❌"
        
        bonus_weights = {
            "title": 10,
            "company": 10,
            "topic": 5
        }
        
        for field, weight in bonus_weights.items():
            value = record.get(field, "")
            is_valid = value and value not in ["", "Unknown", "None", "null"]
            if is_valid:
                score += weight
                field_status[field] = "✅ (bonus)"
        
        if score < 50:
            tier = "Critical"
        elif score < 80:
            tier = "Incomplete"
        elif score < 95:
            tier = "Complete"
        else:
            tier = "High-Quality"
        
        return {
            "score": score,
            "tier": tier,
            "field_status": field_status
        }
    
    def calculate_deal_score(self, record):
        """Calculate completeness score for a production deal"""
        score = 0
        field_status = {}
        
        weights = {
            "company": 25,
            "deal_type": 20,
            "platform": 15,
            "year": 10,
            "genre_focus": 15,
            "notable_projects": 15
        }
        
        for field, weight in weights.items():
            value = record.get(field, "")
            is_valid = value and value not in ["", "Unknown", "None", "null"]
            if is_valid:
                score += weight
                field_status[field] = "✅"
            else:
                field_status[field] = "❌"
        
        bonus_weights = {
            "duration": 10,
            "source": 10
        }
        
        for field, weight in bonus_weights.items():
            value = record.get(field, "")
            is_valid = value and value not in ["", "Unknown", "None", "null"]
            if is_valid:
                score += weight
                field_status[field] = "✅ (bonus)"
        
        if score < 50:
            tier = "Critical"
        elif score < 80:
            tier = "Incomplete"
        elif score < 95:
            tier = "Complete"
        else:
            tier = "High-Quality"
        
        return {
            "score": score,
            "tier": tier,
            "field_status": field_status
        }
    
    def calculate_freshness(self, date_str):
        """Calculate freshness status based on date"""
        if not date_str:
            return "Unknown"
        
        try:
            record_date = datetime.strptime(date_str, "%Y-%m-%d")
            age_days = (datetime.now() - record_date).days
            
            if age_days < 30:
                return "Fresh"
            elif age_days < 90:
                return "Aging"
            elif age_days < 180:
                return "Stale"
            else:
                return "Critical"
        except:
            return "Invalid Date"
    
    def audit_greenlights(self):
        """Audit all greenlights in Neo4j"""
        print("\n" + "="*70)
        print("📊 AUDITING GREENLIGHTS")
        print("="*70)
        
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (g:Greenlight)
                OPTIONAL MATCH (p:Person)-[r:GREENLIT]->(g)
                RETURN g, collect(p.name) as executives
            """)
            
            greenlights = []
            tier_counts = {"Critical": 0, "Incomplete": 0, "Complete": 0, "High-Quality": 0}
            freshness_counts = {"Fresh": 0, "Aging": 0, "Stale": 0, "Critical": 0, "Unknown": 0}
            total_score = 0
            orphan_count = 0
            
            for record in result:
                node = record["g"]
                executives = record["executives"]
                
                props = dict(node.items())
                props["executive"] = ", ".join(executives) if executives else ""
                
                quality = self.calculate_greenlight_score(props)
                freshness = self.calculate_freshness(props.get("date", ""))
                
                greenlights.append({
                    "title": props.get("title", "Unknown"),
                    "score": quality["score"],
                    "tier": quality["tier"],
                    "freshness": freshness,
                    "has_executive": len(executives) > 0,
                    "field_status": quality["field_status"]
                })
                
                tier_counts[quality["tier"]] += 1
                freshness_counts[freshness] += 1
                total_score += quality["score"]
                
                if len(executives) == 0:
                    orphan_count += 1
            
            total = len(greenlights)
            avg_score = total_score / total if total > 0 else 0
            
            self.results["greenlights"] = {
                "total_count": total,
                "average_score": round(avg_score, 1),
                "tier_distribution": tier_counts,
                "tier_percentages": {
                    tier: round(count / total * 100, 1) if total > 0 else 0
                    for tier, count in tier_counts.items()
                },
                "freshness_distribution": freshness_counts,
                "orphan_count": orphan_count,
                "orphan_percentage": round(orphan_count / total * 100, 1) if total > 0 else 0,
                "sample_records": greenlights[:10]  # First 10 for review
            }
            
            print(f"\n✓ Total Greenlights: {total}")
            print(f"✓ Average Score: {avg_score:.1f}%")
            print(f"\n📊 Tier Distribution:")
            for tier, count in tier_counts.items():
                pct = count / total * 100 if total > 0 else 0
                print(f"   {tier}: {count} ({pct:.1f}%)")
            
            print(f"\n⏰ Freshness Distribution:")
            for status, count in freshness_counts.items():
                pct = count / total * 100 if total > 0 else 0
                print(f"   {status}: {count} ({pct:.1f}%)")
            
            print(f"\n🔗 Orphaned Greenlights (no executive): {orphan_count} ({orphan_count/total*100:.1f}%)")
    
    def audit_quotes(self):
        """Audit all quotes in Neo4j"""
        print("\n" + "="*70)
        print("📊 AUDITING QUOTES")
        print("="*70)
        
        with neo4j_driver.session() as session:
            result = session.run("MATCH (q:Quote) RETURN q")
            
            quotes = []
            tier_counts = {"Critical": 0, "Incomplete": 0, "Complete": 0, "High-Quality": 0}
            total_score = 0
            
            for record in result:
                props = dict(record["q"].items())
                quality = self.calculate_quote_score(props)
                
                quotes.append({
                    "executive": props.get("executive", "Unknown"),
                    "score": quality["score"],
                    "tier": quality["tier"]
                })
                
                tier_counts[quality["tier"]] += 1
                total_score += quality["score"]
            
            total = len(quotes)
            avg_score = total_score / total if total > 0 else 0
            
            self.results["quotes"] = {
                "total_count": total,
                "average_score": round(avg_score, 1),
                "tier_distribution": tier_counts,
                "tier_percentages": {
                    tier: round(count / total * 100, 1) if total > 0 else 0
                    for tier, count in tier_counts.items()
                }
            }
            
            print(f"\n✓ Total Quotes: {total}")
            print(f"✓ Average Score: {avg_score:.1f}%")
            print(f"\n📊 Tier Distribution:")
            for tier, count in tier_counts.items():
                pct = count / total * 100 if total > 0 else 0
                print(f"   {tier}: {count} ({pct:.1f}%)")
    
    def audit_deals(self):
        """Audit all production deals in Neo4j"""
        print("\n" + "="*70)
        print("📊 AUDITING PRODUCTION DEALS")
        print("="*70)
        
        with neo4j_driver.session() as session:
            result = session.run("MATCH (d:ProductionDeal) RETURN d")
            
            deals = []
            tier_counts = {"Critical": 0, "Incomplete": 0, "Complete": 0, "High-Quality": 0}
            total_score = 0
            
            for record in result:
                props = dict(record["d"].items())
                quality = self.calculate_deal_score(props)
                
                deals.append({
                    "company": props.get("company", "Unknown"),
                    "score": quality["score"],
                    "tier": quality["tier"]
                })
                
                tier_counts[quality["tier"]] += 1
                total_score += quality["score"]
            
            total = len(deals)
            avg_score = total_score / total if total > 0 else 0
            
            self.results["deals"] = {
                "total_count": total,
                "average_score": round(avg_score, 1),
                "tier_distribution": tier_counts,
                "tier_percentages": {
                    tier: round(count / total * 100, 1) if total > 0 else 0
                    for tier, count in tier_counts.items()
                }
            }
            
            print(f"\n✓ Total Deals: {total}")
            print(f"✓ Average Score: {avg_score:.1f}%")
            print(f"\n📊 Tier Distribution:")
            for tier, count in tier_counts.items():
                pct = count / total * 100 if total > 0 else 0
                print(f"   {tier}: {count} ({pct:.1f}%)")
    
    def audit_pinecone(self):
        """Audit Pinecone vector database"""
        print("\n" + "="*70)
        print("📊 AUDITING PINECONE")
        print("="*70)
        
        stats = index.describe_index_stats()
        
        pinecone_results = {
            "total_vectors": stats.total_vector_count,
            "namespaces": {}
        }
        
        for namespace, info in stats.namespaces.items():
            pinecone_results["namespaces"][namespace] = {
                "vector_count": info.vector_count
            }
            print(f"\n✓ Namespace '{namespace}': {info.vector_count} vectors")
        
        self.results["pinecone"] = pinecone_results
    
    def calculate_overall_metrics(self):
        """Calculate overall database quality metrics"""
        print("\n" + "="*70)
        print("📊 OVERALL METRICS")
        print("="*70)
        
        # Weighted average (greenlights are most important)
        gl_score = self.results["greenlights"]["average_score"]
        q_score = self.results["quotes"]["average_score"]
        d_score = self.results["deals"]["average_score"]
        
        overall_score = (gl_score * 0.6 + q_score * 0.2 + d_score * 0.2)
        
        # Quality grade
        if overall_score >= 95:
            grade = "A+ (Exceptional)"
        elif overall_score >= 85:
            grade = "A (High-Quality)"
        elif overall_score >= 75:
            grade = "B (Good)"
        elif overall_score >= 65:
            grade = "C (Fair)"
        else:
            grade = "D (Needs Improvement)"
        
        self.results["overall"] = {
            "completeness_score": round(overall_score, 1),
            "grade": grade,
            "total_entities": (
                self.results["greenlights"]["total_count"] +
                self.results["quotes"]["total_count"] +
                self.results["deals"]["total_count"]
            ),
            "high_quality_percentage": round(
                (self.results["greenlights"]["tier_distribution"]["High-Quality"] +
                 self.results["quotes"]["tier_distribution"]["High-Quality"] +
                 self.results["deals"]["tier_distribution"]["High-Quality"]) /
                (self.results["greenlights"]["total_count"] +
                 self.results["quotes"]["total_count"] +
                 self.results["deals"]["total_count"]) * 100, 1
            ) if (self.results["greenlights"]["total_count"] +
                  self.results["quotes"]["total_count"] +
                  self.results["deals"]["total_count"]) > 0 else 0
        }
        
        print(f"\n✓ Overall Completeness Score: {overall_score:.1f}%")
        print(f"✓ Quality Grade: {grade}")
        print(f"✓ Total Entities: {self.results['overall']['total_entities']}")
        print(f"✓ High-Quality Entities: {self.results['overall']['high_quality_percentage']:.1f}%")
    
    def save_report(self):
        """Save audit report to JSON file"""
        filename = f"/home/ubuntu/audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n✅ Audit report saved to: {filename}")
        return filename

if __name__ == "__main__":
    auditor = DatabaseAuditor()
    
    print("="*70)
    print("🏥 MANDATE WIZARD DATABASE QUALITY AUDIT")
    print("="*70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    auditor.audit_greenlights()
    auditor.audit_quotes()
    auditor.audit_deals()
    auditor.audit_pinecone()
    auditor.calculate_overall_metrics()
    
    report_file = auditor.save_report()
    
    print("\n" + "="*70)
    print("✅ AUDIT COMPLETE")
    print("="*70)

