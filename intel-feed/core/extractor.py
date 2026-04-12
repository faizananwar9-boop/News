import re
from difflib import SequenceMatcher
from typing import List, Dict, Optional, Tuple

def extract_and_format_robust(raw_output: str, original_items: List[Dict]) -> Optional[str]:
    """Extract formatted lines with multiple fallback strategies."""
    lines = raw_output.strip().split('\n')
    formatted = []
    used_urls = set()
    used_items = set()
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 20:
            continue
        
        if is_fluff(line):
            continue
        
        # Try strategies in order of preference
        result = None
        
        # Strategy 1: Standard extraction with separator
        result = try_standard_extraction(line, original_items, used_urls, used_items)
        
        # Strategy 2: Fuzzy match by content similarity
        if not result:
            result = try_fuzzy_match(line, original_items, used_urls, used_items)
        
        # Strategy 3: Just find any unused item with URL
        if not result:
            result = try_fallback_assignment(line, original_items, used_urls, used_items)
        
        if result:
            formatted.append(result)
            
        if len(formatted) >= 5:
            break
    
    # Pad with raw items if we have fewer than 5
    while len(formatted) < 5 and len(used_items) < len(original_items):
        for item in original_items:
            if item['url'] not in used_items:
                formatted.append(format_raw_item(item))
                used_items.add(item['url'])
                break
        if len(formatted) >= 5:
            break
    
    if not formatted:
        return None
    
    return '\n'.join(f"{i + 1}. {line}" for i, line in enumerate(formatted[:5]))

def try_standard_extraction(line: str, items: List[Dict], used_urls: set, used_items: set) -> Optional[str]:
    """Standard extraction expecting — separator and URL."""
    if '—' not in line and ' - ' not in line:
        return None
    
    separator = '—' if '—' in line else ' - '
    parts = line.split(separator, 1)
    if len(parts) < 2:
        return None
    
    url = extract_url(parts[1])
    if not url:
        url = extract_url(line)
    
    if not url or url in used_urls:
        return None
    
    # Find matching item
    matching_item = find_item_by_url(url, items, used_items)
    if not matching_item:
        matching_item = find_item_by_text(parts[0], items, used_items)
    
    if not matching_item:
        return None
    
    used_urls.add(url)
    used_items.add(matching_item['url'])
    
    insight = clean_insight(parts[0])
    return f"{insight} — {matching_item['source_label']} {matching_item['url']}"

def try_fuzzy_match(line: str, items: List[Dict], used_urls: set, used_items: set) -> Optional[str]:
    """Match line to item by text similarity."""
    # Extract any insight text (remove numbers, prefixes)
    clean_line = re.sub(r'^\d+[\.\):\]\s]*', '', line)
    clean_line = re.sub(r'^item\s*\d+[:\.\s]*', '', clean_line, flags=re.I)
    
    best_match = None
    best_score = 0.0
    
    for item in items:
        if item['url'] in used_items:
            continue
        
        # Compare with title
        title_score = similarity(clean_line, item['title'])
        # Compare with summary
        summary_score = similarity(clean_line, item.get('summary', ''))
        
        score = max(title_score, summary_score * 0.5)
        
        if score > best_score and score > 0.3:  # 30% similarity threshold
            best_score = score
            best_match = item
    
    if best_match:
        used_items.add(best_match['url'])
        insight = clean_insight(clean_line)
        return f"{insight} — {best_match['source_label']} {best_match['url']}"
    
    return None

def try_fallback_assignment(line: str, items: List[Dict], used_urls: set, used_items: set) -> Optional[str]:
    """Assign line to first unused item if it looks like content."""
    # Check if line has substantial content (not just metadata)
    if len(line) < 30:
        return None
    
    # Check for action verbs indicating insight
    action_words = ['built', 'created', 'developed', 'launched', 'achieved', 
                   'automated', 'scaled', 'grew', 'reduced', 'increased']
    has_action = any(word in line.lower() for word in action_words)
    
    if not has_action:
        return None
    
    # Assign to first unused item
    for item in items:
        if item['url'] not in used_items:
            used_items.add(item['url'])
            insight = clean_insight(line)
            return f"{insight} — {item['source_label']} {item['url']}"
    
    return None

def format_raw_item(item: Dict) -> str:
    """Format item directly from original data."""
    title = item['title']
    # Convert title to insight format if needed
    insight = clean_insight(title)
    return f"{insight} — {item['source_label']} {item['url']}"

def find_item_by_url(url: str, items: List[Dict], used_items: set) -> Optional[Dict]:
    """Find item by URL match."""
    for item in items:
        if item['url'] in url or url in item['url']:
            if item['url'] not in used_items:
                return item
    return None

def find_item_by_text(text: str, items: List[Dict], used_items: set) -> Optional[Dict]:
    """Find item by source label in text."""
    for item in items:
        if item['source_label'] in text and item['url'] not in used_items:
            return item
    return None

def clean_insight(text: str) -> str:
    """Clean insight text."""
    # Remove numbering
    text = re.sub(r'^\d+[\.\):\]\s]*', '', text)
    text = re.sub(r'^item\s*\d+[:\.\s]*', '', text, flags=re.I)
    # Remove markdown
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    # Normalize whitespace
    text = ' '.join(text.split())
    return text.strip()

def extract_url(text: str) -> str:
    """Extract URL from text."""
    # More permissive URL matching
    match = re.search(r'https?://[^\s\]\>\)\"\']+', text)
    if match:
        url = match.group(0)
        # Clean trailing punctuation
        url = url.rstrip('.,;:!?)\'\"')
        return url
    return ""

def similarity(a: str, b: str) -> float:
    """Calculate text similarity."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def is_fluff(line: str) -> bool:
    """Check if line is fluff."""
    fluff_patterns = [
        r'^here\s+(are|is)',
        r'^(summary|digest|output):',
        r'^top\s+\d+',
        r'^item\s+\d+[:\.\s]*$',
        r'^(below|following|above)',
        r'^note:',
        r'^\d+\.$',  # Just a number
    ]
    
    lower = line.lower()
    for pattern in fluff_patterns:
        if re.match(pattern, lower):
            return True
    
    return len(line) < 15  # Too short
