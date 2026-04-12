import importlib
from typing import List, Dict

def fetch_all(topic_config: Dict) -> List[Dict]:
    all_items = []
    sources = topic_config.get("sources", {})
    for connector_name, source_list in sources.items():
        try:
            module = importlib.import_module(f"connectors.{connector_name}")
            items = module.fetch(source_list)
            all_items.extend(items)
            print(f"[fetcher] {connector_name}: {len(items)} items")
        except ModuleNotFoundError:
            print(f"[fetcher] No connector for '{connector_name}' — skipping")
        except Exception as e:
            print(f"[fetcher] {connector_name} error: {e}")
    return all_items
