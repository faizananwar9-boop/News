import os
from core.config import load_topic_config
from core.fetcher import fetch_all
from core.digest import filter_new, build
from core.db import get_seen_ids

def test_digest_dry_run(topic_file="topics/pm_ai.yaml"):
    if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("LITELLM_API_KEY"):
        print("ERROR: Set ANTHROPIC_API_KEY or LITELLM_API_KEY")
        return
    
    config = load_topic_config(topic_file)
    topic_slug = config["slug"]
    
    print(f"\nDRY RUN: {config['name']} ({topic_slug})\n")
    
    all_items = fetch_all(config)
    seen = get_seen_ids(topic_slug)
    new_items = filter_new(all_items, seen)
    
    print(f"Fetched: {len(all_items)} | New: {len(new_items)}")
    
    if not new_items:
        print("No new content")
        return
    
    # Show sample of what we're sending
    print(f"\nSample items being sent to LLM:")
    for i, item in enumerate(new_items[:3], 1):
        print(f"  {i}. {item['source_label']}: {item['title'][:50]}...")
    
    print("\nGenerating digest...")
    digest = build(new_items, config["digest_prompt"], config)
    
    if digest:
        print("\n" + "="*60)
        print(digest)
        print("="*60)
        print("\nDRY RUN COMPLETE")
    else:
        print("No digest generated - check filter_items() logic")
        print(f"Items after filter_new: {len(new_items)}")
        # Try to understand why
        from core.digest import filter_items
        filtered = filter_items(new_items)
        print(f"Items after filter_items: {len(filtered) if filtered else 0}")

if __name__ == "__main__":
    test_digest_dry_run()
