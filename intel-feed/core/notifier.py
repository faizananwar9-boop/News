import os
import requests
from typing import List
from datetime import datetime, timezone

def send_telegram(text: str, chat_ids: List[str]):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
    
    hour = datetime.now(timezone.utc).hour
    label = "Morning" if hour < 12 else "Evening"
    full_text = f"*{label} briefing*\n\n{text}"
    
    results = []
    for chat_id in chat_ids:
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": full_text,
                    "parse_mode": "Markdown"
                },
                timeout=10
            )
            resp.raise_for_status()
            print(f"[notifier] Sent to {chat_id}")
            results.append({"chat_id": chat_id, "success": True})
        except Exception as e:
            print(f"[notifier] Failed to send to {chat_id}: {e}")
            results.append({"chat_id": chat_id, "success": False, "error": str(e)})
    
    return results
