# Supabase Setup Guide

## 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Note your project URL and anon/public key
3. Open the SQL Editor in your Supabase dashboard

## 2. Run Schema Migration

Copy the contents of `scripts/init_supabase.sql` and run it in the SQL Editor.

This creates:
- `topics` table - stores topic metadata
- `seen_items` table - tracks seen items for deduplication
- `topic_config` table - stores per-topic configuration

## 3. Configure GitHub Secrets

Add these secrets to your GitHub repository:

```
ANTHROPIC_API_KEY=sk-ant-...
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_PM_AI=-1001234567890

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIs...
```

## 4. Adding New Topics

1. Create a new YAML file in `topics/` (e.g., `fintech.yaml`):

```yaml
name: "Fintech"
description: "Fintech news and updates"

config:
  telegram_channels:
    - TELEGRAM_CHAT_FINTECH
  digest_max_items: 25
  cleanup_after_days: 30

schedule:
  morning_utc: "30 1 * * *"
  evening_utc: "30 11 * * *"

sources:
  rss:
    - url: "https://example.com/feed"
      label: "Example Source"

digest_prompt: |
  Summarize these fintech articles...
```

2. Add the topic to Supabase:

```sql
INSERT INTO topics (slug, name, description) VALUES
('fintech', 'Fintech', 'Fintech news and updates');

INSERT INTO topic_config (topic_slug, config_key, config_value) VALUES
('fintech', 'telegram_channels', '["TELEGRAM_CHAT_FINTECH"]'),
('fintech', 'digest_max_items', '25'),
('fintech', 'cleanup_after_days', '30');
```

3. Add the Telegram channel secret to GitHub:

```
TELEGRAM_CHAT_FINTECH=-1009876543210
```

## 5. Multiple Channels per Topic

You can send to multiple Telegram channels:

```yaml
config:
  telegram_channels:
    - TELEGRAM_CHAT_PM_AI
    - TELEGRAM_CHAT_AI_TEAM
    - TELEGRAM_CHAT_EXECUTIVE
```

Add all corresponding secrets to GitHub.

## Migration from File-Based Storage

If you have an existing `seen_ids.json`:

1. The new system will start fresh (all items will be "new" once)
2. Run `test_local.py` to verify DB connection
3. Check Supabase dashboard to see items being tracked
