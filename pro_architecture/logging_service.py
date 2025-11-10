"""
Comprehensive logging service for Mandate Wizard.
Captures all queries, responses, and user interactions.
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class QueryLogger:
    """Logs all queries and responses with detailed metadata."""
    
    def __init__(self):
        # Set up logging directory
        self.log_dir = Path(os.environ.get("LOG_DIR", "/tmp/mandate_wizard_logs"))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up file logging
        self.setup_file_logging()
        
        # Set up structured JSON logging
        self.json_log_file = self.log_dir / "queries.jsonl"
        
        self.logger = logging.getLogger("mandate_wizard")
    
    def setup_file_logging(self):
        """Set up rotating file handler for logs."""
        log_file = self.log_dir / "mandate_wizard.log"
        
        # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()  # Also log to console
            ]
        )
    
    def log_query(
        self,
        user_email: str,
        user_name: Optional[str],
        question: str,
        response: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log a query and its response.
        
        Args:
            user_email: User's email address
            user_name: User's name (if available)
            question: The query text
            response: The complete response dict from the RAG engine
            metadata: Additional metadata (IP, user agent, etc.)
        """
        timestamp = datetime.utcnow()
        
        # Create structured log entry
        log_entry = {
            "timestamp": timestamp.isoformat(),
            "user": {
                "email": user_email,
                "name": user_name
            },
            "query": {
                "question": question,
                "length": len(question)
            },
            "response": {
                "final_answer": response.get("final_answer", ""),
                "answer_length": len(response.get("final_answer", "")),
                "confidence": response.get("confidence"),
                "entities": response.get("entities", []),
                "retrieved_count": response.get("meta", {}).get("retrieved", 0),
                "latency_ms": response.get("meta", {}).get("latency_ms", 0)
            },
            "metadata": metadata or {}
        }
        
        # Write to JSONL file (one JSON object per line)
        with open(self.json_log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        # Also log to standard logger
        self.logger.info(
            f"Query from {user_email}: '{question[:100]}...' | "
            f"Confidence: {response.get('confidence', 0):.2f} | "
            f"Latency: {response.get('meta', {}).get('latency_ms', 0)}ms"
        )
    
    def log_authentication(
        self,
        email: str,
        success: bool,
        method: str = "login",
        reason: Optional[str] = None
    ):
        """
        Log authentication attempts.
        
        Args:
            email: User's email
            success: Whether authentication succeeded
            method: Authentication method (login, magic_link, etc.)
            reason: Reason for failure (if applicable)
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "authentication",
            "email": email,
            "method": method,
            "success": success,
            "reason": reason
        }
        
        auth_log_file = self.log_dir / "auth.jsonl"
        with open(auth_log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"Auth {status}: {email} via {method}" + (f" - {reason}" if reason else ""))
    
    def log_error(
        self,
        user_email: Optional[str],
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Log errors and exceptions.
        
        Args:
            user_email: User's email (if available)
            error_type: Type of error
            error_message: Error message
            context: Additional context
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "error",
            "user_email": user_email,
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {}
        }
        
        error_log_file = self.log_dir / "errors.jsonl"
        with open(error_log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        self.logger.error(f"Error for {user_email}: {error_type} - {error_message}")
    
    def get_query_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get query statistics for the last N hours.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Dict with statistics
        """
        if not self.json_log_file.exists():
            return {"total_queries": 0}
        
        cutoff_time = datetime.utcnow().timestamp() - (hours * 3600)
        
        queries = []
        with open(self.json_log_file, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    entry_time = datetime.fromisoformat(entry["timestamp"]).timestamp()
                    if entry_time >= cutoff_time:
                        queries.append(entry)
                except:
                    continue
        
        if not queries:
            return {"total_queries": 0}
        
        # Calculate statistics
        total_queries = len(queries)
        unique_users = len(set(q["user"]["email"] for q in queries))
        avg_latency = sum(q["response"]["latency_ms"] for q in queries) / total_queries
        avg_confidence = sum(q["response"]["confidence"] or 0 for q in queries) / total_queries
        
        return {
            "total_queries": total_queries,
            "unique_users": unique_users,
            "avg_latency_ms": round(avg_latency, 2),
            "avg_confidence": round(avg_confidence, 3),
            "time_period_hours": hours
        }


# Global logger instance
_logger = None

def get_logger() -> QueryLogger:
    """Get or create the global logger instance."""
    global _logger
    if _logger is None:
        _logger = QueryLogger()
    return _logger
