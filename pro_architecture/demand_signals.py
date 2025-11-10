"""
Database Demand Signal Tracking

Tracks what users are asking for that we don't have good data on.
This helps prioritize what content to add to the database.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

class DemandSignalTracker:
    def __init__(self, log_dir: str = "/tmp/mandate_wizard_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.demand_file = self.log_dir / "demand_signals.jsonl"
    
    def log_demand(self, question: str, response: Dict[str, Any], user_email: str = None):
        """
        Log a demand signal when:
        - Low confidence (< 0.7)
        - Few results retrieved (< 3)
        - No entities found
        - Short answer (< 100 chars)
        """
        meta = response.get("meta", {})
        retrieved = meta.get("retrieved", 0)
        answer_length = len(response.get("final_answer", ""))
        entities = response.get("entities", [])
        
        # Determine if this is a demand signal
        is_demand_signal = False
        reasons = []
        
        if retrieved < 3:
            is_demand_signal = True
            reasons.append("few_results")
        
        if len(entities) == 0:
            is_demand_signal = True
            reasons.append("no_entities")
        
        if answer_length < 100:
            is_demand_signal = True
            reasons.append("short_answer")
        
        # Extract potential entities from question
        potential_entities = self._extract_entities_from_question(question)
        
        if is_demand_signal:
            signal = {
                "timestamp": datetime.utcnow().isoformat(),
                "question": question,
                "user_email": user_email,
                "reasons": reasons,
                "retrieved_docs": retrieved,
                "answer_length": answer_length,
                "entities_found": len(entities),
                "potential_entities": potential_entities,
                "category": self._categorize_question(question)
            }
            
            with open(self.demand_file, "a") as f:
                f.write(json.dumps(signal) + "\n")
    
    def _extract_entities_from_question(self, question: str) -> List[str]:
        """Extract potential entity names from question."""
        # Simple heuristic: capitalized words/phrases
        import re
        # Find sequences of capitalized words
        pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        entities = re.findall(pattern, question)
        return list(set(entities))
    
    def _categorize_question(self, question: str) -> str:
        """Categorize the type of question."""
        q_lower = question.lower()
        
        if any(word in q_lower for word in ["who", "executive", "contact", "email"]):
            return "executive_search"
        elif any(word in q_lower for word in ["mandate", "looking for", "buying", "greenlight"]):
            return "mandate_query"
        elif any(word in q_lower for word in ["deal", "production company", "producer"]):
            return "deal_query"
        elif any(word in q_lower for word in ["pitch", "how to", "strategy"]):
            return "strategy_query"
        elif any(word in q_lower for word in ["recent", "latest", "new", "announced"]):
            return "news_query"
        else:
            return "general"
    
    def get_top_demands(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get the most common demand signals."""
        if not self.demand_file.exists():
            return []
        
        signals = []
        with open(self.demand_file, "r") as f:
            for line in f:
                try:
                    signals.append(json.loads(line))
                except:
                    pass
        
        # Group by potential entities and questions
        from collections import Counter
        
        entity_counts = Counter()
        question_patterns = Counter()
        
        for signal in signals:
            for entity in signal.get("potential_entities", []):
                entity_counts[entity] += 1
            
            # Simplified question pattern
            q = signal["question"]
            if len(q) > 100:
                q = q[:100] + "..."
            question_patterns[q] += 1
        
        return {
            "top_missing_entities": entity_counts.most_common(limit),
            "top_question_patterns": question_patterns.most_common(limit),
            "total_signals": len(signals),
            "by_category": self._count_by_category(signals)
        }
    
    def _count_by_category(self, signals: List[Dict]) -> Dict[str, int]:
        """Count signals by category."""
        from collections import Counter
        categories = [s.get("category", "general") for s in signals]
        return dict(Counter(categories))
