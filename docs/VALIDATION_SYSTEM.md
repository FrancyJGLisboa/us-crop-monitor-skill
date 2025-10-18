# Data Validation System v2.0

## 📋 Overview

The Data Validation System was introduced in version 2.0 of the **us-crop-monitor** skill to ensure integrity, transparency, and reliability of USDA NASS crop condition data.

### Why Was It Created?

**Original Problem:**
Users received data without any context about:
- Data age (could be months old)
- Source (cache vs API)
- Temporal discrepancies (receiving 2024 data when we're in 2025)
- Anomalies or suspicious patterns

**Solution:**
Multi-layer automatic validation system that:
- ✅ Provides full transparency about data provenance
- ⚠️ Detects and alerts about potential problems
- ❌ Identifies serious errors
- 🚫 Blocks critical data (with override option)

---

## 🏗️ System Architecture

### Main Components

```
┌─────────────────────────────────────────┐
│        Data Validator (Core)            │
│    Central Orchestrator + Severities    │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴───────┐
       │               │
       ▼               ▼
┌─────────────┐  ┌─────────────┐
│ Validators  │  │ Formatters  │
└─────────────┘  └─────────────┘
       │               │
   ┌───┴───┬───────┬───┴───┐
   │       │       │       │
   ▼       ▼       ▼       ▼
Temporal Complete Anomaly Metadata
```

---

## 🔍 Validators

### 1. **Temporal Validator**
Validates temporal aspects of data.

**Checks:**
- ✅ Requested year vs returned year vs current year
- ✅ Data age (freshness)
- ✅ Week within crop season
- ✅ Date consistency

**Example Alerts:**
```
ℹ️  INFO: Data is from current year (2025)
⚠️  WARNING: Data is 25 days old - may be outdated
❌ ERROR: Requested year 2025, but received year 2024
🚫 CRITICAL: Data is 2 years old (2023 vs 2025)
```

### 2. **Completeness Validator**
Ensures all expected data is present.

**Checks:**
- ✅ All 5 condition categories present (EXCELLENT, GOOD, FAIR, POOR, VERY POOR)
- ✅ Important states present (major producers)
- ✅ Category sum = 100% (±2% tolerance)

**Example Alerts:**
```
ℹ️  INFO: All 5 condition categories present
✅ INFO: All top 10 CORN producers present in data
⚠️  WARNING: Iowa (major producer) missing from data
❌ ERROR: POOR category missing
```

### 3. **Anomaly Detector**
Detects abnormal patterns and outliers.

**Checks:**
- ✅ Extreme values (100% or 0% in categories)
- ✅ Abrupt week-over-week changes (>50 points = critical)
- ✅ Statistical outliers (>3 sigma)
- ✅ Large year-over-year changes (>30 points)

**Example Alerts:**
```
⚠️  WARNING: Montana: Outlier (23.0%) - 3.1 standard deviations from mean
🚫 CRITICAL: Missouri: EXTREME change: -52 points in one week
⚠️  WARNING: 8 states with large changes (>20 points)
```

### 4. **Metadata Manager**
Manages transparency and data provenance.

**Captured Information:**
- 📅 `fetched_at`: When data was retrieved
- 📍 `from_cache`: Whether from cache or API
- 📆 `published_at`: When USDA published the data
- 🔢 `version`: System version

**Metadata Examples:**
```
ℹ️  INFO: Data fetched 2 hours ago
ℹ️  INFO: Source: USDA API
ℹ️  INFO: Published by USDA 7 days ago
```

---

## ⚡ Severity Levels

The system uses 4 severity levels:

| Icon | Severity | Description | Action |
|------|---------|-------------|--------|
| ℹ️ | **INFO** | Informational, useful context | None |
| ⚠️ | **WARNING** | Attention needed, not critical | Alert user |
| ❌ | **ERROR** | Serious problem, data still usable | Alert strongly |
| 🚫 | **CRITICAL** | Severe, data unreliable | **BLOCK** + request confirmation |

---

## 🎯 How to Use

### Automatic Usage (Default)

All 6 analysis functions include validations automatically:

```python
from analyze_crops import current_condition_report

# Validations run automatically
report = current_condition_report('CORN', 2025)

# Access validation results
validation = report['validation']

print(f"Status: {validation['summary']}")  # "✅ 15 | ⚠️ 2"
print(validation['formatted'])  # Formatted validation section

if validation['should_block']:
    print("🚫 Data blocked!")
    print(validation['blocking_message'])
```

### Manual Validation

To validate custom data:

```python
from utils.data_validator import DataValidator, ValidationReport
from utils.temporal_validator import validate_temporal_consistency

# Create validator
validator = DataValidator()
report = ValidationReport()

# Run validations
validate_temporal_consistency(df, report, validator.config)

# View results
for result in report.results:
    print(result)
```

---

## ⚙️ Configuration

Settings in `config/validation_config.json`:

```json
{
  "temporal": {
    "max_age_warning_days": 30,
    "max_age_error_days": 90,
    "max_age_critical_years": 2
  },
  "anomaly": {
    "max_week_change_warning": 20,
    "max_week_change_critical": 50,
    "sigma_threshold": 3.0
  },
  "completeness": {
    "require_all_categories": true
  },
  "display": {
    "show_info": true,
    "show_warnings": true,
    "verbose_mode": false
  }
}
```

### Customization

```python
# Create validator with custom config
custom_config = {
    "temporal": {
        "max_age_warning_days": 14  # More strict
    }
}

validator = DataValidator(config=custom_config)
```

---

## 📊 Output Examples

### Example 1: Valid Data

```
======================================================================
 CURRENT CORN CONDITIONS - 2025 SEASON
======================================================================

📊 Validations: ℹ️ 5 | ⚠️ 0 | ❌ 0 | 🚫 0

Week #39 - Year 2025
📅 Published by USDA: 7 days ago
🔄 Source: Cache (fetched 2 hours ago)

NATIONAL CONDITIONS:
  Excellent: 17.0%
  Good: 49.0%
  → GOOD + EXCELLENT: 66.0%

✅ VALIDATIONS PASSED:
  ✅ Temporal OK: Data from 2025 (current year)
  ✅ Completeness OK: All 5 categories present
  ✅ Consistency OK: Sum = 100.0%
  ✅ Seasonal OK: Week #39 within season
  ✅ Anomalies: No abrupt changes detected
```

### Example 2: With Warnings

```
📊 Validations: ℹ️ 3 | ⚠️ 4 | ❌ 0 | 🚫 0

⚠️  WARNINGS:
  ⚠️ Data is 35 days old - may be outdated
  ⚠️ Montana: Outlier (19%) - 3.4 standard deviations
  ⚠️ Kansas (major producer) at 42% - below average
  ⚠️ 3 states with changes >20 points vs last week

✅ Data approved for use with above caveats
```

### Example 3: Critical Block

```
🚫 CRITICAL VALIDATION FAILED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROBLEM: The returned data is from 2023, but you requested 2025.

DETAILS:
  - Requested year: 2025
  - Returned year: 2023
  - Discrepancy: 2 years

POSSIBLE CAUSES:
  1. 2025 data not yet published by USDA
  2. API query error
  3. Date configuration problem

RECOMMENDATION:
  → Check if 2025 data has been published at:
    https://www.nass.usda.gov/Charts_and_Maps/Crop_Progress_&_Condition/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Do you want to continue anyway and see 2023 data? (yes/no)
```

---

## 🧪 Tests

Run system tests:

```bash
# Basic validation system test
python test_validation.py

# Specific tests
python -m pytest tests/test_temporal_validator.py
python -m pytest tests/test_completeness_validator.py
python -m pytest tests/test_anomaly_detector.py
```

---

## 📚 References

- [Validator Source Code](../scripts/utils/)
- [Default Configuration](../config/validation_config.json)
- [Usage Examples](../examples/)
- [USDA NASS API Docs](https://quickstats.nass.usda.gov/api/)

---

## 🔄 Version History

### v2.0.0 (2025-10-18)
- ✨ Initial validation system release
- ✅ 4 validators implemented
- ✅ Severity system
- ✅ Visual formatting with icons
- ✅ Automatic blocking for critical cases
- ✅ Full integration in all 6 analysis functions

---

**Developed to ensure you always know exactly what you're looking at when analyzing crop data.**
