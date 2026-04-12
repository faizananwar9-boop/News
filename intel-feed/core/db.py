"""Supabase database layer for intel-feed with fallback to local JSON."""
import os
import json
from typing import List, Dict, Set, Optional

SEEN_FILE = "seen_ids.json"
_use_local = os.environ.get("LOCAL_MODE", "").lower() in ("true", "1", "yes")

_supabase = None

def _init_supabase():
    """Try to initialize Supabase, fall back to None if not configured."""
    global _supabase
    if _supabase is None and not _use_local:
        try:
            from supabase import create_client
            url = os.environ.get("SUPABASE_URL")
            key = os.environ.get("SUPABASE_KEY")
            if url and key:
                _supabase = create_client(url, key)
                print("[db] Connected to Supabase")
            else:
                print("[db] SUPABASE_URL/KEY not set, using local JSON fallback")
        except Exception as e:
            print(f"[db] Failed to connect to Supabase: {e}")
    return _supabase


def get_seen_ids(topic_slug: str) -> Set[str]:
    """Get set of seen item IDs for a topic."""
    supabase = _init_supabase()
    
    if supabase:
        try:
            response = supabase.table("seen_items").select("item_id").eq("topic_slug", topic_slug).execute()
            if getattr(response, "error", None):
                raise Exception(response.error)
            return set(row["item_id"] for row in (response.data or []))
        except Exception as e:
            print(f"[db] Error loading from Supabase: {e}, falling back to local")
    
    # Fallback to local JSON
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE) as f:
                return set(json.load(f))
        except Exception as e:
            print(f"[db] Error loading local file: {e}")
    return set()


def mark_seen(topic_slug: str, items: List[Dict]) -> bool:
    """Mark items as seen for a topic."""
    supabase = _init_supabase()
    
    item_ids = [item["id"] for item in items if item.get("id")]
    if not item_ids:
        print("[db] No item IDs to mark as seen")
        return True
    
    records = [
        {
            "topic_slug": topic_slug,
            "item_id": item["id"],
            "item_url": item.get("url", ""),
            "item_title": item.get("title", ""),
            "source_connector": item.get("connector", ""),
            "source_label": item.get("source_label", "")
        }
        for item in items if item.get("id")
    ]
    
    if supabase:
        try:
            batch_size = 100
            for i in range(0, len(records), batch_size):
                chunk = records[i:i + batch_size]
                response = supabase.table("seen_items").upsert(chunk).execute()
                if getattr(response, "error", None):
                    raise Exception(response.error)
            print(f"[db] Marked {len(records)} items as seen in Supabase")
            return True
        except Exception as e:
            print(f"[db] Error saving to Supabase: {e}, falling back to local")
    
    # Fallback to local JSON
    seen = get_seen_ids(topic_slug)
    seen.update(item_ids)
    try:
        with open(SEEN_FILE, "w") as f:
            json.dump(list(seen), f)
        if supabase:
            print(f"[db] Marked {len(item_ids)} items as seen locally after Supabase failure")
        else:
            print(f"[db] Marked {len(item_ids)} items as seen locally")
        return True
    except Exception as e:
        print(f"[db] Error saving local file: {e}")
        return False


def cleanup_old(topic_slug: str, days: int = 30):
    """Remove seen items older than N days for a topic."""
    # Only works in Supabase mode
    supabase = _init_supabase()
    if supabase:
        try:
            from datetime import datetime, timedelta
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            
            supabase.table("seen_items")\
                .delete()\
                .eq("topic_slug", topic_slug)\
                .lt("seen_at", cutoff)\
                .execute()
            
            print(f"[db] Cleaned up items older than {days} days")
        except Exception as e:
            print(f"[db] Error cleaning up: {e}")


def get_topic_config(topic_slug: str) -> Dict:
    """Get all config for a topic from database."""
    supabase = _init_supabase()
    
    if supabase:
        try:
            response = supabase.table("topic_config")\
                .select("config_key, config_value")\
                .eq("topic_slug", topic_slug)\
                .execute()
            
            config = {}
            for row in response.data:
                config[row["config_key"]] = row["config_value"]
            return config
        except Exception as e:
            print(f"[db] Error loading config: {e}")
    
    return {}
