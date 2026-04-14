#!/usr/bin/env python3
"""
Test-Debug-Iterate script for digest generation.
Run this to see the actual output and diagnose issues.
"""
import os
import sys
sys.path.insert(0, '/Users/faizan.anwar/Documents/Code/News/intel-feed')

from core.config import load_topic_config
from core.fetcher import fetch_all
from core.digest import filter_new, filter_items, _sort_items, _extract_formatted_lines
from core.llm import get_llm_config, generate_summary
from core.db import get_seen_ids

def test_and_show_output(topic_file="topics/pm_ai.yaml"):
    if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("LITELLM_API_KEY"):
        print("ERROR: Set ANTHROPIC_API_KEY or LITELLM_API_KEY")
        return

    config = load_topic_config(topic_file)
    topic_slug = config["slug"]

    print(f"\n{'='*70}")
    print(f"TEST RUN: {config['name']} ({topic_slug})")
    print(f"{'='*70}\n")

    # Step 1: Fetch
    all_items = fetch_all(config)
    seen = get_seen_ids(topic_slug)
    new_items = filter_new(all_items, seen)

    print(f"[FETCH] Total: {len(all_items)} | New: {len(new_items)}")

    if not new_items:
        print("No new content to process")
        return

    # Step 2: Filter
    filtered_items = filter_items(new_items, config.get('ranking', {}))
    print(f"[FILTER] After removing spam/dev/duplicates: {len(filtered_items)}")

    if not filtered_items:
        print("All items filtered out!")
        return

    # Step 3: Sort
    sorted_items = _sort_items(filtered_items)
    print(f"[SORT] Top 5 by priority:")
    for i, item in enumerate(sorted_items[:5]):
        print(f"  {i+1}. [{item.get('_dynamic_priority', '?')}] {item['source_label']}: {item['title'][:50]}...")

    # Step 4: Build prompt and call LLM
    from core.digest import _format_item_for_prompt
    content = "\n\n".join(
        _format_item_for_prompt(i, idx)
        for idx, i in enumerate(sorted_items[:10])  # Send top 10 for variety
    )
    full_prompt = f"{config['digest_prompt']}\n\nItems:\n{content}"

    print(f"\n[PROMPT] Length: {len(full_prompt)} chars")
    print(f"[PROMPT] Last 500 chars:\n...{full_prompt[-500:]}")

    # Step 5: Call LLM
    print(f"\n[LLM] Calling {get_llm_config()['provider']}...")
    llm_config = get_llm_config()
    raw_output = generate_summary(full_prompt, llm_config)

    print(f"\n{'='*70}")
    print("RAW LLM OUTPUT:")
    print(f"{'='*70}")
    print(raw_output)
    print(f"{'='*70}")

    # Step 6: Extract
    print("\n[EXTRACT] Applying extraction rules...")
    digest = _extract_formatted_lines(raw_output, max_items=5)

    print(f"\n{'='*70}")
    print("FINAL EXTRACTED DIGEST:")
    print(f"{'='*70}")
    if digest:
        print(digest)
    else:
        print("NO DIGEST EXTRACTED!")
    print(f"{'='*70}")

    # Validation
    print("\n[VALIDATION] Checking output format...")
    if digest:
        lines = [l for l in digest.split('\n') if l.strip()]
        print(f"  - Line count: {len(lines)} (expected: 5)")

        for i, line in enumerate(lines):
            has_url = 'http' in line
            has_dash = '—' in line
            starts_with_source = any(line.startswith(s) for s in [
                "Lenny's Newsletter", "Lenny Rachitsky", "Shreyas Doshi",
                "SVPG", "Benedict Evans", "Ethan Mollick",
                "Exponential View", "Import AI"
            ])

            issues = []
            if not has_url:
                issues.append("no URL")
            if not has_dash:
                issues.append("no em-dash")
            if not starts_with_source:
                issues.append("bad start")

            if issues:
                print(f"  - Line {i+1}: {' '.join(issues)} | {line[:60]}...")
            else:
                print(f"  - Line {i+1}: ✓")

if __name__ == "__main__":
    test_and_show_output()
