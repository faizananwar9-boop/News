import os
import anthropic
from typing import List, Dict, Optional

def get_llm_config() -> Dict:
    """Get LLM configuration from environment."""
    provider = os.environ.get("LLM_PROVIDER", "anthropic").lower()

    if provider == "anthropic":
        return {
            "provider": "anthropic",
            "api_key": os.environ.get("ANTHROPIC_API_KEY"),
            "base_url": "https://api.anthropic.com",
            "model": os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
            "max_tokens": 2000
        }
    elif provider == "litellm":
        return {
            "provider": "litellm",
            "api_key": os.environ.get("LITELLM_API_KEY"),
            "base_url": os.environ.get("LITELLM_BASE_URL", "https://grid.ai.juspay.net"),
            "model": os.environ.get("LITELLM_MODEL", "claude-3-sonnet-20240229"),
            "max_tokens": 2000
        }
    elif provider == "openai":
        return {
            "provider": "openai",
            "api_key": os.environ.get("OPENAI_API_KEY"),
            "base_url": "https://api.openai.com/v1",
            "model": os.environ.get("OPENAI_MODEL", "gpt-4"),
            "max_tokens": 2000
        }
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}")

def generate_summary(prompt: str, config: Dict) -> str:
    """Generate summary using configured LLM provider."""
    provider = config["provider"]
    
    if provider == "anthropic":
        return _call_anthropic(prompt, config)
    elif provider == "litellm":
        return _call_litellm(prompt, config)
    elif provider == "openai":
        return _call_openai(prompt, config)
    else:
        raise ValueError(f"Unknown provider: {provider}")

def _call_anthropic(prompt: str, config: Dict) -> str:
    """Call Anthropic API."""
    if not config.get("api_key"):
        raise ValueError("ANTHROPIC_API_KEY not set")
    
    client = anthropic.Anthropic(
        api_key=config["api_key"],
        base_url=config["base_url"]
    )
    
    msg = client.messages.create(
        model=config["model"],
        max_tokens=config["max_tokens"],
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text

def _call_litellm(prompt: str, config: Dict) -> str:
    """Call LiteLLM proxy."""
    if not config.get("api_key"):
        raise ValueError("LITELLM_API_KEY not set")
    if not config.get("base_url"):
        raise ValueError("LITELLM_BASE_URL not set")
    
    import requests
    
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": config["model"],
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": config["max_tokens"]
    }
    
    response = requests.post(
        f"{config['base_url']}/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60
    )
    response.raise_for_status()
    
    data = response.json()
    return data["choices"][0]["message"]["content"]

def _call_openai(prompt: str, config: Dict) -> str:
    """Call OpenAI API."""
    if not config.get("api_key"):
        raise ValueError("OPENAI_API_KEY not set")
    
    import requests
    
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": config["model"],
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": config["max_tokens"]
    }
    
    response = requests.post(
        f"{config['base_url']}/chat/completions",
        headers=headers,
        json=payload,
        timeout=60
    )
    response.raise_for_status()
    
    data = response.json()
    return data["choices"][0]["message"]["content"]
