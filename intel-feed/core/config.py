"""Configuration resolver for topics."""
import os
import yaml
from typing import Dict, List, Any
from pathlib import Path


def resolve_secrets(config: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve environment variable names in config to actual values.
    
    For telegram_channels, resolves env var names to actual channel IDs.
    """
    resolved = config.copy()
    
    # Resolve telegram_channels from env var names to actual values
    if "telegram_channels" in resolved:
        channel_env_vars = resolved["telegram_channels"]
        if isinstance(channel_env_vars, list):
            resolved["telegram_channels"] = [
                os.environ.get(var_name, var_name)  # Fallback to var name if not set
                for var_name in channel_env_vars
                if os.environ.get(var_name) or not var_name.startswith("TELEGRAM_")
            ]
    
    return resolved


def load_topic_config(topic_file: str) -> Dict[str, Any]:
    """Load topic configuration from YAML file.
    
    Loads YAML and resolves environment variables for secrets.
    """
    topic_path = Path(topic_file)
    if not topic_path.exists():
        raise FileNotFoundError(f"Topic file not found: {topic_file}")
    
    with open(topic_path) as f:
        config = yaml.safe_load(f)
    
    # Extract topic slug from filename (e.g., topics/pm_ai.yaml -> pm_ai)
    topic_slug = topic_path.stem
    config["slug"] = topic_slug
    
    # Resolve secrets in config
    if "config" in config:
        config["config"] = resolve_secrets(config["config"])
    
    # Handle legacy format: migrate telegram_chat_id_secret to config.telegram_channels
    if "telegram_chat_id_secret" in config and "config" not in config:
        secret_name = config.pop("telegram_chat_id_secret", None)
        if secret_name:
            config["config"] = {
                "telegram_channels": [os.environ.get(secret_name, secret_name)]
            }
    
    return config


def get_telegram_channels(config: Dict[str, Any]) -> List[str]:
    """Get list of Telegram channel IDs from config."""
    topic_config = config.get("config", {})
    channels = topic_config.get("telegram_channels", [])
    
    # Legacy fallback
    if not channels and "telegram_chat_id_secret" in config:
        secret_name = config["telegram_chat_id_secret"]
        channel = os.environ.get(secret_name)
        if channel:
            channels = [channel]
    
    return channels


def get_digest_max_items(config: Dict[str, Any]) -> int:
    """Get maximum number of items to include in digest."""
    topic_config = config.get("config", {})
    return topic_config.get("digest_max_items", 25)


def get_cleanup_days(config: Dict[str, Any]) -> int:
    """Get number of days to keep seen items before cleanup."""
    topic_config = config.get("config", {})
    return topic_config.get("cleanup_after_days", 30)
