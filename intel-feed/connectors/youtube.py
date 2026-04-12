import feedparser
from typing import List, Dict

def fetch(sources: List[Dict], max_per_feed: int = 3) -> List[Dict]:
    items = []
    for source in sources:
        try:
            url = f"https://www.youtube.com/feeds/videos.xml?channel_id={source['channel_id']}"
            feed = feedparser.parse(url)
            limit = source.get("max_items", max_per_feed)
            for entry in feed.entries[:limit]:
                items.append({
                    "id": entry.get("id") or entry.get("link", ""),
                    "title": entry.get("title", "").strip(),
                    "url": entry.get("link", ""),
                    "summary": entry.get("summary", "")[:500].strip(),
                    "source_label": source["label"],
                    "connector": "youtube",
                })
        except Exception as e:
            print(f"[youtube] Failed {source.get('label')}: {e}")
    return items
