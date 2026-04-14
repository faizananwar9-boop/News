import os
from core.config import load_topic_config
from core.fetcher import fetch_all
from core.digest import filter_new, filter_items, _sort_items, _extract_formatted_lines
from core.llm import get_llm_config, generate_summary
from core.db import get_seen_ids

def test_debug(topic_file="topics/pm_ai.yaml"):
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: Set ANTHROPIC_API_KEY")
        return

    config = load_topic_config(topic_file)
    topic_slug = config["slug"]

    print(f"\nDEBUG RUN: {config['name']} ({topic_slug})\n")

    all_items = fetch_all(config)
    seen = get_seen_ids(topic_slug)
    new_items = filter_new(all_items, seen)

    print(f"Fetched: {len(all_items)} | New: {len(new_items)}")

    if not new_items:
        print("No new content")
        return

    # Debug: Check filtering
    print("\n--- STEP 1: FILTER ---")
    filtered_items = filter_items(new_items, config.get('ranking', {}))
    print(f"After filtering: {len(filtered_items)} items")
    if not filtered_items:
        print("WARNING: All items were filtered out!")
        print("First new item sample:")
        if new_items:
            print(f"  Title: {new_items[0]['title'][:80]}")
            print(f"  Source: {new_items[0]['source_label']}")
        return

    # Debug: Check sorting
    print("\n--- STEP 2: SORT ---")
    sorted_items = _sort_items(filtered_items)
    print(f"Sorted: {len(sorted_items)} items")
    print("Top 3 items:")
    for i, item in enumerate(sorted_items[:3]):
        print(f"  {i+1}. [{item.get('_dynamic_priority', '?')}] {item['source_label']}: {item['title'][:60]}...")

    # Debug: Build prompt
    print("\n--- STEP 3: PROMPT ---")
    from core.digest import _format_item_for_prompt
    content = "\n\n".join(
        _format_item_for_prompt(i, idx)
        for idx, i in enumerate(sorted_items[:25])
    )
    full_prompt = f"{config['digest_prompt']}\n\nItems to digest (sorted by relevance):\n{content}"
    print(f"Prompt length: {len(full_prompt)} chars")
    print(f"Prompt preview:\n{full_prompt[:500]}...")

    # Debug: Call LLM
    print("\n--- STEP 4: LLM CALL ---")
    llm_config = get_llm_config()
    print(f"Provider: {llm_config['provider']}")
    raw_output = generate_summary(full_prompt, llm_config)
    print(f"Raw output length: {len(raw_output)} chars")
    print(f"\nRAW OUTPUT:\n{'='*60}")
    print(raw_output)
    print(f"{'='*60}")

    # Debug: Extract
    print("\n--- STEP 5: EXTRACT ---")
    digest = _extract_formatted_lines(raw_output)
    print(f"Extracted length: {len(digest)} chars")
    print(f"\nEXTRACTED:\n{'='*60}")
    print(digest)
    print(f"{'='*60}")

if __name__ == "__main__":
    test_debug()
