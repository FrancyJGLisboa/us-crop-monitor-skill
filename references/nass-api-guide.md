# NASS QuickStats API - Complete Guide

## Overview

The USDA National Agricultural Statistics Service (NASS) QuickStats API provides programmatic access to the most comprehensive source of U.S. agricultural statistics. This guide covers everything needed to effectively use the API for crop condition monitoring.

## API Basics

### Base URL

```
https://quickstats.nass.usda.gov/api/
```

### Authentication

All requests require an API key passed as query parameter:

```
?key=YOUR_API_KEY
```

Or as HTTP header:
```
X-API-Key: YOUR_API_KEY
```

### Getting an API Key

1. Visit: https://quickstats.nass.usda.gov/api/
2. Click "Request API Key"
3. Fill simple form (name, email, intended use)
4. Key sent instantly to email
5. Key is permanent (does not expire)

## Main Endpoints

### 1. /api/api_GET

Primary endpoint for data retrieval.

**Purpose**: Fetch agricultural statistics

**Method**: GET

**Parameters**: Combination of WHAT/WHERE/WHEN filters

**Response**: JSON array of records (max 50,000)

**Example**:
```
GET /api/api_GET?key=YOUR_KEY&commodity_desc=CORN&year=2024&statisticcat_desc=CONDITION
```

**Response Structure**:
```json
{
  "data": [
    {
      "source_desc": "SURVEY",
      "sector_desc": "CROPS",
      "commodity_desc": "CORN",
      "statisticcat_desc": "CONDITION",
      "short_desc": "CORN - CONDITION, MEASURED IN PCT GOOD",
      "domain_desc": "TOTAL",
      "state_name": "IOWA",
      "agg_level_desc": "STATE",
      "year": 2024,
      "freq_desc": "WEEKLY",
      "reference_period_desc": "WEEK #32",
      "week_ending": "2024-08-11",
      "Value": "56",
      "CV (%)": ""
    }
  ]
}
```

### 2. /api/get_param_values

Get possible values for any parameter.

**Purpose**: Discover valid parameter values

**Method**: GET

**Parameters**:
- `param`: Parameter name to query

**Example**:
```
GET /api/get_param_values?key=YOUR_KEY&param=commodity_desc
```

**Response**:
```json
{
  "commodity_desc": [
    "ALMONDS",
    "APPLES",
    "BARLEY",
    "CORN",
    ...
  ]
}
```

**Useful for**:
- Discovering available commodities
- Finding valid state names
- Getting all years with data

### 3. /api/get_counts

Get record count without fetching data.

**Purpose**: Check result size before full request

**Method**: GET

**Parameters**: Same as api_GET

**Response**:
```json
{
  "count": 1234
}
```

**Use Case**: Validate query before requesting large dataset

## Parameter Categories

### WHAT Parameters (Data Selection)

**commodity_desc**: Crop or livestock commodity
- Examples: `CORN`, `SOYBEANS`, `WHEAT`, `CATTLE`
- Case-sensitive
- Use get_param_values to discover all

**statisticcat_desc**: Type of statistic
- `CONDITION`: Crop condition ratings
- `PROGRESS`: Planting/harvest progress
- `PRODUCTION`: Production estimates
- `YIELD`: Yield estimates
- `AREA`: Area planted/harvested
- `PRICE`: Price data

**short_desc**: Detailed description with units
- Very specific, includes measurement
- Example: `CORN - CONDITION, MEASURED IN PCT EXCELLENT`
- Example: `SOYBEANS - PROGRESS, MEASURED IN PCT PLANTED`

**domain_desc**: Data domain
- Usually `TOTAL` for condition data
- Can be `ORGANIC`, `NON-ORGANIC`, etc.

### WHERE Parameters (Geography)

**agg_level_desc**: Aggregation level
- `NATIONAL`: US-level
- `STATE`: State-level
- `COUNTY`: County-level (not all data available)
- `REGION`: Regional aggregations
- `WATERSHED`: Watershed level

**state_name**: State name (uppercase)
- Example: `IOWA`, `ILLINOIS`, `CALIFORNIA`
- Required when agg_level_desc=STATE and filtering to one state

**state_alpha**: 2-letter state code
- Example: `IA`, `IL`, `CA`
- Alternative to state_name

**county_code**: FIPS county code
- Format: 3-digit number
- Requires agg_level_desc=COUNTY

### WHEN Parameters (Time)

**year**: Calendar year
- Format: 4-digit integer
- Available: 1866-present (varies by commodity/statistic)

**freq_desc**: Frequency of data
- `WEEKLY`: Weekly reports (crop condition/progress)
- `MONTHLY`: Monthly estimates
- `ANNUAL`: Yearly summaries
- `POINT IN TIME`: Specific dates

**reference_period_desc**: Specific time period
- Format varies by freq_desc
- Weekly: `WEEK #32`, `WEEK #01`
- Monthly: `JAN`, `FEB`, `MAR`, etc.
- Annual: `YEAR`

**week_ending**: Date string
- Format: `YYYY-MM-DD`
- Sunday of week for weekly data
- Useful for exact date matching

**begin_code** and **end_code**: Date range
- Format: `YYYYMMDD`
- Used for custom date ranges

### Other Important Parameters

**source_desc**: Data source
- `SURVEY`: Survey data (most common)
- `CENSUS`: Census of Agriculture
- `OTHER`: Administrative data

**sector_desc**: Agricultural sector
- `CROPS`: Field crops
- `ANIMALS & PRODUCTS`: Livestock
- `ECONOMICS`: Economic data
- `DEMOGRAPHICS`: Farm demographics

**unit_desc**: Unit of measurement
- `PCT`: Percentage
- `BU`: Bushels
- `TONS`: Tons
- `$ / BU`: Dollars per bushel

## Operators

Add operators to parameter names for advanced filtering:

**Comparison Operators**:
- `__LE`: Less than or equal (≤)
- `__LT`: Less than (<)
- `__GT`: Greater than (>)
- `__GE`: Greater than or equal (≥)
- `__NE`: Not equal (≠)

**String Operators**:
- `__LIKE`: Pattern matching (SQL LIKE)
- `__NOT_LIKE`: Negative pattern match

**Examples**:
```
year__GE=2020           # Years >= 2020
year__LE=2023           # Years <= 2023
commodity_desc__LIKE=WHEAT%   # All wheat types
state_name__NOT_LIKE=%DAKOTA% # Exclude Dakota states
```

## Response Formats

### JSON (Default)

```
GET /api/api_GET?key=KEY&...
```

Returns JSON object with `data` array.

### CSV

```
GET /api/api_GET?key=KEY&format=CSV&...
```

Returns CSV text, useful for direct import to Excel/R/Python.

### XML

```
GET /api/api_GET?key=KEY&format=XML&...
```

Returns XML document.

## Rate Limits and Best Practices

### Rate Limits

NASS does not officially document rate limits, but practical observation suggests:

- **Recommended**: 10-15 requests/minute
- **Max record limit**: 50,000 records per request
- **Concurrent requests**: Not recommended

### Best Practices

**1. Use Specific Parameters**
- Don't fetch all data and filter locally
- Narrow queries to exactly what you need

**Bad**:
```python
# Fetches ALL crop condition data (huge!)
params = {'statisticcat_desc': 'CONDITION'}
```

**Good**:
```python
# Specific query
params = {
    'commodity_desc': 'CORN',
    'statisticcat_desc': 'CONDITION',
    'year': 2024,
    'reference_period_desc': 'WEEK #32',
    'agg_level_desc': 'STATE'
}
```

**2. Cache Aggressively**
- Historical data never changes → cache permanently
- Current week data can be revised → cache with 7-day TTL
- Implement local caching to minimize API calls

**3. Handle Errors Gracefully**
- 401: Invalid API key
- 429: Rate limit (wait and retry)
- 500/502/503: Server issues (retry with backoff)
- Empty data: Not an error, just no data available

**4. Batch Requests Intelligently**
- Fetch multiple states in one call (agg_level=STATE without state filter)
- Fetch full season with one call (omit reference_period_desc)
- More efficient than multiple individual requests

**5. Respect Publication Schedule**
- Crop Progress & Condition published Mondays 4pm ET
- Querying before publication returns previous week
- Build delays into automated workflows

## Crop Condition Specifics

### Data Source

Crop condition data comes from weekly surveys during growing season.

**Survey Methodology**:
- Voluntary reporters (farmers, extension agents)
- Stratified sampling by state
- Reporters rate fields in 5 categories

### Condition Categories

1. **VERY POOR**: < 20% of potential yield expected
2. **POOR**: 20-40% of potential
3. **FAIR**: 40-60% of potential
4. **GOOD**: 60-80% of potential
5. **EXCELLENT**: > 80% of potential

Sum of all five categories should equal 100% (within rounding).

### Important Considerations

**Subjectivity**: Ratings are subjective opinions, not measured data

**Relative Measure**: "Good" in a drought year may differ from "Good" in ideal conditions

**State Variation**: Rating standards can vary slightly by state/reporter

**Temporal Consistency**: Year-over-year comparisons more reliable than absolute values

### Typical Query for Current Conditions

```python
params = {
    'key': API_KEY,
    'source_desc': 'SURVEY',
    'sector_desc': 'CROPS',
    'commodity_desc': 'CORN',  # or SOYBEANS, WHEAT
    'statisticcat_desc': 'CONDITION',
    'agg_level_desc': 'STATE',  # or NATIONAL
    'year': 2024,
    'reference_period_desc': 'WEEK #32',
    'freq_desc': 'WEEKLY'
}
```

This returns all 5 condition categories for all states for specified week.

### Getting Latest Week

API doesn't provide "latest week" directly. Must:
1. Query without reference_period_desc
2. Extract all available weeks
3. Take max week number

Or use our `get_latest_week()` function which does this automatically.

## Data Coverage

### Temporal Coverage

**Crop Condition Data**:
- Started: Mid-1980s (exact year varies by commodity)
- Frequency: Weekly during growing season
- Historical: Fully available back to start

**Growing Seasons** (approximate):
- **Corn**: Weeks 18-42 (May-October)
- **Soybeans**: Weeks 18-44 (May-November)
- **Winter Wheat**: Weeks 14-26 (April-June)
- **Spring Wheat**: Weeks 20-36 (May-September)

### Geographic Coverage

Not all states grow all crops. Coverage by major crops:

**Corn**:
- Major: IA, IL, NE, MN, IN, SD, OH, WI, MO, KS
- Minor: MI, KY, NC, PA, TX
- Total: ~20 states with regular reporting

**Soybeans**:
- Major: IA, IL, MN, NE, IN, MO, OH, SD, ND, AR
- Minor: MI, WI, KS, KY, MS, TN
- Total: ~18 states

**Wheat**:
- Winter: KS, OK, TX, MT, CO, NE, SD
- Spring: ND, MT, MN, SD, WA, ID
- Total: ~20 states combined

## Common Query Patterns

### Pattern 1: Current National Conditions

Get latest national snapshot:

```python
# Get latest week first
all_weeks = api.get('api_GET', {
    'commodity_desc': 'CORN',
    'statisticcat_desc': 'CONDITION',
    'agg_level_desc': 'NATIONAL',
    'year': 2024
})

# Extract latest week
latest_week = max(extract_week_numbers(all_weeks))

# Get specific week data
data = api.get('api_GET', {
    'commodity_desc': 'CORN',
    'statisticcat_desc': 'CONDITION',
    'agg_level_desc': 'NATIONAL',
    'year': 2024,
    'reference_period_desc': f'WEEK #{latest_week:02d}'
})
```

### Pattern 2: State Rankings

Get all states for one week:

```python
data = api.get('api_GET', {
    'commodity_desc': 'SOYBEANS',
    'statisticcat_desc': 'CONDITION',
    'agg_level_desc': 'STATE',
    'year': 2024,
    'reference_period_desc': 'WEEK #32'
    # Note: No state_name filter - gets ALL states
})
```

Returns ~100 records (5 categories × ~20 states).

### Pattern 3: Historical Trend

Get full season for analysis:

```python
data = api.get('api_GET', {
    'commodity_desc': 'CORN',
    'statisticcat_desc': 'CONDITION',
    'agg_level_desc': 'NATIONAL',
    'year': 2024
    # Note: No reference_period_desc - gets ALL weeks
})
```

Returns all weeks published so far in year.

## Error Handling

### HTTP Status Codes

- **200**: Success (but check if data array is empty)
- **401**: Unauthorized (invalid API key)
- **429**: Too Many Requests (rate limit)
- **500/502/503**: Server errors (retry)

### Empty Results

```json
{"data": []}
```

Not an error! Means:
- No data exists for parameters
- Parameters are valid but no matching records
- Common causes: Wrong week number, commodity/state combo doesn't exist

### Handling Example

```python
try:
    response = requests.get(url, params=params)

    if response.status_code == 401:
        raise AuthenticationError("Invalid API key")

    if response.status_code == 429:
        time.sleep(60)  # Wait 1 minute
        # Retry...

    if response.status_code >= 500:
        # Server error, retry with backoff
        ...

    data = response.json()

    if not data or len(data) == 0:
        raise DataNotFoundError("No data for parameters")

except requests.Timeout:
    # Handle timeout
    ...
```

## Additional Resources

**Official Documentation**: https://quickstats.nass.usda.gov/api/

**API Registration**: https://quickstats.nass.usda.gov/api/#registration

**Quick Stats Web Interface**: https://quickstats.nass.usda.gov/
- Useful for exploring data before coding
- Can build queries visually
- Export to CSV

**NASS Developer Page**: https://www.nass.usda.gov/developer/

**Parameter Definitions**: https://quickstats.nass.usda.gov/api/#param_define
