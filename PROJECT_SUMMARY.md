# Intel-Feed Project Summary

## Overview
Production-ready intelligence feed aggregator with keyword-based ranking and multi-channel delivery.

**Status**: ✅ Production Ready  
**Last Updated**: April 2026  
**Version**: 2.0

---

## Architecture

### Core Components

| Module | Purpose | Key Files |
|--------|---------|-----------|
| **Connectors** | Content fetching | `connectors/rss.py`, `nitter.py`, `youtube.py` |
| **Scorer** | Ranking algorithm | `core/content_scorer.py` |
| **Extractor** | LLM output parsing | `core/extractor.py` |
| **LLM Router** | Multi-provider support | `core/llm.py` |
| **Database** | Supabase + fallback | `core/db.py` |
| **Notifier** | Telegram sender | `core/notifier.py` |
| **Logger** | File + console logging | `core/logger.py` |

### Data Flow

```
1. Fetch (RSS/Nitter/YouTube) → items with title, summary, url, published
2. Filter seen → new items only
3. Score → keyword (70%) + recency (30%)
4. Rank → sort by total score
5. Select → top 5 items
6. Summarize → LLM generates digest
7. Extract → robust parsing with 3 fallbacks
8. Send → Telegram notification
9. Store → mark as seen in Supabase
```

---

## Key Features Implemented

### 1. Hybrid Ranking System
- **Keyword scoring**: Configurable weights (high: 2.0, medium: 0.5)
- **Recency scoring**: 5.0 (today) → 0.5 (9+ days)
- **Weight ratio**: 70% keywords / 30% recency (configurable via YAML)

### 2. Robust LLM Extraction
Three fallback strategies:
1. Standard extraction (separator + URL)
2. Fuzzy match by text similarity
3. Fallback assignment by action verbs
Plus: Padding with raw items if < 5 extracted

### 3. Multi-Provider LLM
Supported providers:
- Anthropic (`claude-sonnet-4-6`)
- LiteLLM proxy
- OpenAI

Switch via `LLM_PROVIDER` env var.

### 4. Resilient Design
- Supabase primary, JSON file fallback
- Multiple Nitter instances (auto-failover)
- Try/catch around all external calls
- Comprehensive logging to file (`intel_feed.log`)

### 5. GitHub Actions Integration
- Scheduled: 7am & 5pm IST
- Matrix builds per topic
- Artifact upload for logs
- Conditional seen-marking (prod only)

---

## Configuration Reference

### Environment Variables

```bash
# Required
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-api03-...
TELEGRAM_BOT_TOKEN=123456:ABC-...
TELEGRAM_CHAT_PM_AI=-100...

# Optional (Supabase)
SUPABASE_URL=https://...
SUPABASE_KEY=eyJ...

# Optional (override)
ANTHROPIC_MODEL=claude-sonnet-4-6
```

### YAML Structure (`topics/pm_ai.yaml`)

```yaml
name: string                 # Display name
description: string          # Brief desc

ranking:
  recency_weight: float      # 0.0-1.0 (default: 0.3)
  high_value_keywords:       # List of {keyword, weight}
  medium_value_keywords:     # List of {keyword, weight}
  bonus_patterns:           # List of {pattern, weight}

config:
  telegram_channels:        # List of env var names
  digest_max_items: int     # Max items per source
  cleanup_after_days: int   # DB retention

sources:
  rss:                      # List of {url, label}
  nitter:                   # List of {handle, label}
  youtube:                  # List of {channel_id, label, max_items}

digest_prompt: string       # LLM prompt template
```

---

## File Structure

```
intel-feed/
├── connectors/          # Source adapters
│   ├── rss.py          # RSS feed parser
│   ├── nitter.py       # Twitter/X via Nitter
│   └── youtube.py      # YouTube RSS
├── core/               # Business logic
│   ├── config.py       # YAML loading
│   ├── content_scorer.py  # Keyword + recency scoring
│   ├── db.py           # Supabase/JSON storage
│   ├── digest.py       # Main build flow
│   ├── extractor.py    # Robust LLM output parsing
│   ├── llm.py          # Multi-provider LLM router
│   ├── logger.py       # File + console logging
│   ├── notifier.py     # Telegram sender
│   └── priority_sorter.py  # Sorting utilities
├── topics/             # Topic configurations
│   └── pm_ai.yaml      # PM x AI topic
├── scripts/            # Utilities
│   ├── init_supabase.sql
│   └── refine_loop.py
├── .github/workflows/
│   └── digest.yml      # GitHub Actions
├── main.py             # Entry point
├── test_*.py           # Test scripts
└── requirements.txt
```

---

## Deployment Checklist

- [ ] Create GitHub repo
- [ ] Add all secrets to GitHub
- [ ] Set up Supabase (optional)
- [ ] Configure topics in YAML
- [ ] Test locally: `python main.py topics/pm_ai.yaml`
- [ ] Enable GitHub Actions
- [ ] Verify first scheduled run
- [ ] Check logs in artifacts

---

## Recent Changes

### v2.0 (April 2026)
- ✅ Added recency-based ranking (70/30 split)
- ✅ Implemented 3-strategy LLM extraction with fallbacks
- ✅ Added file logging (`intel_feed.log`) for debugging
- ✅ Removed dead code from digest.py
- ✅ Fixed Nitter handle formatting (removed @ symbols)
- ✅ Added error handling throughout
- ✅ Created comprehensive test suite
- ✅ Multi-provider LLM support (Anthropic, LiteLLM, OpenAI)
- ✅ GitHub Actions artifact upload for logs

### v1.0 (Initial)
- Basic RSS/Nitter/YouTube fetching
- Anthropic-only LLM
- Single Telegram channel
- File-based deduplication

---

## Known Limitations

1. **Nitter reliability**: Often fails, auto-skips (expected)
2. **Rate limits**: Anthropic has token limits
3. **Date parsing**: Some feeds lack publish dates (falls back to neutral score)
4. **Extraction**: LLM can still produce invalid formats (mitigated by 3 fallbacks)

---

## Debugging

### Local Logs
```bash
tail -f intel_feed.log
```

### GitHub Actions Logs
1. Go to Actions tab → Failed run
2. Download `logs-topics/pm_ai.yaml` artifact
3. View `intel_feed.log`

---

## Maintainer

@faizananwar9-boop
