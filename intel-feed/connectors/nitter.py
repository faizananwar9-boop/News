import feedparser
from typing import List, Dict

NITTER_INSTANCES = [
    "nitter.privacydev.net",
    "nitter.poast.org",
    "nitter.net",
]

def fetch(sources: List[Dict], max_per_feed: int = 8) -> List[Dict]:
    items = []
    for source in sources:
        fetched = False
        for instance in NITTER_INSTANCES:
            try:
                url = f"https://{instance}/{source['handle']}/rss"
                feed = feedparser.parse(url)
                if not feed.entries:
                    continue
                for entry in feed.entries[:max_per_feed]:
                    items.append({
                        "id": entry.get("id") or entry.get("link", ""),
                        "title": entry.get("title", "").strip(),
                        "url": entry.get("link", ""),
                        "summary": entry.get("summary", "")[:500].strip(),
                        "source_label": source["label"],
                        "connector": "nitter",
                    })
                fetched = True
                break
            except Exception as e:
                print(f"[nitter] {instance} failed for @{source['handle']}: {e}")
        if not fetched:
            print(f"[nitter] All instances failed for @{source['handle']}")
    return items
