"""Send a custom test message to Telegram to verify integration."""
import os
import sys
import requests
from datetime import datetime

def send_custom_test_message():
    # Get credentials
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_PM_AI")
    
    if not token:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN not set")
        print("Run: export TELEGRAM_BOT_TOKEN='123456:ABC-DEF...'")
        sys.exit(1)
    
    if not chat_id:
        print("❌ ERROR: TELEGRAM_CHAT_PM_AI not set")
        print("Run: export TELEGRAM_CHAT_PM_AI='-1001234567890'")
        sys.exit(1)
    
    # Build custom test message
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    message = f"""🧪 *Intel-Feed Bot Test*

⏰ Timestamp: `{timestamp}`

This is a test message to verify your Telegram integration is working correctly.

✅ *Configuration Verified:*
• Bot Token: Working
• Chat ID: `{chat_id}`
• Parse Mode: Markdown

📝 *Next Steps:*
1. If you see this message, Telegram is configured correctly
2. Run the full test: `python test_digest.py`
3. Deploy to GitHub Actions

_Bot is ready for production digests!_ 🚀"""
    
    # Send message
    try:
        print(f"Sending test message to chat ID: {chat_id}...")
        
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_notification": False
            },
            timeout=10
        )
        
        resp.raise_for_status()
        result = resp.json()
        
        if result.get("ok"):
            print("✅ Message sent successfully!")
            print(f"   Message ID: {result['result']['message_id']}")
            print(f"   Chat: {result['result']['chat']['title']}")
            print("\n📱 Check your Telegram channel for the test message.")
            return True
        else:
            print(f"❌ Telegram API error: {result}")
            return False
            
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        if e.response.status_code == 401:
            print("   → Bot token is invalid or revoked")
        elif e.response.status_code == 400:
            print("   → Chat ID is invalid or bot is not a member")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = send_custom_test_message()
    sys.exit(0 if success else 1)
