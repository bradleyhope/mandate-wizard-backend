"""
Parallel Query Execution Module
Executes database queries in parallel to reduce total query time
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional
import time


class ParallelQueryExecutor:
    """Execute multiple database queries in parallel"""
    
    def __init__(self, max_workers=4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def execute_parallel(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute multiple tasks in parallel
        
        Args:
            tasks: List of task dictionaries with 'name', 'func', and 'args'
                   Example: [
                       {'name': 'vector_search', 'func': search_func, 'args': (query,)},
                       {'name': 'graph_search', 'func': graph_func, 'args': (attrs,)}
                   ]
        
        Returns:
            Dictionary mapping task names to results
        """
        start_time = time.time()
        results = {}
        futures = {}
        
        # Submit all tasks
        for task in tasks:
            future = self.executor.submit(task['func'], *task.get('args', ()), **task.get('kwargs', {}))
            futures[future] = task['name']
        
        # Collect results as they complete
        for future in as_completed(futures):
            task_name = futures[future]
            try:
                result = future.result(timeout=30)  # 30 second timeout per task
                results[task_name] = {'success': True, 'data': result, 'error': None}
                print(f"✓ {task_name} completed in {time.time() - start_time:.2f}s")
            except Exception as e:
                results[task_name] = {'success': False, 'data': None, 'error': str(e)}
                print(f"✗ {task_name} failed: {e}")
        
        total_time = time.time() - start_time
        print(f"⚡ Parallel execution completed in {total_time:.2f}s")
        
        return results
    
    def cleanup(self):
        """Cleanup executor resources"""
        self.executor.shutdown(wait=False)


def parallelize_hybrid_query(engine, question: str, intent: str, attributes: Dict) -> Dict[str, Any]:
    """
    Execute HybridRAG query components in parallel
    
    Args:
        engine: HybridRAGEnginePinecone instance
        question: User question
        intent: Classified intent
        attributes: Extracted attributes
    
    Returns:
        Dictionary with all query results
    """
    executor = ParallelQueryExecutor(max_workers=3)
    
    tasks = []
    
    # Task 1: Vector search
    tasks.append({
        'name': 'vector_search',
        'func': engine.vector_search,
        'args': (question,),
        'kwargs': {'top_k': 10}
    })
    
    # Task 2: Graph search (if relevant)
    if intent in ['ROUTING', 'STRATEGIC', 'HYBRID']:
        tasks.append({
            'name': 'graph_search',
            'func': engine.graph_search,
            'args': (attributes,)
        })
    
    # Task 3: Greenlight search (for factual queries)
    if intent in ['FACTUAL_QUERY', 'STRATEGIC', 'HYBRID']:
        def search_greenlights():
            try:
                return engine.search_greenlights(attributes)
            except:
                return []
        
        tasks.append({
            'name': 'greenlight_search',
            'func': search_greenlights,
            'args': ()
        })
    
    # Execute all tasks in parallel
    results = executor.execute_parallel(tasks)
    executor.cleanup()
    
    return results


def merge_parallel_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge parallel query results into a single structure
    
    Args:
        results: Dictionary from parallelize_hybrid_query
    
    Returns:
        Merged results dictionary
    """
    merged = {
        'vector_results': None,
        'graph_results': [],
        'greenlight_results': [],
        'errors': []
    }
    
    # Extract vector search results
    if 'vector_search' in results and results['vector_search']['success']:
        merged['vector_results'] = results['vector_search']['data']
    elif 'vector_search' in results:
        merged['errors'].append(f"Vector search failed: {results['vector_search']['error']}")
    
    # Extract graph search results
    if 'graph_search' in results and results['graph_search']['success']:
        merged['graph_results'] = results['graph_search']['data'] or []
    elif 'graph_search' in results and not results['graph_search']['success']:
        merged['errors'].append(f"Graph search failed: {results['graph_search']['error']}")
    
    # Extract greenlight search results
    if 'greenlight_search' in results and results['greenlight_search']['success']:
        merged['greenlight_results'] = results['greenlight_search']['data'] or []
    elif 'greenlight_search' in results and not results['greenlight_search']['success']:
        merged['errors'].append(f"Greenlight search failed: {results['greenlight_search']['error']}")
    
    return merged

