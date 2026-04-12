from core.config import load_topic_config
from core.fetcher import fetch_all
from core.digest import filter_new
from core.db import get_seen_ids

config = load_topic_config("topics/pm_ai.yaml")
topic_slug = config["slug"]

seen = get_seen_ids(topic_slug)
items = fetch_all(config)
new_items = filter_new(items, seen)

print(f"\nTopic: {config['name']} ({topic_slug})")
print(f"Fetched {len(items)} total items")
print(f"New (unseen) items: {len(new_items)}")
print(f"Seen in database: {len(seen)}")

for i in new_items[:10]:
    print(f"  [{i['connector']}] {i['source_label']}: {i['title'][:70]}")
