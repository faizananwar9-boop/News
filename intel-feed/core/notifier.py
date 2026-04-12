import os
import requests
from typing import List
from datetime import datetime, timezone

def _escape_markdown(text: str) -> str:
    """Escape special Markdown characters for Telegram."""
    # Escape Markdown special characters: * _ ` [ ]
    escapable = ['*', '_', '[', ']', '`']
    for char in escapable:
        text = text.replace(char, f'\\{char}')
    return text

def send_telegram(text: str, chat_ids: List[str]):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
    
    hour = datetime.now(timezone.utc).hour
    label = "Morning" if hour < 12 else "Evening"
    escaped_text = _escape_markdown(text)
    full_text = f"*{label} briefing*\n\n{escaped_text}"
    
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
            payload = resp.json()

            if not payload.get("ok", False):
                error_msg = payload.get("description", "Telegram API returned ok=false")
                print(f"[notifier] Telegram API failed for {chat_id}: {error_msg} | payload: {payload}")
                results.append({"chat_id": chat_id, "success": False, "error": error_msg, "payload": payload})
                continue

            message_id = None
            if isinstance(payload.get("result"), dict):
                message_id = payload["result"].get("message_id")

            print(f"[notifier] Sent to {chat_id}")
            results.append({"chat_id": chat_id, "success": True, "message_id": message_id, "payload": payload})
        except requests.exceptions.HTTPError as e:
            error_msg = str(e)
            try:
                payload = resp.json()
                error_msg = payload.get("description", error_msg)
            except Exception:
                pass
            print(f"[notifier] Failed to send to {chat_id}: {error_msg}")
            results.append({"chat_id": chat_id, "success": False, "error": error_msg})
        except Exception as e:
            print(f"[notifier] Failed to send to {chat_id}: {e}")
            results.append({"chat_id": chat_id, "success": False, "error": str(e)})
    
    return results
