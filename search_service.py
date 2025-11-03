#!/usr/bin/env python3
"""
Search Service for Mandate Wizard

This script can be called externally to perform web searches and return results.
It acts as a bridge between the Flask app and the search capabilities.
"""

import sys
import json
import argparse
from intelligent_search import IntelligentSearch, score_database_confidence

def main():
    parser = argparse.ArgumentParser(description='Intelligent search service')
    parser.add_argument('--question', required=True, help='User question')
    parser.add_argument('--database-answer', help='Answer from database (optional)')
    parser.add_argument('--intent', help='Intent classification from database')
    parser.add_argument('--confidence', type=float, default=0.5, help='Database confidence score')
    
    args = parser.parse_args()
    
    # Initialize intelligent search
    searcher = IntelligentSearch()
    
    # Analyze the question
    analysis = searcher.analyze_question(args.question)
    
    # Determine if we should search
    should_search = searcher.should_use_web_search(analysis, args.confidence)
    
    # Determine search tactics
    tactics = searcher.determine_search_tactics(analysis)
    
    # Output results as JSON
    result = {
        'question_analysis': analysis,
        'should_search': should_search,
        'tactics': tactics,
        'search_queries': []
    }
    
    # Extract all search queries
    for tactic in tactics:
        result['search_queries'].extend(tactic.get('queries', []))
    
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()

