import re
from typing import List

def clean_llm_output(raw_output: str) -> str:
    """Clean and extract valid lines from LLM output."""
    lines = raw_output.strip().split('\n')
    valid_lines = []
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Skip lines that look like intro/outro
        if is_fluff_line(line):
            continue
        
        # Extract numbered items
        if re.match(r'^\d+[\.\)]\s', line):
            # Clean up the line
            cleaned = clean_line(line)
            if cleaned:
                valid_lines.append(cleaned)
    
    # Renumber to ensure sequential 1-5
    renumbered = []
    for i, line in enumerate(valid_lines[:5], 1):
        # Replace existing number with correct one
        cleaned = re.sub(r'^\d+[\.\)]\s*', f'{i}. ', line)
        renumbered.append(cleaned)
    
    return '\n'.join(renumbered)

def is_fluff_line(line: str) -> bool:
    """Detect intro/outro fluff text."""
    fluff_patterns = [
        r'^here\s+are',
        r'^top\s+stories',
        r'^ai\s+x\s+product',
        r'^skill\s+angle',
        r'^content\s+to',
        r'^summary',
        r'^digest',
        r'^these\s+are',
        r'^below\s+are',
        r'^following\s+are',
        r'^\*\*',  # Markdown bold
        r'^#{1,6}\s',  # Markdown headers
        r'^here\s+is',
        r'^this\s+week',
        r'^today',
        r'^\[',  # Tags like [High Priority]
    ]
    
    lower_line = line.lower()
    for pattern in fluff_patterns:
        if re.search(pattern, lower_line):
            return True
    
    return False

def clean_line(line: str) -> str:
    """Clean individual line - remove metadata tags, fix format."""
    # Remove metadata tags like [High Priority], [Important], etc.
    line = re.sub(r'\[[^\]]+\]\s*', '', line)
    
    # Remove markdown formatting
    line = re.sub(r'\*\*([^*]+)\*\*', r'\1', line)  # Bold
    line = re.sub(r'\*([^*]+)\*', r'\1', line)      # Italic
    line = re.sub(r'`([^`]+)`', r'\1', line)        # Code
    
    # Ensure separator is em-dash (—) not hyphen or en-dash
    line = re.sub(r'\s*[-–—]\s+', ' — ', line)
    
    # Remove extra whitespace
    line = ' '.join(line.split())
    
    return line.strip()

def enforce_exactly_five(cleaned_output: str) -> str:
    """Ensure exactly 5 items, padding or truncating if needed."""
    lines = cleaned_output.strip().split('\n')
    
    if len(lines) >= 5:
        return '\n'.join(lines[:5])
    
    # If less than 5, that's an error - return as-is for diagnosis
    return cleaned_output
