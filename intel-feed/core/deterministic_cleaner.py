import re
from typing import List, Dict, Tuple

def clean_deterministic(llm_output: str, original_items: List[Dict]) -> str:
    """Deterministically clean LLM output to exact format required."""
    lines = llm_output.strip().split('\n')
    cleaned_items = []
    item_index = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Extract content after item prefix (Item 1:, 1., etc.)
        content = extract_content_after_prefix(line)
        if not content:
            continue
        
        # Get corresponding original item for URL
        original_item = original_items[item_index] if item_index < len(original_items) else {}
        
        # Ensure format: Content — Source URL
        formatted = format_line(content, original_item)
        if formatted:
            cleaned_items.append(formatted)
            item_index += 1
        
        if len(cleaned_items) >= 5:
            break
    
    # Renumber 1-5
    result = []
    for i, item in enumerate(cleaned_items[:5], 1):
        # Replace any existing numbering with clean 1-5
        clean_item = re.sub(r'^(Item\s+)?\d+[\.\):\-\s]*', '', item).strip()
        result.append(f"{i}. {clean_item}")
    
    return '\n'.join(result)

def extract_content_after_prefix(line: str) -> str:
    """Remove Item 1:, 1., 1), etc. prefixes."""
    # Match patterns: "Item 1:", "1.", "1)", "1 -", "1:"
    patterns = [
        r'^Item\s*\d+[:\.\-\)]\s*',
        r'^\d+[:\.\-\)]\s*',
    ]
    
    content = line
    for pattern in patterns:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)
    
    return content.strip()

def format_line(content: str, original_item: Dict) -> str:
    """Format to: Insight — Source URL."""
    # Remove any existing source attribution patterns to rebuild
    content = re.sub(r'\s*[—–-]\s*\w+[^\n]*$', '', content)  # Remove trailing source
    content = content.strip()
    
    # Get source name
    source_label = original_item.get('source_label', 'Source')
    
    # Get URL - critical!
    url = original_item.get('url', '').strip()
    if not url:
        url = extract_url_from_content(content)
    
    # Build final format
    if url:
        return f"{content} — {source_label} {url}"
    else:
        return f"{content} — {source_label}"

def extract_url_from_content(content: str) -> str:
    """Extract URL if present in content."""
    url_pattern = r'(https?://[^\s]+)'
    match = re.search(url_pattern, content)
    return match.group(1) if match else ''

def validate_clean_output(output: str) -> Tuple[bool, List[str]]:
    """Quick validation of cleaned output."""
    issues = []
    lines = output.split('\n')
    
    if len(lines) != 5:
        issues.append(f"Expected 5 lines, got {len(lines)}")
    
    for i, line in enumerate(lines, 1):
        # Check format: Number. Content — Source URL
        if not re.match(r'^\d+\.\s+.+\s+[—–-]\s+.+\s+https?://', line):
            issues.append(f"Line {i} missing URL or wrong format")
    
    return len(issues) == 0, issues
