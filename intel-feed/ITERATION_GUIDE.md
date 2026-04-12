# Test-Fix Iteration Guide

## Automated Loop Script

Run the automated test-fix loop:

```bash
source venv/bin/activate
export LITELLM_API_KEY=your_key
python auto_test_fix.py
```

This script will:
1. Fetch content
2. Call LLM
3. Extract formatted lines
4. Validate each line against criteria
5. Report specific issues found
6. Give recommendations for fixes

## Manual Fix Cycle

If automated validation fails, manually iterate:

```bash
# Step 1: Run test and capture output
python auto_test_fix.py 2>&1 | tee last_run.txt

# Step 2: Identify issues from report
# Look for: "Issues found:" and "Recommendations:" sections

# Step 3: Fix based on issue type
```

## Common Issues & Fixes

### Issue: "Invalid start" (line doesn't start with valid source)
**Fix:** Strengthen prompt to list exact source labels required

### Issue: "Contains 'about'" or "Insight starts weakly"
**Fix:** Add examples showing BAD ("about X") vs GOOD (action verb + outcome)

### Issue: "Missing em-dash" or "Contains ' - '"
**Fix:** Emphasize em-dash (—) requirement, show exact format

### Issue: "Analysis line" detected
**Fix:** Add stronger constraints banning "Item 1:", "keep", "skip" language

### Issue: Less than 5 lines extracted
**Fix:** Ensure LLM knows to output EXACTLY 5, not fewer

## Validation Criteria

Each line MUST:
1. Start with valid source: "Lenny's Newsletter", "Lenny Rachitsky", "SVPG", "Shreyas Doshi", "Exponential View", "Import AI"
2. Contain em-dash (—) separator
3. Contain URL (https://)
4. NOT contain " about " (weak phrasing)
5. NOT contain " - " (analysis style)
6. Insight must start with action verb (not "about", "on", "discussing")

## Desired Output Format

```
Lenny's Newsletter Anthropic scaled $1B to $19B using AI agents for autonomous growth — https://www.lennysnewsletter.com/p/anthropic-growth
SVPG Prototypes validate ideas but products require different success criteria — https://www.svpg.com/prototypes-vs-products/
Shreyas Doshi Product sense becomes decisive advantage as AI commoditizes execution — https://shreyasdoshi.substack.com/p/product-sense
```

Key characteristics:
- Source label at start
- Action verb + outcome + mechanism
- Em-dash (—) before URL
- Full URL at end
- No "about" or weak framing
