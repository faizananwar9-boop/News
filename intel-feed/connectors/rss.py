import feedparser
from typing import List, Dict

def fetch(sources: List[Dict], max_per_feed: int = 5) -> List[Dict]:
    items = []
    for source in sources:
        try:
            feed = feedparser.parse(source["url"])
            for entry in feed.entries[:max_per_feed]:
                items.append({
                    "id": entry.get("id") or entry.get("link", ""),
                    "title": entry.get("title", "").strip(),
                    "url": entry.get("link", ""),
                    "summary": entry.get("summary", "")[:500].strip(),
                    "source_label": source["label"],
                    "connector": "rss",
                    "published": entry.get("published", ""),
                    "published_parsed": entry.get("published_parsed"),
                })
        except Exception as e:
            print(f"[rss] Failed {source['url']}: {e}")
    return items
