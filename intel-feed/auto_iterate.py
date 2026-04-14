#!/usr/bin/env python3
"""
Fully automated test-fix loop.
Runs test, logs to file, reads file, validates, fixes, repeats.
"""
import os
import sys
import re
import subprocess
import time
sys.path.insert(0, '/Users/faizan.anwar/Documents/Code/News/intel-feed')

# Configuration
LOG_FILE = "/tmp/digest_test_output.log"
MAX_ITERATIONS = 5
VALID_SOURCES = {
    "Lenny's Newsletter", "Lenny Rachitsky", "Shreyas Doshi",
    "SVPG", "Benedict Evans", "Ethan Mollick",
    "Exponential View", "Import AI", "TLDR AI"
}

def validate_digest(output_file: str) -> dict:
    """Read output file and validate format."""
    result = {
        'valid': False,
        'lines': [],
        'issues': [],
        'line_count': 0
    }

    if not os.path.exists(output_file):
        result['issues'].append("Output file not found")
        return result

    with open(output_file, 'r') as f:
        content = f.read()

    lines = [l.strip() for l in content.split('\n') if l.strip()]
    result['lines'] = lines
    result['line_count'] = len(lines)

    # Must have exactly 5 lines
    if len(lines) != 5:
        result['issues'].append(f"Expected 5 lines, got {len(lines)}")

    for i, line in enumerate(lines, 1):
        # Check 1: Starts with valid source
        has_source = any(line.startswith(src) for src in VALID_SOURCES)
        if not has_source:
            result['issues'].append(f"Line {i}: Invalid start - '{line[:40]}...'")

        # Check 2: Has em-dash
        if '—' not in line:
            result['issues'].append(f"Line {i}: Missing em-dash")

        # Check 3: Has URL
        if not re.search(r'https?://', line):
            result['issues'].append(f"Line {i}: Missing URL")

        # Check 4: No weak "about" phrasing
        parts = line.split('—')
        if len(parts) >= 1:
            insight = parts[0]
            for src in VALID_SOURCES:
                if insight.startswith(src):
                    insight = insight[len(src):].strip()
                    break
            if ' about ' in insight.lower():
                result['issues'].append(f"Line {i}: Weak 'about' phrasing")

    if not result['issues'] and len(lines) == 5:
        result['valid'] = True

    return result

def run_single_test() -> bool:
    """Run one test iteration, log to file, return True if successful."""
    print(f"\n{'='*70}")
    print(f"RUNNING TEST ITERATION")
    print(f"{'='*70}")

    # Run the test and capture output
    env = os.environ.copy()
    cmd = [sys.executable, "-c", """
import sys
sys.path.insert(0, '/Users/faizan.anwar/Documents/Code/News/intel-feed')

from core.config import load_topic_config
from core.fetcher import fetch_all
from core.digest import filter_new, filter_items, _sort_items, _extract_formatted_lines
from core.llm import get_llm_config, generate_summary
from core.db import get_seen_ids

config = load_topic_config("topics/pm_ai.yaml")
all_items = fetch_all(config)
seen = get_seen_ids(config["slug"])
new_items = filter_new(all_items, seen)
filtered = filter_items(new_items, config.get('ranking', {}))
sorted_items = _sort_items(filtered)

from core.digest import _format_item_for_prompt
content = "\\n\\n".join(_format_item_for_prompt(i, idx) for idx, i in enumerate(sorted_items[:10]))
full_prompt = f"{config['digest_prompt']}\\n\\nItems:\\n{content}"

llm_config = get_llm_config()
raw_output = generate_summary(full_prompt, llm_config)
extracted = _extract_formatted_lines(raw_output, max_items=5)

if extracted:
    print(extracted)
else:
    print("EXTRACTION_FAILED")
    print(raw_output[:2000])
"""]

    try:
        with open(LOG_FILE, 'w') as f:
            subprocess.run(cmd, env=env, stdout=f, stderr=subprocess.STDOUT, timeout=120)
    except subprocess.TimeoutExpired:
        print("TIMEOUT: Test took too long")
        return False
    except Exception as e:
        print(f"ERROR running test: {e}")
        return False

    # Validate output
    result = validate_digest(LOG_FILE)

    # Show results
    with open(LOG_FILE, 'r') as f:
        output = f.read()

    print(f"\nOUTPUT ({result['line_count']} lines):")
    print("-" * 70)
    print(output[:1500])
    print("-" * 70)

    if result['issues']:
        print("\nISSUES FOUND:")
        for issue in result['issues']:
            print(f"  - {issue}")

    return result['valid']

def apply_fix(iteration: int, issues: list) -> bool:
    """Apply fixes based on detected issues. Returns True if fixes applied."""
    print(f"\nAPPLYING FIXES (Iteration {iteration})...")

    # Read current prompt
    import yaml
    with open("topics/pm_ai.yaml", 'r') as f:
        config = yaml.safe_load(f)

    prompt = config.get('digest_prompt', '')
    original_prompt = prompt

    # Fix 1: If lines don't start with valid source
    if any("Invalid start" in i for i in issues):
        print("  → Strengthening source label requirement")
        if "Source label must be EXACTLY" not in prompt:
            prompt += """

MUST START WITH ONE OF THESE EXACT STRINGS:
Lenny's Newsletter
Lenny Rachitsky
SVPG
Shreyas Doshi
Exponential View
Import AI"""

    # Fix 2: If missing em-dash or using " - "
    if any("em-dash" in i for i in issues):
        print("  → Enforcing em-dash separator")
        if "Use em-dash" not in prompt:
            prompt += """

SEPARATOR: Use em-dash (—) not hyphen (-)
BAD: Lenny's Newsletter - Anthropic growth
GOOD: Lenny's Newsletter Anthropic growth — https://..."""

    # Fix 3: If weak "about" phrasing
    if any("about" in i.lower() for i in issues):
        print("  → Banning weak 'about' phrasing")
        if "FORBIDDEN PHRASES" not in prompt:
            prompt += """

FORBIDDEN PHRASES (WILL BE FILTERED):
- "about Anthropic"
- "about Yash"
- "about product"
- Any line with " about "

REQUIRED: Action verb + outcome
GOOD: "Anthropic scaled $1B to $19B using AI agents"
BAD: "Lenny's Newsletter about Anthropic growth"""

    # Fix 4: If missing URLs
    if any("Missing URL" in i for i in issues):
        print("  → Enforcing URL requirement")
        if "END WITH URL" not in prompt:
            prompt += """

END WITH URL: Every line must end with — https://..."""

    # Save if changed
    if prompt != original_prompt:
        config['digest_prompt'] = prompt
        with open("topics/pm_ai.yaml", 'w') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        print("  ✓ Prompt updated")
        return True

    print("  (No automatic fixes available)")
    return False

def main():
    """Main iteration loop."""
    print("="*70)
    print("AUTOMATED TEST-FIX LOOP")
    print("="*70)

    for iteration in range(1, MAX_ITERATIONS + 1):
        print(f"\n{'='*70}")
        print(f"ITERATION {iteration}/{MAX_ITERATIONS}")
        print(f"{'='*70}")

        # Run test
        success = run_single_test()

        if success:
            print(f"\n{'='*70}")
            print("✅ SUCCESS! Output is in correct format.")
            print(f"{'='*70}")
            with open(LOG_FILE, 'r') as f:
                print(f.read())
            return 0

        # Get issues and apply fixes
        result = validate_digest(LOG_FILE)
        if not apply_fix(iteration, result['issues']):
            print("\n⚠️ Cannot auto-fix. Manual intervention needed.")
            print(f"Check {LOG_FILE} for output")
            return 1

        time.sleep(1)

    print(f"\n{'='*70}")
    print("❌ MAX ITERATIONS REACHED")
    print("Manual fix required. Check log file:")
    with open(LOG_FILE, 'r') as f:
        print(f.read())
    return 1

if __name__ == "__main__":
    sys.exit(main())
