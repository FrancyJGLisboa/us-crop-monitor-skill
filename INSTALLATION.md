# Installation Guide - US Crop Monitor Skill

## Quick Installation (3 minutes)

### Step 1: Configure API Key (one-time only)
```bash
export NASS_API_KEY="5D441C94-9939-32CA-951F-726FC3EEF69A"
echo 'export NASS_API_KEY="5D441C94-9939-32CA-951F-726FC3EEF69A"' >> ~/.zshrc
source ~/.zshrc
```

### Step 2: Install the Skill in Claude Code

#### Option A: Install from GitHub (Recommended)
```bash
# Clone the repository
git clone https://github.com/FrancyJGLisboa/us-crop-monitor-skill.git

# Navigate to Claude Code skills directory (or your preferred location)
cd /path/to/your/skills/directory
mv /path/to/us-crop-monitor-skill ./us-crop-monitor

# Install in Claude Code
/plugin marketplace add ./us-crop-monitor
```

#### Option B: Install from local directory
```bash
# If you already have the skill directory
/plugin marketplace add /path/to/us-crop-monitor
```

**Expected output**: `Successfully added marketplace: us-crop-monitor`

### Step 3: Test
Ask Claude:
```
"How is corn in the US today?"
```

✅ If it responds with USDA data → Installation successful!

---

## Detailed Installation

### Prerequisites

1. **Python 3.8+** with required packages:
   ```bash
   pip install requests pandas numpy scipy
   ```

2. **NASS API Key** (free, instant):
   - Visit: https://quickstats.nass.usda.gov/api/
   - Click "Request API Key"
   - Fill form (takes 30 seconds)
   - Key sent to email instantly
   - Key is permanent (doesn't expire)

### Installation Steps

#### 1. Get the Skill

**From GitHub:**
```bash
git clone https://github.com/FrancyJGLisboa/us-crop-monitor-skill.git
cd us-crop-monitor-skill
```

**From ZIP:**
```bash
unzip us-crop-monitor.zip
cd us-crop-monitor
```

#### 2. Configure API Key

**For macOS/Linux (zsh):**
```bash
# Add to ~/.zshrc
echo 'export NASS_API_KEY="YOUR_KEY_HERE"' >> ~/.zshrc

# Reload
source ~/.zshrc

# Verify
echo $NASS_API_KEY
# Should display your key
```

**For macOS/Linux (bash):**
```bash
# Add to ~/.bashrc
echo 'export NASS_API_KEY="YOUR_KEY_HERE"' >> ~/.bashrc

# Reload
source ~/.bashrc

# Verify
echo $NASS_API_KEY
```

**For Windows:**
```powershell
# Set environment variable (PowerShell)
[System.Environment]::SetEnvironmentVariable('NASS_API_KEY','YOUR_KEY_HERE','User')

# Verify
$env:NASS_API_KEY
```

#### 3. Install Skill in Claude Code

```bash
# Navigate to the skill directory
cd /path/to/us-crop-monitor

# Install
/plugin marketplace add $(pwd)
```

Or specify full path:
```bash
/plugin marketplace add /full/path/to/us-crop-monitor
```

#### 4. Verify Installation

**Check if installed:**
```bash
/plugin list
```

**Expected output:**
```
Installed plugins:
• us-crop-monitor (v2.0.0) - Comprehensive USDA NASS crop monitoring
```

**Test the skill:**
Ask Claude any of these questions:
- "What are current corn conditions?"
- "What's the corn harvest progress?"
- "What's the corn yield estimate?"
- "Give me a complete corn report"

---

## Updating the Skill

### Method 1: Update in Place (if installed as symlink)

```bash
cd /path/to/us-crop-monitor

# Pull latest changes
git pull origin main

# Optional: Restart Claude Code
# The skill will automatically use the new version
```

### Method 2: Reinstall

```bash
# Remove old version
/plugin marketplace remove us-crop-monitor

# Get new version
cd /path/to/us-crop-monitor
git pull origin main

# Reinstall
/plugin marketplace add $(pwd)
```

### Method 3: Clear Cache (if data seems outdated)

```bash
# Clear skill cache
rm -rf /path/to/us-crop-monitor/data/cache/*

# The skill will rebuild cache with fresh data
```

---

## Verification

### Check Installation

```bash
# Verify skills list
/plugin list

# Verify API key
echo $NASS_API_KEY

# Verify Python dependencies
python -c "import requests, pandas, numpy, scipy; print('✓ All dependencies installed')"
```

### Test Queries

Try each type of query to ensure all features work:

**1. Condition Query:**
```
"What are corn conditions in the US?"
```

**2. Progress Query:**
```
"What's the corn harvest progress?"
```

**3. Yield Query:**
```
"What's the corn yield estimate?"
```

**4. Comprehensive Report:**
```
"Give me a complete corn report"
```

---

## Troubleshooting

### Problem: "API key is required"

**Solution:**
```bash
# Check if set
echo $NASS_API_KEY

# If empty, configure again
export NASS_API_KEY="5D441C94-9939-32CA-951F-726FC3EEF69A"
echo 'export NASS_API_KEY="5D441C94-9939-32CA-951F-726FC3EEF69A"' >> ~/.zshrc
source ~/.zshrc
```

### Problem: "Skill doesn't appear in /plugin list"

**Possible causes:**
1. Incorrect path
2. Missing `.claude-plugin/marketplace.json` file

**Solution:**
```bash
# Verify marketplace.json exists
ls -la /path/to/us-crop-monitor/.claude-plugin/marketplace.json

# If missing, reinstall from GitHub
git clone https://github.com/FrancyJGLisboa/us-crop-monitor-skill.git
/plugin marketplace add ./us-crop-monitor-skill
```

### Problem: "Skill doesn't activate automatically"

**Cause:** Query doesn't contain keywords

**Solution:**
- Include crop name explicitly: "corn", "soybeans", or "wheat"
- Include action: "conditions", "progress", "yield", etc.
- Example that works: "corn conditions" (not just "crop data")

### Problem: Missing Python dependencies

**Solution:**
```bash
# Install all dependencies
pip install requests pandas numpy scipy

# Or with virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install requests pandas numpy scipy
```

### Problem: Slow performance

**Cause:** Empty cache

**Solution:**
- First request is always slower (2-5s) - this is normal
- Subsequent requests will be fast (<200ms)
- Cache builds automatically on first use

---

## For Developers

### Running Tests

```bash
cd /path/to/us-crop-monitor

# Run validation tests
python test_validation.py

# Run specific test modules
python -m pytest tests/test_temporal_validator.py
python -m pytest tests/test_completeness_validator.py

# Run demo
python demo_validation_system.py
```

### Running Scripts Directly

```bash
# Example daily report
python example_daily_report.py

# Manual data fetch
python scripts/fetch_nass.py --commodity CORN --year 2025

# Test specific analysis
python -c "from scripts.analyze_crops import current_condition_report; print(current_condition_report('CORN'))"
```

---

## Uninstallation

### Remove Skill

```bash
# Remove from Claude Code
/plugin marketplace remove us-crop-monitor

# Optional: Remove files
rm -rf /path/to/us-crop-monitor

# Optional: Remove API key from config
# Edit ~/.zshrc and remove the NASS_API_KEY line
```

---

## Additional Resources

- **README.md**: Complete feature overview
- **SKILL.md**: Detailed skill documentation (for Claude)
- **docs/VALIDATION_SYSTEM.md**: Data validation system documentation
- **DECISIONS.md**: Architecture and design decisions

---

## Getting Help

1. **Check Documentation**: See README.md and SKILL.md
2. **Check Logs**: Look in `data/logs/` for error messages
3. **USDA NASS API**: https://quickstats.nass.usda.gov/api/
4. **GitHub Issues**: https://github.com/FrancyJGLisboa/us-crop-monitor-skill/issues

---

**Installation complete! Start monitoring US crops with natural language queries.** 🌾
