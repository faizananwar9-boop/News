from typing import List, Dict

def sort_by_priority(items: List[Dict]) -> List[Dict]:
    """Sort items by priority (highest first), then by reach."""
    
    def get_priority_score(item: Dict) -> int:
        """Calculate priority score for sorting."""
        # Get priority from item or default to 5
        priority = item.get('priority', 5)
        
        # Boost high-reach items slightly
        reach_boost = 0
        reach = item.get('reach', 'medium')
        if reach == 'high':
            reach_boost = 0.5
        elif reach == 'medium':
            reach_boost = 0.2
        
        return priority + reach_boost
    
    # Sort descending by priority score
    return sorted(items, key=get_priority_score, reverse=True)

def get_top_n(items: List[Dict], n: int = 5) -> List[Dict]:
    """Get top N items by priority."""
    sorted_items = sort_by_priority(items)
    return sorted_items[:n]

def enrich_with_source_metadata(items: List[Dict], sources_config: Dict) -> List[Dict]:
    """Add priority/reach metadata from sources config to each item."""
    enriched = []
    
    for item in items:
        connector = item.get('connector', '')
        source_label = item.get('source_label', '')
        
        # Find matching source in config
        priority = 5  # default
        reach = 'medium'  # default
        
        if connector in sources_config:
            for source in sources_config[connector]:
                if source.get('label') == source_label:
                    priority = source.get('priority', 5)
                    reach = source.get('reach', 'medium')
                    break
        
        enriched_item = item.copy()
        enriched_item['priority'] = priority
        enriched_item['reach'] = reach
        enriched.append(enriched_item)
    
    return enriched
