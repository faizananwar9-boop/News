#!/usr/bin/env python3
"""
Automated test-fix loop for digest generation.
Runs test, validates output, reports issues, suggests fixes.
"""
import os
import sys
import re
sys.path.insert(0, '/Users/faizan.anwar/Documents/Code/News/intel-feed')

from core.config import load_topic_config
from core.fetcher import fetch_all
from core.digest import filter_new, filter_items, _sort_items, _extract_url
from core.llm import get_llm_config, generate_summary
from core.db import get_seen_ids

# Desired output criteria
VALID_SOURCES = {
    "Lenny's Newsletter", "Lenny Rachitsky", "Shreyas Doshi",
    "SVPG", "Benedict Evans", "Ethan Mollick",
    "Exponential View", "Import AI", "TLDR AI"
}

def validate_line(line: str, line_num: int) -> list:
    """Validate a single line and return list of issues."""
    issues = []
    line_stripped = line.strip()

    if not line_stripped:
        return ["Empty line"]

    # Check 1: Must start with valid source
    has_valid_source = any(line_stripped.startswith(src) for src in VALID_SOURCES)
    if not has_valid_source:
        # Find what it starts with
        first_word = line_stripped.split()[0] if line_stripped.split() else "EMPTY"
        issues.append(f"Invalid start '{first_word}...' (must start with valid SourceLabel)")

    # Check 2: Must have em-dash
    if '—' not in line_stripped:
        issues.append("Missing em-dash (—)")

    # Check 3: Must have URL
    url = _extract_url(line_stripped)
    if not url:
        issues.append("Missing URL")

    # Check 4: Must NOT have " about " pattern
    if ' about ' in line_stripped.lower():
        issues.append("Contains 'about' (weak phrasing)")

    # Check 5: Must NOT have " - " pattern (indicates analysis format)
    if re.search(r'\s+-\s+', line_stripped):
        issues.append("Contains ' - ' (analysis style)")

    # Check 6: Insight part should not start with weak words
    if '—' in line_stripped:
        parts = line_stripped.split('—')
        insight = parts[0].strip()
        # Remove source label to get just insight
        for src in VALID_SOURCES:
            if insight.startswith(src):
                insight = insight[len(src):].strip()
                break

        weak_starts = ['about ', 'on ', 'discussing ', 'covering ', 'explaining ']
        if any(insight.lower().startswith(w) for w in weak_starts):
            issues.append(f"Insight starts weakly: '{insight[:30]}...'")

    return issues

def analyze_output(raw_output: str, extracted_digest: str) -> dict:
    """Analyze the output and return detailed report."""
    report = {
        'raw_length': len(raw_output),
        'extracted_length': len(extracted_digest) if extracted_digest else 0,
        'raw_lines': [],
        'extracted_lines': [],
        'issues_found': [],
        'recommendations': []
    }

    # Analyze raw output
    raw_lines = [l.strip() for l in raw_output.split('\n') if l.strip()]
    report['raw_lines'] = raw_lines

    # Count potential formatted lines in raw output
    formatted_count = 0
    for line in raw_lines:
        if any(line.startswith(src) for src in VALID_SOURCES):
            formatted_count += 1
        elif line.lower().startswith(('item ', 'lenny ', 'svpg ', 'shreyas ', 'exponential ', 'import ')):
            report['issues_found'].append(f"Analysis line: {line[:50]}...")

    report['formatted_lines_in_raw'] = formatted_count

    # Analyze extracted output
    if extracted_digest:
        extracted_lines = [l.strip() for l in extracted_digest.split('\n') if l.strip()]
        report['extracted_lines'] = extracted_lines

        for i, line in enumerate(extracted_lines, 1):
            issues = validate_line(line, i)
            if issues:
                report['issues_found'].append(f"Line {i}: {', '.join(issues)}")

    # Generate recommendations
    if formatted_count == 0:
        report['recommendations'].append("LLM not outputting any formatted lines - strengthen prompt")
    elif formatted_count < 5:
        report['recommendations'].append(f"Only {formatted_count} formatted lines found - need 5")

    if any('about' in i.lower() for i in report['issues_found']):
        report['recommendations'].append("Ban 'about' in insights - require action verbs")

    if any(' - ' in i for i in report['issues_found']):
        report['recommendations'].append("LLM using ' - ' instead of em-dash - enforce em-dash in prompt")

    return report

def run_test_fix_loop(topic_file="topics/pm_ai.yaml"):
    """Main test-fix loop."""
    if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("LITELLM_API_KEY"):
        print("ERROR: Set ANTHROPIC_API_KEY or LITELLM_API_KEY")
        return

    config = load_topic_config(topic_file)

    print(f"\n{'='*70}")
    print(f"AUTO TEST-FIX LOOP: {config['name']}")
    print(f"{'='*70}\n")

    # Fetch and prepare data
    all_items = fetch_all(config)
    seen = get_seen_ids(config["slug"])
    new_items = filter_new(all_items, seen)
    filtered = filter_items(new_items, config.get('ranking', {}))
    sorted_items = _sort_items(filtered)

    print(f"[DATA] Fetched: {len(all_items)} | New: {len(new_items)} | Filtered: {len(filtered)}")

    if len(sorted_items) < 5:
        print(f"[ERROR] Not enough items ({len(sorted_items)}) to generate digest")
        return

    # Build prompt
    from core.digest import _format_item_for_prompt
    content = "\n\n".join(_format_item_for_prompt(i, idx) for idx, i in enumerate(sorted_items[:10]))
    full_prompt = f"{config['digest_prompt']}\n\nItems:\n{content}"

    # Call LLM
    print(f"[LLM] Calling {get_llm_config()['provider']}...")
    llm_config = get_llm_config()
    raw_output = generate_summary(full_prompt, llm_config)

    # Extract
    from core.digest import _extract_formatted_lines
    extracted = _extract_formatted_lines(raw_output, max_items=5)

    # Analyze
    report = analyze_output(raw_output, extracted)

    # Print results
    print(f"\n{'='*70}")
    print("RAW LLM OUTPUT:")
    print(f"{'='*70}")
    print(raw_output[:2000])
    if len(raw_output) > 2000:
        print(f"... ({len(raw_output) - 2000} more chars)")
    print(f"{'='*70}")

    print(f"\n{'='*70}")
    print("EXTRACTED DIGEST:")
    print(f"{'='*70}")
    if extracted:
        print(extracted)
    else:
        print("NO DIGEST EXTRACTED")
    print(f"{'='*70}")

    print(f"\n{'='*70}")
    print("ANALYSIS REPORT:")
    print(f"{'='*70}")
    print(f"Raw output: {report['raw_length']} chars")
    print(f"Formatted lines in raw: {report['formatted_lines_in_raw']}")
    print(f"Extracted lines: {len(report['extracted_lines'])}")

    if report['issues_found']:
        print(f"\nIssues found:")
        for issue in report['issues_found']:
            print(f"  - {issue}")

    if report['recommendations']:
        print(f"\nRecommendations:")
        for rec in report['recommendations']:
            print(f"  → {rec}")

    # Validation summary
    print(f"\n{'='*70}")
    print("VALIDATION SUMMARY:")
    print(f"{'='*70}")

    if not extracted:
        print("❌ FAIL: No digest extracted")
        return False

    lines = [l for l in extracted.split('\n') if l.strip()]
    if len(lines) != 5:
        print(f"❌ FAIL: Expected 5 lines, got {len(lines)}")
        return False

    all_valid = True
    for i, line in enumerate(lines, 1):
        issues = validate_line(line, i)
        if issues:
            print(f"❌ Line {i}: {', '.join(issues)}")
            all_valid = False
        else:
            print(f"✓ Line {i}: Valid")

    if all_valid:
        print("\n✅ SUCCESS: All validation passed!")
        return True
    else:
        print("\n❌ FAIL: Issues found - need to fix")
        return False

if __name__ == "__main__":
    success = run_test_fix_loop()
    sys.exit(0 if success else 1)
