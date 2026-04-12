#!/usr/bin/env python3
"""Iterative refinement loop for perfecting digest output."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.config import load_topic_config
from core.fetcher import fetch_all
from core.digest import filter_new
from core.digest_v2 import build_v2
from core.db import get_seen_ids
from core.validator import validate_output, diagnose_issues
from core.llm import get_llm_config

def run_refinement_loop(topic_file: str = "topics/pm_ai.yaml", max_iterations: int = 5):
    """Run iterative refinement until output meets criteria or max iterations reached."""
    
    print("="*70)
    print("DIGEST REFINEMENT LOOP")
    print("="*70)
    
    # Load config and fetch items
    config = load_topic_config(topic_file)
    topic_slug = config["slug"]
    
    print(f"\nTopic: {config['name']}")
    print(f"Model: {get_llm_config()['model']}\n")
    
    # Fetch and filter
    all_items = fetch_all(config)
    seen = get_seen_ids(topic_slug)
    new_items = filter_new(all_items, seen)
    
    print(f"Total items: {len(all_items)}")
    print(f"New items: {len(new_items)}\n")
    
    if not new_items:
        print("❌ No new items to summarize")
        return
    
    # Iteration loop
    for iteration in range(1, max_iterations + 1):
        print(f"\n{'─'*70}")
        print(f"ITERATION {iteration}/{max_iterations}")
        print(f"{'─'*70}\n")
        
        # Generate digest
        try:
            output = build_v2(
                new_items, 
                config["digest_prompt"],
                config.get("sources", {}),
                max_retries=1
            )
        except Exception as e:
            print(f"❌ Generation error: {e}")
            continue
        
        if not output:
            print("❌ No output generated")
            continue
        
        # Validate
        is_valid, issues = validate_output(output)
        
        print("OUTPUT:")
        print("="*70)
        print(output)
        print("="*70)
        
        if is_valid:
            print(f"\n✅ SUCCESS! Output validated in {iteration} iteration(s)")
            print(f"\nCriteria met:")
            print("  ✓ Exactly 5 items")
            print("  ✓ Correct format (Number. Insight — Author Source URL)")
            print("  ✓ No extra text")
            return output
        else:
            print(f"\n⚠️  VALIDATION ISSUES:")
            for issue in issues:
                print(f"  - {issue}")
            
            diagnosis = diagnose_issues(output, issues)
            print(f"\n🔍 DIAGNOSIS:")
            for cause, detected in diagnosis.items():
                if detected:
                    print(f"  - {cause}")
            
            if iteration < max_iterations:
                print(f"\n🔄 Retrying with adjustments...")
    
    print(f"\n{'='*70}")
    print(f"❌ Max iterations ({max_iterations}) reached without valid output")
    print(f"{'='*70}")
    return None

if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("LITELLM_API_KEY"):
        print("❌ Set ANTHROPIC_API_KEY or LITELLM_API_KEY")
        sys.exit(1)
    
    topic_file = sys.argv[1] if len(sys.argv) > 1 else "topics/pm_ai.yaml"
    run_refinement_loop(topic_file)
