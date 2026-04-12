import re
from datetime import datetime, timezone
from typing import List, Dict

def calculate_keyword_score(item: Dict, ranking_config: Dict) -> float:
    text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
    score = 0.0
    
    for kw_config in ranking_config.get('high_value_keywords', []):
        keyword = kw_config.get('keyword', '').lower()
        weight = kw_config.get('weight', 2.0)
        if keyword and keyword in text:
            score += weight
    
    for kw_config in ranking_config.get('medium_value_keywords', []):
        keyword = kw_config.get('keyword', '').lower()
        weight = kw_config.get('weight', 0.5)
        if keyword and keyword in text:
            score += weight
    
    for bonus_config in ranking_config.get('bonus_patterns', []):
        pattern = bonus_config.get('pattern', '')
        weight = bonus_config.get('weight', 1.0)
        if pattern and re.search(pattern, text):
            score += weight
    
    return min(score, 10.0)

def calculate_recency_score(item: Dict) -> float:
    published = item.get('published_parsed')
    if not published:
        return 2.5
    
    try:
        pub_date = datetime(*published[:6], tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        days_old = (now - pub_date).days
        score = max(5.0 - (days_old * 0.5), 0.5)
        return score
    except Exception as e:
        print(f"[scorer] Date parse error for '{item.get('title', 'unknown')[:30]}...': {e}")
        return 2.5

def calculate_total_score(item: Dict, ranking_config: Dict) -> float:
    recency_weight = ranking_config.get('recency_weight', 0.3)
    
    keyword_score = calculate_keyword_score(item, ranking_config)
    recency_score = calculate_recency_score(item)
    
    normalized_keyword = min(keyword_score, 10.0)
    total = (normalized_keyword * (1 - recency_weight)) + (recency_score * recency_weight)
    
    return total

def rank_by_content(items: List[Dict], ranking_config: Dict) -> List[Dict]:
    scored = []
    for item in items:
        item_copy = item.copy()
        item_copy['total_score'] = calculate_total_score(item, ranking_config)
        item_copy['keyword_score'] = calculate_keyword_score(item, ranking_config)
        item_copy['recency_score'] = calculate_recency_score(item)
        scored.append(item_copy)
    
    return sorted(scored, key=lambda x: x['total_score'], reverse=True)
