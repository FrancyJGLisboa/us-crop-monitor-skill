# Troubleshooting Guide

Common problems and solutions for US Crop Monitor skill.

## API Key Issues

### Problem: "API key is required"

**Symptoms**:
```
AuthenticationError: API key is required. Set NASS_API_KEY environment variable.
```

**Cause**: Environment variable not set or not loaded.

**Solutions**:

**1. Check if variable is set**:
```bash
echo $NASS_API_KEY
```

If empty, proceed to step 2.

**2. Add to shell configuration**:

For **zsh** (macOS default):
```bash
nano ~/.zshrc
# Add this line:
export NASS_API_KEY='your_key_here'
# Save (Ctrl+O, Enter, Ctrl+X)
source ~/.zshrc
```

For **bash**:
```bash
nano ~/.bashrc
export NASS_API_KEY='your_key_here'
source ~/.bashrc
```

**3. Verify**:
```bash
echo $NASS_API_KEY
# Should print your key
```

**4. Restart Claude Code**:
Environment variables loaded at startup. Restart Claude Code after setting.

### Problem: "Invalid API key"

**Symptoms**:
```
AuthenticationError: Invalid API key (401)
```

**Causes**:
1. Typo in API key
2. Extra spaces/quotes
3. Expired or revoked key (rare)

**Solutions**:

**1. Verify key format**:
API keys are typically 36 characters: `XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX`

**2. Check for extra characters**:
```bash
# Print key with quotes to see hidden chars
echo "'$NASS_API_KEY'"
```

Look for extra quotes, spaces, or newlines.

**3. Test key directly**:
```bash
curl "https://quickstats.nass.usda.gov/api/api_GET?key=$NASS_API_KEY&commodity_desc=CORN&year=2024&statisticcat_desc=CONDITION" | head -20
```

Should return JSON data, not error.

**4. Request new key**:
If all else fails, request a new API key from:
https://quickstats.nass.usda.gov/api/

## Data Availability Issues

### Problem: "No data found"

**Symptoms**:
```
DataNotFoundError: No data found for CORN 2024 week 50
```

**Causes**:
1. Week number doesn't exist yet (future)
2. Week number out of season range
3. Commodity/state combination invalid
4. Data not published yet

**Solutions**:

**1. Check current date and week**:
```python
from datetime import datetime
current_week = datetime.now().isocalendar()[1]
print(f"Current week: {current_week}")
```

Crop data published on Mondays. Data for week N available Monday of week N+1.

**2. Verify season range**:
- Corn/Soybeans: Weeks 18-44 (May-October)
- Winter Wheat: Weeks 14-26 (April-June)
- Spring Wheat: Weeks 20-36 (May-September)

**3. Check commodity name** (case-sensitive!):
- ✓ Correct: `CORN`, `SOYBEANS`, `WHEAT`
- ✗ Wrong: `corn`, `Corn`, `SOYBEAN` (singular)

**4. Verify state grows crop**:
Not all states grow all crops. Example:
- North Dakota: wheat, soybeans (not much corn)
- Iowa: corn, soybeans (not much wheat)

**5. Use get_latest_week()**:
```python
latest = client.get_latest_week('CORN', 2024)
print(f"Latest week available: {latest}")
```

### Problem: Partial state data

**Symptoms**:
Only 10 states returned when expecting 18+.

**Causes**:
1. Some states haven't reported yet
2. Small states excluded from survey
3. Crop not significant in some states

**Solutions**:

**1. Accept partial data**:
This is normal. Not all states report all crops every week.

**2. Focus on major producers**:
For national trends, top 10 states represent 80%+ of production.

**3. Check specific state**:
```python
# If specific state needed
data = client.get_crop_conditions(
    commodity='CORN',
    year=2024,
    week=32,
    state='IA'
)
```

If returns empty, that state truly has no data.

## Cache Issues

### Problem: Stale data returned

**Symptoms**:
Getting last week's data when new week published.

**Cause**: Cache hasn't expired yet (7-day TTL for recent data).

**Solutions**:

**1. Bypass cache**:
```python
data = client.get_crop_conditions(
    commodity='CORN',
    year=2024,
    use_cache=False
)
```

**2. Invalidate cache**:
```python
from utils.cache_manager import CacheManager
cache = CacheManager()
cache.invalidate('*CORN*2024*')  # Clear corn 2024 cache
```

**3. Manual cache clear**:
```bash
rm -rf data/cache/recent/*
```

**4. Adjust check time**:
Crop reports published Mondays 4pm ET. Check after 5pm ET to ensure data loaded.

### Problem: Cache grows too large

**Symptoms**:
`data/cache/` directory is several GB.

**Cause**: Years of accumulated historical data.

**Solutions**:

**1. Check cache size**:
```python
cache = CacheManager()
stats = cache.stats()
print(f"Total size: {stats['total_size_kb'] / 1024:.1f} MB")
```

**2. Clear old years**:
```bash
rm -rf data/cache/*2020*
rm -rf data/cache/*2021*
# Keep recent years only
```

**3. Full cache reset**:
```bash
rm -rf data/cache/*
```

Cache will rebuild on next use.

## Rate Limiting

### Problem: Slow responses or errors

**Symptoms**:
```
RateLimitError: Rate limit exceeded, waiting 60s...
```

Or just slow performance.

**Cause**: Too many requests in short time.

**Solutions**:

**1. Enable caching** (should be on by default):
```python
# Ensure cache is used
data = client.get_crop_conditions(..., use_cache=True)
```

**2. Batch requests**:
```python
# Bad: Multiple requests
for state in states:
    data = client.get_crop_conditions(..., state=state)

# Good: Single request
data = client.get_crop_conditions(..., agg_level='STATE')
# Returns all states at once
```

**3. Prefetch common queries**:
```bash
python scripts/fetch_nass.py --commodity CORN --year 2024 --prefetch
```

Loads cache for current week before interactive use.

**4. Increase wait time**:
Edit `scripts/fetch_nass.py`:
```python
self.rate_limiter = RateLimiter(max_requests=10, time_window=60)
# Reduce from 15 to 10 requests per minute
```

## Skill Activation Issues

### Problem: Skill doesn't activate automatically

**Symptoms**:
Claude doesn't use skill even when asking about crop conditions.

**Causes**:
1. Query missing keywords
2. Skill not installed
3. Description mismatch

**Solutions**:

**1. Include explicit keywords**:
```
# Vague (may not activate)
"How are crops doing?"

# Explicit (will activate)
"What are current corn conditions in the US?"
"NASS crop progress for soybeans"
"Crop condition report"
```

**2. Verify installation**:
```bash
ls ~/.claude/plugins/marketplaces/
# Should see "us-crop-monitor"
```

If not, reinstall:
```bash
/plugin marketplace add /path/to/us-crop-monitor
```

**3. Check description synchronization**:
SKILL.md description must match marketplace.json description exactly.

```bash
# Check SKILL.md
head -5 us-crop-monitor/SKILL.md

# Check marketplace.json
cat us-crop-monitor/.claude-plugin/marketplace.json | grep description
```

Must be identical. If different, edit marketplace.json to match SKILL.md.

## Data Quality Issues

### Problem: Percentages don't sum to 100

**Symptoms**:
```
Warning: Invalid percentages (sum != 100%)
```

**Cause**: Data rounding or missing categories.

**Solutions**:

**1. Check tolerance** (±2% is normal):
```python
total = sum([excellent, good, fair, poor, very_poor])
if 98 <= total <= 102:
    # Accept as valid
```

**2. Normalize if needed**:
```python
categories = ['EXCELLENT', 'GOOD', 'FAIR', 'POOR', 'VERY POOR']
total = sum(row[cat] for cat in categories)
if total > 0:
    for cat in categories:
        row[cat] = (row[cat] / total) * 100
```

**3. Flag and log**:
If sum is far off (< 95 or > 105), data may be corrupted. Log for investigation.

### Problem: Extreme week-over-week changes

**Symptoms**:
State shows +25 point jump in one week.

**Cause**: Likely data revision or error, not real change.

**Solutions**:

**1. Verify with web interface**:
Check https://quickstats.nass.usda.gov/ to confirm values.

**2. Check for revisions**:
NASS occasionally revises recently published data.

**3. Flag as outlier**:
```python
if abs(wow_delta) > 20:
    print(f"Warning: Extreme change detected: {state} {wow_delta:+.1f}")
    # Verify before reporting
```

## Performance Issues

### Problem: Queries take too long

**Symptoms**:
Waiting 10+ seconds for response.

**Causes**:
1. Cache miss
2. Large query (many states/weeks)
3. Slow network

**Solutions**:

**1. Use cache**:
First query slow (2-5s), subsequent fast (<200ms).

**2. Reduce query scope**:
```python
# Slow: All weeks, all states
data = client.get_crop_conditions('CORN', 2024, agg_level='STATE')

# Fast: One week, national
data = client.get_crop_conditions('CORN', 2024, week=32, agg_level='NATIONAL')
```

**3. Prefetch**:
For daily use, prefetch overnight:
```bash
# Add to crontab
0 6 * * 1 python /path/to/scripts/fetch_nass.py --commodity CORN --year 2024 --prefetch
```

Runs Monday 6am, loads cache before work day.

**4. Check network**:
```bash
ping quickstats.nass.usda.gov
```

If slow (>200ms) or packet loss, network issue.

## Python/Dependency Issues

### Problem: "ModuleNotFoundError"

**Symptoms**:
```
ModuleNotFoundError: No module named 'pandas'
```

**Cause**: Required libraries not installed.

**Solutions**:

**1. Install dependencies**:
```bash
pip install pandas numpy requests scipy
```

Or if using requirements.txt:
```bash
pip install -r requirements.txt
```

**2. Check Python version**:
```bash
python3 --version
# Should be 3.8+
```

**3. Use virtual environment** (recommended):
```bash
python3 -m venv venv
source venv/bin/activate
pip install pandas numpy requests scipy
```

### Problem: Import errors

**Symptoms**:
```
ImportError: cannot import name 'CacheManager' from 'utils.cache_manager'
```

**Cause**: Path issues or __init__.py missing.

**Solutions**:

**1. Verify __init__.py exists**:
```bash
ls scripts/utils/__init__.py
```

Should exist (can be empty).

**2. Check file structure**:
```
scripts/
├── fetch_nass.py
├── parse_conditions.py
├── analyze_crops.py
└── utils/
    ├── __init__.py
    ├── cache_manager.py
    ├── rate_limiter.py
    └── validators.py
```

**3. Run from correct directory**:
```bash
# From skill root
python scripts/fetch_nass.py

# NOT from scripts/
cd scripts
python fetch_nass.py  # May have import issues
```

## Getting Help

### Diagnostic Information to Collect

When reporting issues, include:

**1. Skill version**:
```bash
grep "Version:" us-crop-monitor/SKILL.md | head -1
```

**2. API connectivity**:
```bash
curl -I https://quickstats.nass.usda.gov/api/api_GET
# Should return HTTP 200 (or 400 - still means connected)
```

**3. Error messages**:
Copy full error traceback.

**4. Query details**:
- Commodity
- Year
- Week
- State (if specific)

**5. Cache stats**:
```python
from utils.cache_manager import CacheManager
cache = CacheManager()
print(cache.stats())
```

### Quick Diagnostic Script

```python
#!/usr/bin/env python3
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

# Check 1: API key
api_key = os.environ.get('NASS_API_KEY')
print(f"API key set: {bool(api_key)}")
if api_key:
    print(f"API key length: {len(api_key)}")

# Check 2: Dependencies
try:
    import pandas
    import numpy
    import requests
    print("Dependencies: OK")
except ImportError as e:
    print(f"Dependencies: MISSING - {e}")

# Check 3: Utils imports
try:
    from utils.cache_manager import CacheManager
    from utils.rate_limiter import RateLimiter
    from utils.validators import validate_commodity
    print("Utils: OK")
except ImportError as e:
    print(f"Utils: FAILED - {e}")

# Check 4: API connectivity
try:
    import requests
    r = requests.get('https://quickstats.nass.usda.gov/api/api_GET', timeout=5)
    print(f"API accessible: {r.status_code == 400}")  # 400 expected (no params)
except Exception as e:
    print(f"API accessible: FAILED - {e}")

# Check 5: Cache
try:
    cache = CacheManager()
    stats = cache.stats()
    print(f"Cache: {stats['total_entries']} entries, {stats['total_size_kb']} KB")
except Exception as e:
    print(f"Cache: FAILED - {e}")

print("\nDiagnostics complete!")
```

Save as `diagnose.py` and run:
```bash
python diagnose.py
```

## Common Error Messages Reference

| Error | Cause | Solution |
|-------|-------|----------|
| `API key is required` | Env var not set | Set NASS_API_KEY |
| `Invalid API key (401)` | Wrong key | Verify key, request new |
| `No data found` | Invalid params or no data exists | Check commodity/year/week |
| `Rate limit exceeded` | Too many requests | Wait, enable cache |
| `Server error (500)` | NASS API down | Retry later |
| `Request timeout` | Network slow | Check connection |
| `ModuleNotFoundError` | Missing dependency | pip install package |
| `Percentage sum != 100` | Data rounding | Use ±2% tolerance |
| `Cache write failed` | Permission issue | Check directory permissions |

## Still Need Help?

1. Review SKILL.md for feature documentation
2. Check references/ for methodology details
3. Test with provided example queries
4. Run diagnostic script above
5. Check NASS API status: https://www.nass.usda.gov/
