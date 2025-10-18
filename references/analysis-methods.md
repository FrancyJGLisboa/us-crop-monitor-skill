# Crop Condition Analysis Methodologies

This document details the methodologies, formulas, and interpretations for all analyses provided by the US Crop Monitor skill.

## Core Metrics

### Good+Excellent Percentage

**Definition**: Sum of "Good" and "Excellent" condition percentages.

**Formula**:
```
G+E% = %Good + %Excellent
```

**Why This Metric?**:
- Industry standard for assessing crop health
- Strong correlation with final yield
- Simplifies communication (one number vs five)
- Historical comparability

**Interpretation Ranges**:
- **≥ 70%**: Excellent conditions, above-average yield expected
- **60-69%**: Good conditions, average yield expected
- **50-59%**: Fair conditions, below-average yield possible
- **< 50%**: Poor conditions, significant yield reduction likely

**Caveats**:
- Not a precise yield predictor (many other factors)
- "Good" definition varies by baseline expectations
- More useful for comparisons than absolute values

### Poor+Very Poor Percentage

**Definition**: Sum of "Poor" and "Very Poor" percentages.

**Formula**:
```
P+VP% = %Poor + %Very Poor
```

**Use**:
- Risk indicator
- P+VP% > 15% signals significant problems
- Useful for identifying distressed areas

## Analysis 1: Current Condition Report

### Methodology

**Objective**: Provide snapshot of current crop status.

**Steps**:

1. **Data Acquisition**:
   - Fetch latest week available
   - Get all 5 condition categories
   - National and/or state level

2. **Aggregation**:
   - If state-level requested: Return state directly
   - If national requested:
     - Use national records if available
     - Otherwise, average state percentages

3. **Calculation**:
   ```python
   G+E = Good% + Excellent%
   P+VP = Poor% + Very_Poor%
   ```

4. **Ranking** (if national):
   - Sort all states by G+E%
   - Identify top 5 and bottom 5

### Interpretation Guidelines

**National G+E%**:
- Compare to:
  - Previous week (is it improving?)
  - Same week last year (better or worse year?)
  - 5-year average for week (above or below normal?)

**State Rankings**:
- **Top states**: Favorable weather, good management
- **Bottom states**: Identify cause (drought, flood, pests)
- **Large producers in bottom**: Major risk to supply

**Within-State Distribution**:
- Ideal: High Excellent, low Poor/VP
- Concerning: Bimodal (high E + high VP = variable conditions)
- Mediocre but stable: High Fair

### Example Interpretation

```
CORN - Week #32, 2024
National: 69% G+E

Breakdown:
  Excellent: 15%
  Good: 54%
  Fair: 25%
  Poor: 5%
  Very Poor: 1%

Interpretation:
- Solid conditions overall (69% > average 66%)
- Well-distributed (not bimodal)
- Low stress (only 6% P+VP)
- Yield outlook: Above average
```

## Analysis 2: Week-over-Week Comparison

### Methodology

**Objective**: Detect short-term trends (improvement or deterioration).

**Steps**:

1. **Data Acquisition**:
   - Fetch current week (W)
   - Fetch previous week (W-1)
   - State-level for both

2. **Calculation**:
   ```python
   Delta_state = G+E%_W - G+E%_(W-1)
   Delta_national = mean(Delta_state)
   ```

3. **Categorization**:
   - Improved: Delta > 0
   - Deteriorated: Delta < 0
   - Unchanged: Delta = 0

4. **Ranking**:
   - Sort states by Delta
   - Top 5 improvements
   - Top 5 deteriorations

### Statistical Considerations

**Significance Thresholds**:
- |Delta| < 2 points: Noise (sampling variation)
- |Delta| 2-5 points: Moderate change (watch)
- |Delta| > 5 points: Significant change (investigate)

**Temporal Patterns**:
- Early season: Conditions often decline (heat stress)
- Mid-season: Can swing either way (weather dependent)
- Late season: Usually stable or slight decline

**Regional Patterns**:
- Drought emergence: Multi-state deterioration
- Storm damage: Localized deterioration
- Heat relief: Multi-state improvement

### Interpretation

**Positive Delta** (Improvement):
- Recent rainfall after dry period
- Cooler temperatures after heat
- Natural crop development (early season)

**Negative Delta** (Deterioration):
- Drought onset or intensification
- Heat stress
- Disease/pest pressure
- Storm damage

**Example**:
```
SOYBEANS Week #32 vs #31
National: 64% → 61% (Δ -3)

Top Deteriorations:
- Missouri: -11 points (drought stress)
- Arkansas: -7 points (heat wave)
- Tennessee: -6 points (dry conditions)

Interpretation:
Central Plains experiencing heat/drought.
Northern states stable. Monitor next 2 weeks;
if drought persists, expect further declines.
```

## Analysis 3: Year-over-Year Comparison

### Methodology

**Objective**: Compare current season to previous year(s).

**Steps**:

1. **Week Matching**:
   - Use same week number for both years
   - Week #32 of 2024 vs Week #32 of 2023
   - Accounts for seasonal timing

2. **Data Acquisition**:
   - Fetch Year Y, Week W
   - Fetch Year Y-1, Week W
   - State-level for both

3. **Calculation**:
   ```python
   Delta_YoY = G+E%_current_year - G+E%_previous_year
   ```

4. **Categorization**:
   ```python
   if Delta >= +10: "Much better"
   elif Delta >= +5: "Better"
   elif Delta >= -5: "Similar"
   elif Delta >= -10: "Worse"
   else: "Much worse"
   ```

### Contextual Factors

**Weather Differences**:
- Compare rainfall, temperature patterns
- Similar weather → direct comparison valid
- Different weather → contextualize

**Pest/Disease**:
- Major pest outbreaks affect comparability
- Example: 2012 drought vs 2013 normal year

**Management Changes**:
- Adoption of drought-tolerant varieties
- Changes in planting dates

### Yield Correlation

**Empirical Relationship**:
```
Yield change % ≈ 0.5 × (Delta G+E%)
```

**Example**:
- Delta G+E = +10 points
- Expected yield change ≈ +5%

**Caveat**: Rough estimate only. Actual yield depends on:
- When conditions improved/deteriorated (critical growth stages)
- Final month weather (filling period crucial)
- Starting yield potential

### Interpretation Example

```
CORN 2024 vs 2023, Week #32
National: 69% vs 55% (Δ +14)

Category Breakdown:
           2024   2023   Delta
Excellent: 15%    10%    +5
Good:      54%    45%    +9
Fair:      25%    30%    -5
Poor:      5%     12%    -7
VP:        1%     3%     -2

Interpretation:
Major improvement across all categories.
2023 was drought-stressed year.
2024 has favorable moisture/temps.
Expect yield +7-10% vs 2023 (which was
poor year, so still may not reach record).
```

## Analysis 4: State Rankings

### Methodology

**Objective**: Identify best and worst states by condition.

**Steps**:

1. **Data Acquisition**:
   - Fetch single week, all states
   - Calculate G+E% for each state

2. **Ranking**:
   ```python
   states_sorted = sort_descending(states, by='G+E%')
   rank = 1 to N
   ```

3. **Production Weighting** (optional):
   - Load production share for each state
   - Flag large producers (> 5% national production)
   - Identify risks (large producer + poor condition)

### Interpreting Rankings

**Top States**:
- Best growing conditions
- May not be largest producers
- Example: Wisconsin often tops rankings (favorable climate) but is small producer

**Bottom States**:
- Experiencing stress
- If large producer: Supply risk
- If small producer: Limited national impact

**Middle Rankings**:
- Most states cluster here
- Small differences (1-2 points) not meaningful

### Production-Weighted Analysis

**Risk Assessment**:
```
Risk Score = Production Share × (100 - G+E%)
```

Higher risk score = larger impact on national supply.

**Example**:
```
Iowa: 16% production, 71% G+E
Risk = 16 × (100-71) = 16 × 29 = 464

Mississippi: 1% production, 42% G+E
Risk = 1 × (100-42) = 1 × 58 = 58
```

Iowa's poor conditions matter much more than Mississippi's.

## Analysis 5: Season Trend Analysis

### Methodology

**Objective**: Identify patterns across entire growing season.

**Steps**:

1. **Data Acquisition**:
   - Fetch ALL weeks for year
   - National or specific state

2. **Time Series Construction**:
   ```python
   for each week:
       calculate G+E%
   ```

3. **Trend Estimation**:
   Linear regression:
   ```
   G+E% = β₀ + β₁ × Week + ε
   ```

   Where:
   - β₁ (slope) indicates trend direction
   - R² indicates trend strength

4. **Peak/Valley Detection**:
   ```python
   peak = max(G+E%)
   valley = min(G+E%)
   amplitude = peak - valley
   ```

### Typical Seasonal Patterns

**Corn & Soybeans**:
```
Weeks 18-22: High (emergence, vegetative)
Weeks 24-30: Decline (pollination stress)
Weeks 32-38: Stable or slight decline (grain fill)
Weeks 40+: Further decline (maturity)
```

**Winter Wheat**:
```
Weeks 14-18: Moderate (jointing)
Weeks 20-24: Peak or decline (heading)
Weeks 26-30: Decline (maturity)
```

### Interpretation

**Positive Slope** (β₁ > 0):
- Rare, but possible
- Indicates recovery from early stress
- Or unusually good late-season weather

**Negative Slope** (β₁ < 0):
- Most common pattern
- Natural: crops undergo stress as season progresses
- Concerning if slope is steep

**High Amplitude**:
- Volatile season
- Significant weather events
- Example: 2024 drought → recovery → heat

**Low Amplitude**:
- Stable season
- Consistently good or bad
- Easier to forecast yield

### Example

```
SOYBEANS 2024 Trend Analysis

Weeks: 18-36 (May-Sept)
Equation: G+E% = 75 - 0.6×Week
R² = 0.82

Peak: 72% (Week 18)
Valley: 64% (Week 36, current)
Amplitude: 8 points

Interpretation:
Moderate deterioration trend (-0.6 pts/week).
Started strong but gradual decline due to heat.
Still within normal range (64% > 60% threshold).
If trend continues: 60% by Week 40 (harvest).
Yield: Slightly below average expected.
```

## Analysis 6: Multi-Crop Dashboard

### Methodology

**Objective**: Compare multiple crops simultaneously.

**Steps**:

1. For each crop:
   - Current conditions (G+E%)
   - WoW delta
   - YoY delta
   - Top 3 states

2. **Cross-Crop Analysis**:
   ```python
   if all(crops_deteriorating):
       → Regional weather event
   elif some(crops_deteriorating):
       → Crop-specific issues
   ```

3. **Formatting**:
   - Tabular layout
   - Color coding (green/yellow/red)
   - Trend arrows

### Cross-Crop Insights

**Correlated Movement** (all crops similar):
- Shared weather patterns
- Example: Drought affects corn, soybeans, wheat similarly

**Divergent Movement**:
- Crop-specific factors
- Example: Corn declines (heat stress during pollination) but soybeans stable (not yet pollinating)
- Example: Disease specific to one crop

**Geographic Divergence**:
- Northern states good, Southern poor
- Indicates regional weather pattern

### Example Dashboard

```
═══════════════════════════════════════════════════
 US CROPS - Week #32, 2024
═══════════════════════════════════════════════════
Crop       G+E%   WoW    YoY    Top States
───────────────────────────────────────────────────
CORN        69    +2     +14    WI,PA,MN
SOYBEANS    64    -3     +9     WI,ND,MN
WHEAT       58    --     +5     MT,ID,WA
───────────────────────────────────────────────────

Insights:
✓ Corn improving (recent rains)
⚠ Soybeans deteriorating (Southern drought)
→ Both better than 2023 drought year
✓ Upper Midwest excellent across crops
⚠ Central Plains stress (soy > corn)
```

## Validation and Quality Checks

### Data Validation

**Sum Check**:
```python
total = Excellent + Good + Fair + Poor + Very_Poor
assert 98 <= total <= 102  # Allow 2% tolerance
```

**Outlier Detection**:
```python
if abs(value - mean) > 3 × std_dev:
    flag_as_outlier()
```

**Temporal Consistency**:
```python
if abs(current_week - previous_week) > 20:
    flag_for_review()  # 20-point jump unusual
```

### Reporting Confidence

**High Confidence**:
- Large states (IA, IL, NE)
- Mid-season data
- Consistent with weather patterns

**Lower Confidence**:
- Small states (small sample size)
- Early season (rapid changes)
- Contradicts weather data (verify)

## References

1. USDA NASS Methodology: https://www.nass.usda.gov/Surveys/Guide_to_NASS_Surveys/
2. Crop Progress Definitions: https://www.nass.usda.gov/Publications/National_Crop_Progress/Terms_and_Definitions/
3. Statistical Methods: https://www.nass.usda.gov/Education_and_Outreach/Understanding_Statistics/
