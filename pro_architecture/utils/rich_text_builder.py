"""
Rich Text Builder
Builds rich text representations of entities for embedding.
"""

def build_executive_rich_text(entity: dict, cards: list = None) -> str:
    """
    Build rich text for an executive entity.
    
    Args:
        entity: Entity dict from PostgreSQL
        cards: List of card dicts for this entity
        
    Returns:
        str: Rich text representation for embedding
    """
    attributes = entity.get('attributes', {})
    name = entity.get('name', 'Unknown')
    title = attributes.get('title', '')
    company = attributes.get('company', 'Netflix')
    region = attributes.get('region', '')
    
    # Start with name and title
    text_parts = [f"{name}"]
    if title:
        text_parts.append(f"{title} at {company}")
    
    # Add region if available
    if region:
        text_parts.append(f"Region: {region}")
    
    text = "\n".join(text_parts) + "\n\n"
    
    # Add bio from attributes or cards
    bio = attributes.get('bio')
    if not bio and cards:
        # Look for bio card
        bio_cards = [c for c in cards if c.get('card_type') == 'bio']
        if bio_cards:
            bio = bio_cards[0].get('content')
    
    if bio:
        text += f"Background:\n{bio}\n\n"
    
    # Add mandate from attributes or cards
    mandate = attributes.get('mandate')
    if not mandate and cards:
        # Look for mandate card
        mandate_cards = [c for c in cards if c.get('card_type') == 'mandate']
        if mandate_cards:
            mandate = mandate_cards[0].get('content')
    
    if mandate:
        text += f"Mandate:\n{mandate}\n\n"
    
    # Add genres if available
    genres = attributes.get('genres', [])
    if genres:
        if isinstance(genres, list):
            text += f"Genres: {', '.join(genres)}\n"
        else:
            text += f"Genres: {genres}\n"
    
    # Add formats if available
    formats = attributes.get('formats', [])
    if formats:
        if isinstance(formats, list):
            text += f"Formats: {', '.join(formats)}\n"
        else:
            text += f"Formats: {formats}\n"
    
    # Add recent greenlights
    recent_greenlights = attributes.get('recent_greenlights', [])
    if recent_greenlights:
        if isinstance(recent_greenlights, list) and recent_greenlights:
            text += f"\nRecent Greenlights:\n"
            for project in recent_greenlights[:5]:  # Limit to 5
                text += f"- {project}\n"
        elif isinstance(recent_greenlights, str):
            text += f"\nRecent Greenlights: {recent_greenlights}\n"
    
    # Add contact hints if available
    contact_hints = attributes.get('contact_hints')
    if contact_hints:
        text += f"\nContact: {contact_hints}\n"
    
    return text.strip()


def build_project_rich_text(entity: dict, cards: list = None) -> str:
    """
    Build rich text for a project entity.
    
    Args:
        entity: Entity dict from PostgreSQL
        cards: List of card dicts for this entity
        
    Returns:
        str: Rich text representation for embedding
    """
    attributes = entity.get('attributes', {})
    name = entity.get('name', 'Unknown')
    
    text_parts = [f"{name}"]
    
    # Add project details
    platform = attributes.get('platform', 'Netflix')
    genre = attributes.get('genre', '')
    format_type = attributes.get('format', '')
    
    if genre:
        text_parts.append(f"Genre: {genre}")
    if format_type:
        text_parts.append(f"Format: {format_type}")
    
    text = "\n".join(text_parts) + "\n\n"
    
    # Add description
    description = attributes.get('description')
    if description:
        text += f"{description}\n\n"
    
    # Add production company
    production_company = attributes.get('production_company')
    if production_company:
        text += f"Production Company: {production_company}\n"
    
    # Add executive
    executive = attributes.get('executive')
    if executive:
        text += f"Executive: {executive}\n"
    
    # Add status
    status = attributes.get('status')
    if status:
        text += f"Status: {status}\n"
    
    # Add greenlight date
    greenlight_date = attributes.get('greenlight_date')
    if greenlight_date:
        text += f"Greenlight Date: {greenlight_date}\n"
    
    return text.strip()


def build_company_rich_text(entity: dict, cards: list = None) -> str:
    """
    Build rich text for a company entity.
    
    Args:
        entity: Entity dict from PostgreSQL
        cards: List of card dicts for this entity
        
    Returns:
        str: Rich text representation for embedding
    """
    attributes = entity.get('attributes', {})
    name = entity.get('name', 'Unknown')
    
    text = f"{name}\n\n"
    
    # Add country
    country = attributes.get('country')
    if country:
        text += f"Country: {country}\n"
    
    # Add specializations
    specializations = attributes.get('specializations', [])
    if specializations:
        if isinstance(specializations, list):
            text += f"Specializations: {', '.join(specializations)}\n"
        else:
            text += f"Specializations: {specializations}\n"
    
    # Add focus areas
    focus_areas = attributes.get('focus_areas', [])
    if focus_areas:
        if isinstance(focus_areas, list):
            text += f"Focus Areas: {', '.join(focus_areas)}\n"
        else:
            text += f"Focus Areas: {focus_areas}\n"
    
    # Add recent projects
    recent_projects = attributes.get('recent_projects', [])
    if recent_projects:
        if isinstance(recent_projects, list) and recent_projects:
            text += f"\nRecent Projects:\n"
            for project in recent_projects[:5]:
                text += f"- {project}\n"
    
    return text.strip()


def build_rich_text(entity: dict, cards: list = None) -> str:
    """
    Build rich text for any entity type.
    
    Args:
        entity: Entity dict from PostgreSQL
        cards: List of card dicts for this entity
        
    Returns:
        str: Rich text representation for embedding
    """
    entity_type = entity.get('entity_type', 'person')
    
    if entity_type == 'person':
        return build_executive_rich_text(entity, cards)
    elif entity_type == 'project':
        return build_project_rich_text(entity, cards)
    elif entity_type == 'company':
        return build_company_rich_text(entity, cards)
    else:
        # Fallback: just use name and attributes
        name = entity.get('name', 'Unknown')
        attributes = entity.get('attributes', {})
        return f"{name}\n\n{str(attributes)}"


# Test
if __name__ == '__main__':
    # Test executive
    brandon = {
        'name': 'Brandon Riegg',
        'entity_type': 'person',
        'attributes': {
            'title': 'VP of Unscripted Series and Docs',
            'company': 'Netflix',
            'region': 'US',
            'bio': 'Brandon Riegg oversees Netflix\'s global unscripted series and documentary programming, leading the team responsible for developing and producing some of the platform\'s most popular non-fiction content.',
            'mandate': 'Looking for character-driven documentary series with global appeal, true crime investigations, and innovative unscripted formats that push creative boundaries.',
            'genres': ['documentary', 'unscripted', 'true crime'],
            'formats': ['docuseries', 'limited series', 'feature documentary'],
            'recent_greenlights': ['Beckham', 'The Kings of Tupelo', 'Full Swing']
        }
    }
    
    print("Brandon Riegg Rich Text:")
    print("="*70)
    print(build_rich_text(brandon))
    print("\n" + "="*70)
    print(f"Length: {len(build_rich_text(brandon))} characters")
