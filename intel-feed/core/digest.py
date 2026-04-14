import re
from typing import List, Dict, Optional
from core.llm import get_llm_config, generate_summary
from core.content_scorer import rank_by_content
from core.extractor import extract_and_format_robust
from core.logger import logger

DEFAULT_NEGATIVE_KEYWORDS = [
    "birthday wishes",
    "happy birthday",
    "b'day",
    "bday",
    "best wishes",
    "wish you",
    "congratulations",
]

DEFAULT_NEGATIVE_PATTERNS = [
    r"\bbirthday\b",
    r"\bbday\b",
    r"\bbest wishes\b",
    r"\bwish(es)? you\b",
    r"\bcongratulations\b",
]


def filter_new(items: List[Dict], seen: set) -> List[Dict]:
    return [i for i in items if i["id"] and i["id"] not in seen]


def _normalize_text(value: str) -> str:
    return (value or "").strip().lower()


def _build_negative_filters(ranking_config: Optional[Dict]) -> Dict[str, List[str]]:
    ranking_config = ranking_config or {}
    negative_keywords = [
        str(kw).lower().strip()
        for kw in ranking_config.get("negative_keywords", [])
        if isinstance(kw, str) and kw.strip()
    ]
    negative_patterns = [
        str(pattern).strip()
        for pattern in ranking_config.get("negative_patterns", [])
        if isinstance(pattern, str) and pattern.strip()
    ]

    if not negative_keywords:
        negative_keywords = DEFAULT_NEGATIVE_KEYWORDS.copy()

    if not negative_patterns:
        negative_patterns = DEFAULT_NEGATIVE_PATTERNS.copy()

    return {
        "keywords": negative_keywords,
        "patterns": negative_patterns,
    }


def _is_negative_item(item: Dict, ranking_config: Optional[Dict] = None) -> bool:
    text = _normalize_text(item.get("title", "")) + " " + _normalize_text(item.get("summary", ""))
    filters = _build_negative_filters(ranking_config)

    for keyword in filters["keywords"]:
        if keyword and keyword in text:
            return True

    for pattern in filters["patterns"]:
        if pattern and re.search(pattern, text):
            return True

    return False


def filter_items(items: List[Dict], ranking_config: Optional[Dict] = None) -> List[Dict]:
    ranking_config = ranking_config or {}
    seen_signatures = set()
    cleaned = []

    for item in items:
        title = _normalize_text(item.get("title", ""))
        summary = _normalize_text(item.get("summary", ""))
        url = _normalize_text(item.get("url", ""))

        if not title or not url:
            continue

        if _is_negative_item(item, ranking_config):
            continue

        signature = (title, url)
        if signature in seen_signatures:
            continue

        seen_signatures.add(signature)
        cleaned.append(item)

    return cleaned


def _format_item_for_prompt(item: Dict, idx: int) -> str:
    return (
        f"{idx + 1}. SOURCE: {item.get('source_label', 'Unknown')}\n"
        f"TITLE: {item.get('title', '')}\n"
        f"URL: {item.get('url', '')}"
    )


def _sort_items(items: List[Dict]) -> List[Dict]:
    def _sort_key(item: Dict):
        published = item.get("published_parsed")
        if isinstance(published, tuple):
            return published
        if published is None:
            return ()
        return published

    return sorted(items, key=_sort_key, reverse=True)


def _extract_url(text: str) -> Optional[str]:
    match = re.search(r"https?://[^\s]+", text)
    return match.group(0).rstrip(".,") if match else None


def _extract_formatted_lines(raw_output: str, max_items: int = 5) -> str:
    lines = []
    for raw_line in raw_output.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        line = re.sub(r"^\d+\.\s*", "", line)
        if 'http' not in line:
            continue

        lines.append(line)
        if len(lines) >= max_items:
            break

    return "\n".join(lines)


def build(new_items: List[Dict], prompt_template: str, config: Dict = None) -> tuple:
    if not new_items:
        logger.info("[build] No new_items provided")
        return None, []
    
    ranking_config = config.get('ranking', {}) if config else {}
    
    ranked_items = rank_by_content(new_items, ranking_config)
    top_items = ranked_items[:5]
    
    logger.info(f"[build] Selected top {len(top_items)} items by content relevance")
    for i, item in enumerate(top_items, 1):
        logger.info(f"  {i}. {item['source_label']}: {item['title'][:50]}...")
    
    content = "\n\n".join(
        f"{idx + 1}. SOURCE: {item['source_label']}\nTITLE: {item['title']}\nURL: {item['url']}"
        for idx, item in enumerate(top_items)
    )
    
    full_prompt = f"{prompt_template}\n\n{content}"
    config_llm = get_llm_config()
    
    logger.info("[build] Calling LLM...")
    try:
        raw_output = generate_summary(full_prompt, config_llm)
        logger.info(f"[build] LLM returned {len(raw_output)} characters")
    except Exception as e:
        logger.error(f"[build] LLM call failed: {e}")
        return None, []
    
    result = extract_and_format_robust(raw_output, top_items)
    line_count = result.count('\n') + 1 if result else 0
    logger.info(f"[build] Extracted {line_count} lines")
    return result, top_items
