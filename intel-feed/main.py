import os
import sys
from core.config import load_topic_config, get_telegram_channels
from core.fetcher import fetch_all
from core.digest import filter_new, build
from core.db import get_seen_ids, mark_seen
from core.notifier import send_telegram
from core.logger import logger

def run(topic_file: str):
    try:
        config = load_topic_config(topic_file)
        topic_slug = config["slug"]
        logger.info(f"Running topic: {config['name']}")
        
        seen = get_seen_ids(topic_slug)
        all_items = fetch_all(config)
        new_items = filter_new(all_items, seen)
        logger.info(f"New items after dedup: {len(new_items)}")
        
        if not new_items:
            logger.info("No new content — skipping send.")
            return
        
        digest = build(new_items, config["digest_prompt"], config)
        if digest:
            channels = get_telegram_channels(config)
            
            if channels:
                send_telegram(digest, channels)
                logger.info(f"Sent digest to {len(channels)} channel(s)")
                
                if os.environ.get("GITHUB_ACTIONS") == "true":
                    mark_seen(topic_slug, new_items)
                    logger.info("Marked items as seen in database")
                else:
                    logger.info("Local run - NOT marking items as seen")
            else:
                logger.warning("No Telegram channels configured")
        else:
            logger.warning("No digest generated — skipping send.")
            
    except Exception as e:
        logger.error(f"Fatal error in run(): {e}", exc_info=True)
        raise

if __name__ == "__main__":
    topic_file = sys.argv[1] if len(sys.argv) > 1 else "topics/pm_ai.yaml"
    run(topic_file)
