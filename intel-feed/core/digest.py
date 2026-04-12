from typing import List, Dict, Optional
from core.llm import get_llm_config, generate_summary
from core.content_scorer import rank_by_content
from core.extractor import extract_and_format_robust
from core.logger import logger

def filter_new(items: List[Dict], seen: set) -> List[Dict]:
    return [i for i in items if i["id"] and i["id"] not in seen]

def build(new_items: List[Dict], prompt_template: str, config: Dict = None) -> Optional[str]:
    if not new_items:
        logger.info("[build] No new_items provided")
        return None
    
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
        return None
    
    result = extract_and_format_robust(raw_output, top_items)
    line_count = result.count('\n') + 1 if result else 0
    logger.info(f"[build] Extracted {line_count} lines")
    return result
