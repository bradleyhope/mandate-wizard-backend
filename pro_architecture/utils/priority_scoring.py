"""
Priority Scoring Utility
Calculates priority scores, scope, and seniority for entities.
"""

def determine_seniority(entity: dict) -> str:
    """
    Determine seniority level from title.
    
    Args:
        entity: Entity dict with 'attributes' containing 'title'
        
    Returns:
        str: 'c-suite', 'vp', 'director', 'manager', or 'unknown'
    """
    title = entity.get('attributes', {}).get('title', '').lower()
    
    if not title:
        return 'unknown'
    
    # C-suite indicators
    c_suite_keywords = [
        'ceo', 'cco', 'cfo', 'cto', 'coo',
        'chief', 'president', 'head of'
    ]
    if any(keyword in title for keyword in c_suite_keywords):
        return 'c-suite'
    
    # VP indicators
    vp_keywords = ['vp', 'vice president', 'svp', 'evp']
    if any(keyword in title for keyword in vp_keywords):
        return 'vp'
    
    # Director indicators
    if 'director' in title:
        return 'director'
    
    # Manager indicators
    manager_keywords = ['manager', 'executive', 'coordinator', 'lead']
    if any(keyword in title for keyword in manager_keywords):
        return 'manager'
    
    return 'unknown'


def determine_scope(entity: dict) -> str:
    """
    Determine scope of influence from title and region.
    
    Args:
        entity: Entity dict with 'attributes' containing 'title' and 'region'
        
    Returns:
        str: 'global', 'regional', or 'local'
    """
    attributes = entity.get('attributes', {})
    title = attributes.get('title', '').lower()
    region = attributes.get('region', '').lower()
    seniority = determine_seniority(entity)
    
    # C-suite is always global
    if seniority == 'c-suite':
        return 'global'
    
    # VP with "global" in title
    if seniority == 'vp' and 'global' in title:
        return 'global'
    
    # Regional indicators
    if region in ['us', 'global', 'worldwide']:
        if seniority == 'vp':
            return 'global'
        else:
            return 'regional'
    
    # Specific regions
    if region in ['uk', 'europe', 'latam', 'apac', 'mena', 'emea']:
        return 'regional'
    
    return 'local'


def calculate_priority_score(entity: dict) -> int:
    """
    Calculate priority score (0-100) based on multiple factors.
    
    Formula:
    - Seniority: 40 points (c-suite=40, vp=30, director=20, manager=10)
    - Scope: 30 points (global=30, regional=20, local=10)
    - Demand: 20 points (based on query_count)
    - Completeness: 10 points (bio, mandate, email, recent_projects)
    
    Args:
        entity: Entity dict with all attributes
        
    Returns:
        int: Priority score (0-100)
    """
    score = 0
    attributes = entity.get('attributes', {})
    
    # 1. Seniority (0-40 points)
    seniority = determine_seniority(entity)
    seniority_scores = {
        'c-suite': 40,
        'vp': 30,
        'director': 20,
        'manager': 10,
        'unknown': 0
    }
    score += seniority_scores.get(seniority, 0)
    
    # 2. Scope (0-30 points)
    scope = determine_scope(entity)
    scope_scores = {
        'global': 30,
        'regional': 20,
        'local': 10
    }
    score += scope_scores.get(scope, 0)
    
    # 3. Demand (0-20 points) - based on query_count
    query_count = entity.get('query_count', 0)
    if query_count > 1000:
        score += 20
    elif query_count > 500:
        score += 15
    elif query_count > 100:
        score += 10
    elif query_count > 10:
        score += 5
    
    # 4. Data completeness (0-10 points)
    completeness = 0
    if attributes.get('bio'):
        completeness += 3
    if attributes.get('mandate'):
        completeness += 3
    if attributes.get('email') or attributes.get('contact_hints'):
        completeness += 2
    if attributes.get('recent_greenlights') or attributes.get('recent_projects'):
        completeness += 2
    score += completeness
    
    return min(score, 100)


def calculate_all_scores(entity: dict) -> dict:
    """
    Calculate all priority-related fields for an entity.
    
    Args:
        entity: Entity dict
        
    Returns:
        dict: {
            'priority_score': int,
            'scope': str,
            'seniority': str
        }
    """
    seniority = determine_seniority(entity)
    scope = determine_scope(entity)
    priority_score = calculate_priority_score(entity)
    
    return {
        'priority_score': priority_score,
        'scope': scope,
        'seniority': seniority
    }


# Test cases
if __name__ == '__main__':
    # Test Brandon Riegg (should be high priority)
    brandon = {
        'attributes': {
            'title': 'VP of Unscripted Series and Docs',
            'region': 'US',
            'bio': 'Brandon Riegg oversees...',
            'mandate': 'Looking for...',
            'recent_greenlights': ['Beckham', 'The Kings of Tupelo']
        },
        'query_count': 1247
    }
    
    print("Brandon Riegg:")
    print(calculate_all_scores(brandon))
    print()
    
    # Test Kate Townsend (should be lower priority)
    kate = {
        'attributes': {
            'title': 'Director of Unscripted',
            'region': 'UK',
            'bio': 'Kate Townsend leads...',
            'mandate': 'Looking for...'
        },
        'query_count': 45
    }
    
    print("Kate Townsend:")
    print(calculate_all_scores(kate))
    print()
    
    # Test Ted Sarandos (should be highest priority)
    ted = {
        'attributes': {
            'title': 'Co-CEO and Chief Content Officer',
            'region': 'Global',
            'bio': 'Ted Sarandos...',
            'mandate': 'Overall content strategy...',
            'email': 'ted@netflix.com'
        },
        'query_count': 5000
    }
    
    print("Ted Sarandos:")
    print(calculate_all_scores(ted))
