-- Supabase Schema for intel-feed
-- Run this in Supabase SQL Editor

-- Table: topics (metadata for each topic)
CREATE TABLE IF NOT EXISTS topics (
    slug TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: seen_items (deduplication tracking)
CREATE TABLE IF NOT EXISTS seen_items (
    id BIGSERIAL PRIMARY KEY,
    topic_slug TEXT NOT NULL REFERENCES topics(slug) ON DELETE CASCADE,
    item_id TEXT NOT NULL,
    item_url TEXT,
    item_title TEXT,
    source_connector TEXT,
    source_label TEXT,
    seen_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(topic_slug, item_id)
);

-- Table: topic_config (per-topic configuration)
CREATE TABLE IF NOT EXISTS topic_config (
    id BIGSERIAL PRIMARY KEY,
    topic_slug TEXT NOT NULL REFERENCES topics(slug) ON DELETE CASCADE,
    config_key TEXT NOT NULL,
    config_value JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(topic_slug, config_key)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_seen_items_topic ON seen_items(topic_slug);
CREATE INDEX IF NOT EXISTS idx_seen_items_seen_at ON seen_items(seen_at);
CREATE INDEX IF NOT EXISTS idx_topic_config_slug ON topic_config(topic_slug);

-- Sample data for pm_ai topic
INSERT INTO topics (slug, name, description) VALUES
('pm_ai', 'PM x AI', 'Product management and AI intersection')
ON CONFLICT (slug) DO NOTHING;

INSERT INTO topic_config (topic_slug, config_key, config_value) VALUES
('pm_ai', 'telegram_channels', '["TELEGRAM_CHAT_PM_AI"]'),
('pm_ai', 'digest_max_items', '25'),
('pm_ai', 'cleanup_after_days', '30')
ON CONFLICT (topic_slug, config_key) DO NOTHING;
