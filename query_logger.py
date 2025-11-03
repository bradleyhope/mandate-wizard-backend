"""
Query Logger - Comprehensive logging system for user queries and responses
Stores all interactions for analysis and improvement
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
import threading

class QueryLogger:
    def __init__(self, db_path="query_logs.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with query logs table"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS query_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_email TEXT NOT NULL,
                    session_id TEXT,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    intent TEXT,
                    followups TEXT,
                    resources TEXT,
                    response_time_ms INTEGER,
                    token_count INTEGER,
                    vector_results_count INTEGER,
                    graph_results_count INTEGER,
                    error TEXT,
                    metadata TEXT
                )
            """)
            
            # Create indexes for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON query_logs(timestamp DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_email 
                ON query_logs(user_email)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_session 
                ON query_logs(session_id)
            """)
            
            conn.commit()
            conn.close()
    
    def log_query(self, user_email, question, answer, intent=None, 
                  followups=None, resources=None, response_time_ms=None,
                  session_id=None, vector_count=0, graph_count=0, 
                  token_count=None, error=None, metadata=None):
        """
        Log a complete query-response interaction
        
        Args:
            user_email: User's email address
            question: The user's question
            answer: The system's response
            intent: Classified intent (FACTUAL_QUERY, ROUTING, etc.)
            followups: List of follow-up questions
            resources: List of resources used
            response_time_ms: Response time in milliseconds
            session_id: Session identifier for conversation tracking
            vector_count: Number of vector search results
            graph_count: Number of graph search results
            token_count: GPT token usage
            error: Any error that occurred
            metadata: Additional metadata as dict
        """
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO query_logs (
                        timestamp, user_email, session_id, question, answer,
                        intent, followups, resources, response_time_ms, token_count,
                        vector_results_count, graph_results_count, error, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.utcnow().isoformat(),
                    user_email,
                    session_id,
                    question,
                    answer,
                    intent,
                    json.dumps(followups) if followups else None,
                    json.dumps(resources) if resources else None,
                    response_time_ms,
                    token_count,
                    vector_count,
                    graph_count,
                    error,
                    json.dumps(metadata) if metadata else None
                ))
                
                conn.commit()
                conn.close()
                
                print(f"[QueryLogger] Logged query from {user_email}: {question[:50]}...")
                
            except Exception as e:
                print(f"[QueryLogger] Error logging query: {e}")
    
    def get_recent_logs(self, limit=100, user_email=None):
        """Get recent query logs"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if user_email:
                cursor.execute("""
                    SELECT * FROM query_logs 
                    WHERE user_email = ?
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (user_email, limit))
            else:
                cursor.execute("""
                    SELECT * FROM query_logs 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
    
    def get_session_logs(self, session_id):
        """Get all logs for a specific session"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM query_logs 
                WHERE session_id = ?
                ORDER BY timestamp ASC
            """, (session_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
    
    def get_stats(self):
        """Get usage statistics"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = {}
            
            # Total queries
            cursor.execute("SELECT COUNT(*) FROM query_logs")
            stats['total_queries'] = cursor.fetchone()[0]
            
            # Unique users
            cursor.execute("SELECT COUNT(DISTINCT user_email) FROM query_logs")
            stats['unique_users'] = cursor.fetchone()[0]
            
            # Average response time
            cursor.execute("SELECT AVG(response_time_ms) FROM query_logs WHERE response_time_ms IS NOT NULL")
            stats['avg_response_time_ms'] = cursor.fetchone()[0]
            
            # Intent distribution
            cursor.execute("""
                SELECT intent, COUNT(*) as count 
                FROM query_logs 
                WHERE intent IS NOT NULL
                GROUP BY intent
            """)
            stats['intent_distribution'] = dict(cursor.fetchall())
            
            # Queries per user
            cursor.execute("""
                SELECT user_email, COUNT(*) as count 
                FROM query_logs 
                GROUP BY user_email 
                ORDER BY count DESC 
                LIMIT 10
            """)
            stats['top_users'] = [{'email': row[0], 'count': row[1]} for row in cursor.fetchall()]
            
            conn.close()
            
            return stats
    
    def export_to_json(self, output_file, limit=None):
        """Export logs to JSON file"""
        logs = self.get_recent_logs(limit=limit or 10000)
        
        with open(output_file, 'w') as f:
            json.dump(logs, f, indent=2)
        
        print(f"[QueryLogger] Exported {len(logs)} logs to {output_file}")
        return len(logs)




# Global singleton instance
_query_logger_instance = None

def get_query_logger(db_path="/home/ubuntu/mandate_wizard_web_app/query_logs.db"):
    """Get the global query logger singleton instance"""
    global _query_logger_instance
    if _query_logger_instance is None:
        _query_logger_instance = QueryLogger(db_path=db_path)
    return _query_logger_instance

