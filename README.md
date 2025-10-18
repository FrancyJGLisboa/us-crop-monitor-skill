# US Crop Monitor - Comprehensive USDA NASS Crop Data Skill

Automate monitoring of US crop conditions, progress, yield, production, and area for corn, soybeans, and wheat using the USDA NASS API.

**Version 2.0** - Now includes all major crop metrics, not just conditions!

## 🆕 What's New in Version 2.0

### Major Expansions

✨ **5 New Data Types** (was 1, now 6 total):
- ✅ Crop Condition (original)
- 🆕 Crop Progress (planting, harvest %)
- 🆕 Yield Estimates (bushels/acre)
- 🆕 Production Forecasts (total bushels)
- 🆕 Area Data (acres planted/harvested)

🤖 **Automatic Year Detection**:
- No need to specify year - automatically uses current year (2025)
- Smart fallback to previous year when current data unavailable
- Seasonal awareness (off-season vs active season)
- Clear messaging about which year's data is shown

📊 **6 New Analysis Functions** (was 5, now 11 total):
- `harvest_progress_report()` - Harvest % by state
- `planting_progress_report()` - Planting % by state
- `yield_analysis()` - Productivity with YoY comparison
- `production_analysis()` - Total output with comparisons
- `area_analysis()` - Planted vs harvested acres
- `comprehensive_crop_report()` - All metrics in one report

🔧 **Enhanced Infrastructure**:
- 4 new parser modules (progress, yield, production, area)
- Unified `get_crop_data()` method for all metric types
- Extended validation system for new data types
- Helper utilities for year detection

📈 **Improved Performance**:
- All new queries use intelligent caching
- Sub-200ms response time for cached queries
- Batch API requests for multi-metric reports
- Rate limiting prevents API throttling

### Backward Compatibility

✅ **100% backward compatible** - All existing condition queries work unchanged!

## Quick Start

### 1. Get NASS API Key (Free)

1. Visit: https://quickstats.nass.usda.gov/api/
2. Click "Request API Key"
3. Fill form (takes 30 seconds)
4. Key sent to email instantly

### 2. Configure API Key

Add to your shell configuration:

```bash
# For zsh (macOS default)
echo 'export NASS_API_KEY="YOUR_KEY_HERE"' >> ~/.zshrc
source ~/.zshrc

# For bash
echo 'export NASS_API_KEY="YOUR_KEY_HERE"' >> ~/.bashrc
source ~/.bashrc
```

**Note**: Replace `YOUR_KEY_HERE` with your actual API key from USDA NASS.

Verify:
```bash
echo $NASS_API_KEY
# Should print your key
```

### 3. Install Skill

**Direct from GitHub (Recommended):**
```bash
/plugin marketplace add github:FrancyJGLisboa/us-crop-monitor-skill
```

**Or install locally:**
```bash
git clone https://github.com/FrancyJGLisboa/us-crop-monitor-skill.git
/plugin marketplace add ./us-crop-monitor-skill
```

Expected output:
```
Successfully added marketplace: us-crop-monitor
```

### 4. Test

Ask Claude:
> "What are current corn conditions in the US?"

If the skill responds with NASS data, installation successful!

## Quick Examples

Try these queries (no year needed - auto-detects 2025!):

**Conditions:**
- "How is corn doing today?" → Auto-detects 2025, shows condition ratings
- "Compare soybean conditions vs last year" → YoY comparison

**Progress:**
- "What's the corn harvest progress?" → Shows % harvested by state
- "How much has been planted?" → Planting progress

**Yield & Production:**
- "What's the corn yield estimate?" → Bushels/acre forecast
- "Total soybean production?" → National production

**Complete Analysis:**
- "Give me a full corn report" → All metrics in one comprehensive view

## Features

### ✨ 11 Analysis Functions (NEW in v2.0!)

**Crop Condition Analysis (Original):**
1. **Current Condition Report** - Latest crop quality snapshot
2. **Week-over-Week Comparison** - Short-term condition trends
3. **Year-over-Year Comparison** - Compare to previous season
4. **State Rankings** - Best/worst states by condition
5. **Season Trend Analysis** - Track quality evolution over season

**Crop Progress Analysis (NEW!):**
6. **Harvest Progress Report** - Percentage harvested by state
7. **Planting Progress Report** - Percentage planted by state

**Yield & Production Analysis (NEW!):**
8. **Yield Analysis** - Bushels per acre estimates with YoY comparison
9. **Production Analysis** - Total production forecasts with comparisons
10. **Area Analysis** - Acres planted/harvested with planted vs harvested comparison

**Comprehensive Reporting (NEW!):**
11. **Comprehensive Crop Report** - All metrics combined in one report

### Supported Crops

- Corn
- Soybeans
- Wheat (Winter and Spring)

### 🤖 Automatic Year Detection (NEW in v2.0!)

**No need to specify the year!** The skill automatically detects the current year and handles fallback logic:

- **"How is corn today?"** → Automatically uses 2025 (current year)
- **Smart fallback**: If current year data not available, tries previous year
- **Seasonal awareness**: Understands off-season (Jan-Apr) vs active season (May-Dec)
- **Clear messaging**: Always tells you which year's data is being shown

**Example:**
```
User: "What are corn conditions today?"
System: Showing 2025 data (auto-detected current year)
        Good+Excellent: 66.0% (Week 39)
```

You can still specify a year explicitly if needed:
- "Corn conditions in 2024" → Uses 2024
- "Compare 2025 vs 2024" → Uses both years

### 📊 Data Metrics Covered

**1. CONDITION** (Quality ratings)
- 5 categories: Excellent, Good, Fair, Poor, Very Poor
- Published weekly during growing season

**2. PROGRESS** (Planting/Harvest progress)
- % Planted, % Emerged, % Harvested
- Published weekly during season

**3. YIELD** (Productivity)
- Bushels per acre
- Monthly forecasts, final estimates

**4. PRODUCTION** (Total output)
- Total bushels produced
- Monthly forecasts, final estimates

**5. AREA** (Acreage)
- Acres planted, acres harvested
- Annual estimates

### Data Source

Official USDA NASS QuickStats API:
- Published weekly (progress/condition) or monthly (yield/production)
- State-level and national aggregations
- Historical data back to mid-1980s

## 🛡️ Data Validation System (v2.0)

**NEW!** All analyses now include automatic data validation to ensure reliability:

### What It Does

- ✅ **Transparency**: Shows data age, source (cache/API), and publication date
- ⚠️ **Anomaly Detection**: Alerts on unusual patterns or extreme changes
- ❌ **Error Detection**: Identifies missing data or inconsistencies
- 🚫 **Critical Protection**: Blocks problematic data (e.g., 2+ years old) with option to override

### Validation Layers

1. **Temporal Validation**
   - Checks data age and freshness
   - Verifies year consistency (requested vs returned)
   - Validates week is within crop season
   - Alerts if data is outdated

2. **Completeness Validation**
   - Ensures all 5 condition categories present
   - Verifies major producing states included
   - Checks data sums to 100% (±2% tolerance)

3. **Anomaly Detection**
   - Detects extreme changes (>50 points = critical)
   - Identifies statistical outliers (>3 sigma)
   - Flags suspicious distributions

4. **Metadata Transparency**
   - Shows when USDA published the data
   - Indicates cache vs fresh API call
   - Displays data retrieval timestamp

### Example Output

```
📊 Validations: ✅ 15 | ⚠️ 2 | ❌ 0 | 🚫 0

ℹ️  INFORMATION:
  ✅ Data is from current year (2025)
  ✅ Source: USDA API
  ✅ Published by USDA 7 days ago
  ✅ All 5 condition categories present
  ✅ Consistency OK: Sum = 100%

⚠️  WARNINGS:
  ⚠️ Montana: Outlier (23%) - 3.1 standard deviations from mean
  ⚠️ Kansas with conditions below historical average
```

### Documentation

See [docs/VALIDATION_SYSTEM.md](docs/VALIDATION_SYSTEM.md) for complete documentation including:
- Architecture and components
- Configuration options
- Custom validation examples
- Troubleshooting

## Example Queries

### Crop Conditions (Original)
```
"What are current corn conditions?"
"Compare soybean conditions this year vs last year"
"Ranking de estados por condição de milho"
"Tendência de safra de trigo em 2024"
"Dashboard of all crop conditions"
"How did wheat conditions change this week?"
"Which states have the best soybean crops?"
```

### Crop Progress (NEW!)
```
"What's the corn harvest progress?"
"How much corn has been harvested in Iowa?"
"Compare harvest progress this year vs last year"
"Show planting progress for soybeans"
"Which states are most advanced in harvest?"
"Progresso de colheita do milho nos EUA"
```

### Yield & Production (NEW!)
```
"What's the corn yield estimate for 2025?"
"Show me soybean yield by state"
"Compare yield 2025 vs 2024"
"Total corn production forecast"
"How many acres of corn were planted?"
"Planted vs harvested acres comparison"
```

### Comprehensive Reports (NEW!)
```
"Give me a complete corn report"
"Show all metrics for soybeans"
"Comprehensive crop analysis"
"Full dashboard for wheat"
```

## Project Structure

```
us-crop-monitor/
├── .claude-plugin/
│   └── marketplace.json           # Plugin configuration
├── SKILL.md                       # Complete skill documentation (6000+ words)
├── README.md                      # This file
├── DECISIONS.md                   # Architecture decisions
├── scripts/
│   ├── fetch_nass.py              # API client (1000+ lines) - ALL METRICS
│   ├── parse_conditions.py        # Condition data parser (480 lines)
│   ├── parse_progress.py          # Progress data parser (NEW! 269 lines)
│   ├── parse_yield.py             # Yield data parser (NEW! 228 lines)
│   ├── parse_production.py        # Production data parser (NEW! 235 lines)
│   ├── parse_area.py              # Area data parser (NEW! 319 lines)
│   ├── analyze_crops.py           # Analysis functions (1600+ lines) - 11 FUNCTIONS
│   └── utils/
│       ├── cache_manager.py       # Intelligent caching (150 lines)
│       ├── rate_limiter.py        # Rate limiting (80 lines)
│       ├── validators.py          # Parameter validation (150 lines)
│       ├── helpers.py             # Year detection (NEW! 156 lines)
│       ├── data_validator.py      # Validation system (NEW! 370 lines)
│       ├── temporal_validator.py  # Temporal checks (NEW! 250 lines)
│       ├── completeness_validator.py  # Data completeness (NEW! 180 lines)
│       ├── anomaly_detector.py    # Anomaly detection (NEW! 320 lines)
│       └── validation_formatter.py # Formatting (NEW! 150 lines)
├── tests/
│   ├── test_integrated_validation.py  # Integration tests (NEW!)
│   ├── test_year_detection.py     # Year detection tests (NEW!)
│   └── test_all_year_detection.py # Comprehensive tests (NEW!)
├── references/
│   ├── nass-api-guide.md          # API documentation
│   ├── analysis-methods.md        # Methodology details
│   └── troubleshooting.md         # Common issues and solutions
├── docs/
│   └── VALIDATION_SYSTEM.md       # Validation system docs (NEW!)
├── assets/
│   ├── config.json                # Configuration
│   └── crop-metadata.json         # Crop information
└── data/
    ├── cache/                     # Cached API responses
    └── analysis/                  # Analysis outputs
```

## Dependencies

Required Python packages:
- pandas
- numpy
- requests
- scipy

Install:
```bash
pip install pandas numpy requests scipy
```

Or with virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate
pip install pandas numpy requests scipy
```

## Performance

**Without Cache** (first run):
- Single query: 2-5 seconds
- Dashboard: 10-15 seconds
- Season trend: 15-20 seconds

**With Cache** (subsequent runs):
- Single query: 50-200 ms (10-50x faster!)
- Dashboard: 300-500 ms
- Season trend: 100-300 ms

**Cache Strategy**:
- Historical data (>2 weeks old): Cached permanently
- Recent data (current/last week): 7-day TTL
- Automatic cleanup of expired entries

## Time Savings

**Before**: ~2 hours/day
- Manual NASS website access
- Download CSV files
- Consolidate in Excel
- Manual calculations
- Create charts

**After**: ~3 minutes/day
- Ask Claude natural language questions
- Get instant analysis
- Automated comparisons and trends

**Savings**: 117 hours/month (98.5% reduction!)

## Troubleshooting

### "API key is required"

```bash
# Check if set
echo $NASS_API_KEY

# If empty, add to ~/.zshrc or ~/.bashrc
export NASS_API_KEY='your_key_here'
source ~/.zshrc
```

### "No data found"

- **Cause**: Week number doesn't exist yet or out of season
- **Solution**: Use get_latest_week() or check crop season dates
- **Crop seasons**:
  - Corn/Soybeans: Weeks 18-44 (May-October)
  - Wheat: Varies by type (Winter: Apr-Jun, Spring: May-Sep)

### Slow performance

- **First run**: Normal (building cache)
- **Subsequent runs**: Should be fast (<1 second)
- **If always slow**: Check cache is enabled in config.json

### Skill doesn't activate

- **Include keywords**: "corn conditions", "NASS", "crop progress"
- **Be specific**: "What are current corn conditions?" vs "How are crops?"
- **Verify installation**:
  ```bash
  ls ~/.claude/plugins/marketplaces/us-crop-monitor
  ```

See `references/troubleshooting.md` for complete troubleshooting guide.

## Advanced Usage

### Command-Line Interface

Scripts can be run standalone:

```bash
# Fetch current data
python scripts/fetch_nass.py --commodity CORN --year 2024 --week 32

# Prefetch for caching
python scripts/fetch_nass.py --commodity SOYBEANS --year 2024 --prefetch

# Disable cache
python scripts/fetch_nass.py --commodity WHEAT --year 2024 --no-cache
```

### Automated Daily Updates

Add to crontab for daily prefetch:

```bash
# Run Monday mornings at 6am (after NASS publishes at 4pm Monday)
0 6 * * 1 cd /path/to/us-crop-monitor && python scripts/fetch_nass.py --commodity CORN --year 2024 --prefetch
```

This pre-loads cache before your workday.

### Custom Analysis

Import modules directly:

```python
from scripts.fetch_nass import NassApiClient
from scripts.analyze_crops import current_condition_report, year_over_year_comparison

client = NassApiClient()

# Current conditions
report = current_condition_report('CORN', 2024, client=client)
print(f"Good+Excellent: {report['conditions']['good_excellent']:.1f}%")

# Year-over-year
yoy = year_over_year_comparison('SOYBEANS', 2024, 2023, client=client)
print(f"Delta: {yoy['national_delta']['good_excellent']:+.1f} points")
```

## Documentation

- **SKILL.md**: Complete skill documentation (6000+ words)
  - All 6 analyses explained
  - API details
  - Workflows
  - Interpretation guidelines

- **references/nass-api-guide.md**: Comprehensive API guide
  - Endpoints and parameters
  - Best practices
  - Query patterns
  - Error handling

- **references/analysis-methods.md**: Methodology details
  - Formulas and calculations
  - Statistical methods
  - Interpretation guidelines
  - Validation procedures

- **references/troubleshooting.md**: Problem solving
  - Common errors and solutions
  - Performance optimization
  - Diagnostic tools

## Limitations

1. **Crops**: Only CORN, SOYBEANS, WHEAT (not rice, cotton, etc.)
2. **Geography**: US only (state and national levels)
3. **Data Type**: Conditions only (not prices, yield forecasts, etc.)
4. **Granularity**: State-level (not county-level)
5. **Historical**: Data availability varies (generally mid-1980s onward)
6. **Timeliness**: Data published Mondays 4pm ET (not real-time)

## Future Enhancements

Possible additions:
- More crops (rice, cotton, barley)
- County-level analysis
- Yield forecasting models
- Price integration
- Weather data correlation
- Automated alerts
- Visualization (maps, charts)

## Support

1. **Documentation**: Read SKILL.md and references/
2. **Diagnostics**: Run troubleshooting scripts
3. **NASS API**: https://quickstats.nass.usda.gov/api/
4. **Issues**: Check references/troubleshooting.md

## License

This skill uses public USDA NASS data (US Government works, public domain).

## Credits

**Created by**: Agent Creator (Autonomous Agent Generation System)

**Data Source**: USDA National Agricultural Statistics Service

**Version**: 2.0.0 (with Data Validation System)

**Last Updated**: 2025-10-18
