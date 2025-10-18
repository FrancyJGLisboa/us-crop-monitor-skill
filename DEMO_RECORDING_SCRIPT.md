# Demo Recording Script for Social Media

## 🎬 Terminal Setup (Do This First!)

### 1. Prepare Your Terminal
```bash
# Increase font size for readability
# Go to Terminal → Preferences → Profiles → Text
# Set font size to 18-22pt

# Use a high-contrast theme:
# - Solarized Dark
# - Dracula
# - One Dark Pro

# Set window size
# Resize terminal to approximately 120 columns x 30 rows
```

### 2. Install Recording Tool

**Option A: asciinema (Recommended for web sharing)**
```bash
brew install asciinema

# Test it
asciinema rec test.cast
# Type something, then Ctrl+D to stop
```

**Option B: terminalizer (For GIF creation)**
```bash
npm install -g terminalizer

# Test it
terminalizer record test
# Type something, then Ctrl+D to stop
# Render: terminalizer render test -o test.gif
```

**Option C: Screen Recording (For LinkedIn/YouTube)**
- macOS: Press Cmd+Shift+5
- Select "Record Selected Portion"
- Frame just the terminal window

---

## 🎭 Recording Script (3-4 minutes)

### Scene 1: Introduction (30 seconds)

```bash
# Clear the screen
clear

# Type this (slowly, let viewers read):
echo "🌾 US Crop Monitor - AI-powered USDA crop data analysis"
echo ""
echo "Demonstrating real-time agricultural monitoring with Claude Code..."
echo ""
echo "Repository: github.com/FrancyJGLisboa/us-crop-monitor-skill"
echo ""

# Pause 3 seconds
sleep 3
```

### Scene 2: Simple Condition Query (45 seconds)

**Start Claude Code session, then ask:**

```
What are current corn conditions in the US?
```

**Expected Response:**
- Auto-detected year (2025)
- Condition breakdown (Excellent, Good, Fair, Poor, Very Poor)
- Good+Excellent percentage
- Top states by condition
- Validation icons (✅)

**Pause 5 seconds** - Let viewers read the response

---

### Scene 3: Harvest Progress (45 seconds)

**Ask:**

```
What's the corn harvest progress?
```

**Expected Response:**
- Week number and year
- National % harvested
- Major Corn Belt states progress
- Year-over-year comparison
- Harvest stage indicator

**Pause 5 seconds**

---

### Scene 4: Yield Forecast (45 seconds)

**Ask:**

```
What's the corn yield estimate for 2025?
```

**Expected Response:**
- National yield in bushels/acre
- Comparison with 2024
- Interpretation (above/below average)
- Status indicator

**Pause 5 seconds**

---

### Scene 5: Comprehensive Report (90 seconds)

**Ask:**

```
Give me a complete corn report with all metrics
```

**Expected Response:**
- 🌾 Crop Quality section
- 🚜 Harvest Progress section
- 🌱 Planting Progress section
- 📊 Yield Forecast section
- 🏭 Production Forecast section
- 🗺️ Area section
- Key insights summary

**Pause 8 seconds** - This is the highlight, let viewers absorb

---

### Scene 6: Year-over-Year Comparison (60 seconds)

**Ask:**

```
Compare corn conditions 2025 vs 2024
```

**Expected Response:**
- Side-by-side comparison
- Delta calculations
- State-by-state improvements/declines
- Context and interpretation

**Pause 5 seconds**

---

### Scene 7: Outro (30 seconds)

```bash
# Show installation instructions
clear
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🌾 US Crop Monitor - Easy Installation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Step 1: Get free API key"
echo "  → https://quickstats.nass.usda.gov/api/"
echo ""
echo "Step 2: Install in Claude Code"
echo "  → /plugin marketplace add github:FrancyJGLisboa/us-crop-monitor-skill"
echo ""
echo "Repository:"
echo "  → https://github.com/FrancyJGLisboa/us-crop-monitor-skill"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Pause 5 seconds
sleep 5
```

---

## 🎥 Recording Commands

### Start Recording

**With asciinema:**
```bash
asciinema rec us-crop-monitor-demo.cast
```

**With terminalizer:**
```bash
terminalizer record us-crop-demo
```

**With screen recording:**
- Press Cmd+Shift+5
- Select area
- Click Record

### Execute the Script Above

Follow Scenes 1-7 in order.

**Tips:**
- Type at normal reading speed (not too fast!)
- Pause after each Claude response
- Don't worry about typos - they make it authentic
- If you make a mistake, just keep going or start over

### Stop Recording

**asciinema:**
- Press `Ctrl+D`

**terminalizer:**
- Press `Ctrl+D`

**Screen recording:**
- Click Stop button in menu bar

---

## 🎬 Post-Processing

### Convert asciinema to MP4 (for LinkedIn/Twitter)

**Option 1: Use asciinema player**
```bash
# Upload to asciinema.org
asciinema upload us-crop-monitor-demo.cast

# Share the link, or...
```

**Option 2: Convert to GIF**
```bash
# Install asciicast2gif
npm install -g asciicast2gif

# Convert
asciicast2gif us-crop-monitor-demo.cast us-crop-demo.gif
```

**Option 3: Convert to MP4 with svg-term**
```bash
# Install svg-term-cli
npm install -g svg-term-cli

# Convert
cat us-crop-monitor-demo.cast | svg-term --out us-crop-demo.svg
# Then use browser to save as video, or use ffmpeg
```

### Render terminalizer GIF

```bash
terminalizer render us-crop-demo -o us-crop-monitor.gif
```

### Optimize Video for Social Media

**For LinkedIn (recommended specs):**
- Format: MP4 (H.264)
- Resolution: 1920x1080 or 1280x720
- Duration: 2-3 minutes (optimal engagement)
- File size: < 200MB

**For Twitter/X:**
- Format: MP4
- Duration: 30-60 seconds (shorter is better)
- File size: < 512MB

---

## 📱 Ready-to-Use Social Media Posts

### LinkedIn Post

```
🌾 Just built an AI skill for Claude Code that monitors US crop conditions in real-time!

Watch the demo below 👇

This skill enables natural language queries to access USDA NASS agricultural data instantly.

Key Features:
✅ Real-time crop conditions (corn, soybeans, wheat)
✅ Harvest & planting progress tracking
✅ Yield forecasts & production estimates
✅ Automatic year detection (smart defaults)
✅ Multi-layer data validation
✅ Sub-200ms response time with caching

Perfect for:
• Commodity traders & analysts
• Agricultural researchers
• Farm managers
• Supply chain professionals

Installation: One command in Claude Code
👉 /plugin marketplace add github:FrancyJGLisboa/us-crop-monitor-skill

Repository: https://github.com/FrancyJGLisboa/us-crop-monitor-skill

Built with Claude Code by Anthropic.

#AI #Agriculture #ClaudeCode #DataScience #AgTech #USDA #CommodityTrading #MachineLearning #OpenSource

[Attach video here]
```

### Twitter/X Post

**Option 1 (Thread):**
```
Tweet 1:
🌾 Built an AI skill for @AnthropicAI Claude Code to monitor US crop conditions

Natural language → Real USDA data in seconds

Demo 👇

[Attach short video/GIF]

Tweet 2:
Features:
✅ Crop conditions & progress
✅ Yield forecasts
✅ Multi-crop analysis
✅ Auto year detection

Install in 1 command:
/plugin marketplace add github:FrancyJGLisboa/us-crop-monitor-skill

Tweet 3:
Repository with full docs:
github.com/FrancyJGLisboa/us-crop-monitor-skill

Perfect for traders, analysts, researchers 📊

#AI #AgTech #ClaudeCode
```

**Option 2 (Single tweet):**
```
🌾 AI-powered US crop monitoring in Claude Code

Ask questions in plain English → Get instant USDA data analysis

Demo + Install:
github.com/FrancyJGLisboa/us-crop-monitor-skill

@AnthropicAI #AI #AgTech

[Attach GIF]
```

### YouTube Description

```
Title: US Crop Monitor - AI-Powered Agricultural Data Analysis in Claude Code

Description:
Demonstrating the US Crop Monitor skill for Claude Code - an AI-powered tool that provides instant access to USDA NASS agricultural data through natural language queries.

🌾 Features:
• Real-time crop condition monitoring (corn, soybeans, wheat)
• Harvest and planting progress tracking
• Yield forecasts and production estimates
• Area data (planted/harvested acres)
• Automatic year detection with smart fallbacks
• Multi-layer data validation system
• Lightning-fast responses (<200ms with caching)

📦 Installation:
One command in Claude Code:
/plugin marketplace add github:FrancyJGLisboa/us-crop-monitor-skill

🔗 Links:
Repository: https://github.com/FrancyJGLisboa/us-crop-monitor-skill
Documentation: Full README and installation guide in repo
USDA NASS API: https://quickstats.nass.usda.gov/api/

🎯 Perfect for:
• Commodity traders and analysts
• Agricultural researchers
• Farm managers and agronomists
• Supply chain professionals
• Anyone working with US agricultural data

⚡ Powered by:
Claude Code by Anthropic
USDA NASS QuickStats API

#AI #Agriculture #ClaudeCode #DataScience #AgTech #USDA #Anthropic

Timestamps:
0:00 - Introduction
0:30 - Current conditions query
1:15 - Harvest progress tracking
2:00 - Yield forecast
2:45 - Comprehensive report
4:00 - Year-over-year comparison
5:00 - Installation instructions
```

---

## ✅ Pre-Recording Checklist

- [ ] Terminal font size increased (18-22pt)
- [ ] High-contrast theme selected
- [ ] Window sized appropriately (~120x30)
- [ ] Recording tool installed and tested
- [ ] Claude Code is running
- [ ] us-crop-monitor skill is installed
- [ ] NASS_API_KEY is configured
- [ ] Script reviewed and practiced once
- [ ] Screen is clean (close unnecessary windows)
- [ ] Notifications disabled (Do Not Disturb mode)

## 🎯 Recording Day Tips

1. **Practice first** - Do a dry run without recording
2. **Speak naturally** - If adding voiceover, be conversational
3. **Show enthusiasm** - This is cool technology!
4. **Don't rush** - Pause after responses
5. **Be authentic** - Small typos are okay, shows it's real
6. **Have fun** - Your excitement will come through

---

**Good luck with your recording! 🎬🌾**
