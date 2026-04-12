import os
from typing import List, Dict, Optional
from core.db import get_seen_ids, mark_seen
from core.llm import get_llm_config, generate_summary
from core.priority_sorter import get_top_n, enrich_with_source_metadata
from core.deterministic_cleaner import clean_deterministic, validate_clean_output

def filter_new(items: List[Dict], seen: set) -> List[Dict]:
    return [i for i in items if i["id"] and i["id"] not in seen]

def build_v2(new_items: List[Dict], prompt_template: str, sources_config: Dict, max_retries: int = 3) -> Optional[str]:
    if not new_items:
        return None
    
    enriched = enrich_with_source_metadata(new_items, sources_config)
    top_items = get_top_n(enriched, n=5)
    
    content = "\n\n".join(
        f"ITEM {idx + 1}:"
        f"\nSOURCE: {i['source_label']}"
        f"\nTITLE: {i['title']}"
        f"\nURL: {i['url']}"
        f"\nSNIPPET: {i['summary'][:200]}"
        for idx, i in enumerate(top_items)
    )
    
    full_prompt = f"{prompt_template}\n\n{content}"
    config = get_llm_config()
    
    for attempt in range(max_retries):
        try:
            raw_output = generate_summary(full_prompt, config)
            
            final_output = clean_deterministic(raw_output, top_items)
            
            is_valid, issues = validate_clean_output(final_output)
            
            if is_valid:
                return final_output
            
            print(f"[digest_v2] Attempt {attempt + 1} failed validation:")
            for issue in issues:
                print(f"  - {issue}")
            
            if attempt == max_retries - 1:
                print("[digest_v2] Max retries reached, returning best effort")
                return final_output
                
        except Exception as e:
            print(f"[digest_v2] Attempt {attempt + 1} error: {e}")
            if attempt == max_retries - 1:
                raise
    
    return None
