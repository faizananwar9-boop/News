import re
from typing import List, Tuple, Dict

def validate_output(output: str) -> Tuple[bool, List[str]]:
    """Validate digest output against constraints."""
    issues = []
    
    # Check 1: Must have exactly 5 numbered items
    lines = extract_numbered_lines(output)
    if len(lines) != 5:
        issues.append(f"Expected exactly 5 items, got {len(lines)}")
    
    # Check 2: Each line must match format
    for i, line in enumerate(lines, 1):
        line_issues = validate_line_format(line, i)
        issues.extend(line_issues)
    
    # Check 3: No extra text (intro/outro)
    if has_extra_text(output, lines):
        issues.append("Output contains extra text beyond the 5 items")
    
    return len(issues) == 0, issues

def extract_numbered_lines(output: str) -> List[str]:
    """Extract lines that start with number."""
    lines = []
    for line in output.strip().split('\n'):
        line = line.strip()
        if re.match(r'^\d+\.', line):
            lines.append(line)
    return lines

def validate_line_format(line: str, index: int) -> List[str]:
    """Validate a single line format."""
    issues = []
    
    # Must contain: Number. Text — Author Source URL
    pattern = r'^\d+\.\s+(.+)\s+—\s+(.+)\s+(https?://\S+)$'
    if not re.match(pattern, line):
        issues.append(f"Line {index}: Incorrect format. Expected 'Number. Insight — Author Source URL'")
        return issues
    
    # Extract parts for validation
    match = re.match(pattern, line)
    if match:
        insight = match.group(1)
        
        # Word count check (15-30 words for insight part only)
        word_count = len(insight.split())
        if word_count < 10:
            issues.append(f"Line {index}: Too short ({word_count} words), minimum 10")
        elif word_count > 35:
            issues.append(f"Line {index}: Too long ({word_count} words), maximum 35")
    
    return issues

def has_extra_text(output: str, numbered_lines: List[str]) -> bool:
    """Check if there's text before first or after last numbered line."""
    lines = output.strip().split('\n')
    
    # Find first and last numbered line indices
    first_idx = None
    last_idx = None
    
    for i, line in enumerate(lines):
        if re.match(r'^\d+\.', line.strip()):
            if first_idx is None:
                first_idx = i
            last_idx = i
    
    if first_idx is None:
        return True
    
    # Check for non-empty lines before first numbered line
    for i in range(first_idx):
        if lines[i].strip() and not lines[i].strip().startswith('CONTENT TO'):
            return True
    
    # Check for non-empty lines after last numbered line
    for i in range(last_idx + 1, len(lines)):
        if lines[i].strip():
            return True
    
    return False

def diagnose_issues(output: str, issues: List[str]) -> Dict[str, str]:
    """Diagnose root cause of validation failures."""
    diagnosis = {
        'prompt_needs_stricter_format': False,
        'prompt_needs_examples': False,
        'needs_item_limit': False,
        'needs_post_processing': False,
        'temperature_too_high': False
    }
    
    for issue in issues:
        if 'Expected exactly 5 items' in issue:
            diagnosis['needs_item_limit'] = True
        if 'Incorrect format' in issue:
            diagnosis['prompt_needs_stricter_format'] = True
        if 'extra text' in issue:
            diagnosis['needs_post_processing'] = True
    
    return diagnosis
