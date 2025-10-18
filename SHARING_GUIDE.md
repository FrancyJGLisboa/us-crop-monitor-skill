# Social Media Sharing Guide

## 📹 Your Demo Files

After conversion completes, you'll have:
- **Original**: `~/us-crop-demo.cast` (186 seconds)
- **Edited**: `~/us-crop-demo-edited.cast` (174 seconds, no prompt)
- **GIF**: `~/us-crop-demo.gif` (ready for social media!)

---

## 📱 Ready-to-Post Templates

### LinkedIn Post (Copy-Paste Ready)

```
🌾 Just built an AI skill for Claude Code that monitors US crop conditions in real-time!

Watch the demo below 👇

This skill enables natural language queries to access USDA NASS agricultural data instantly - perfect for commodity traders, analysts, and agricultural professionals.

Key Features:
✅ Real-time crop conditions (corn, soybeans, wheat)
✅ Harvest & planting progress tracking
✅ Yield forecasts & production estimates
✅ Automatic year detection (smart defaults)
✅ Multi-layer data validation
✅ Sub-200ms response time with intelligent caching

Perfect for:
• Commodity traders & analysts
• Agricultural researchers
• Farm managers & agronomists
• Supply chain professionals
• Anyone working with US agricultural data

Installation: One command in Claude Code
👉 /plugin marketplace add github:FrancyJGLisboa/us-crop-monitor-skill

Full documentation:
👉 https://github.com/FrancyJGLisboa/us-crop-monitor-skill

Built with Claude Code by Anthropic 🤖

What agricultural data challenges are you solving? Drop a comment below! 👇

#AI #Agriculture #ClaudeCode #DataScience #AgTech #USDA #CommodityTrading #MachineLearning #OpenSource #ArtificialIntelligence #AgricultureTechnology
```

**[Attach: us-crop-demo.gif or convert to MP4]**

---

### Twitter/X Thread

**Tweet 1:**
```
🌾 Just built an AI skill for @AnthropicAI Claude Code that monitors US crop conditions in real-time

Natural language queries → Instant USDA NASS data analysis

Watch the demo 👇

[Attach GIF]
```

**Tweet 2:**
```
Features:
✅ Crop conditions & progress
✅ Harvest tracking
✅ Yield forecasts
✅ Production estimates
✅ Auto year detection
✅ Data validation

Install in one command:
/plugin marketplace add github:FrancyJGLisboa/us-crop-monitor-skill
```

**Tweet 3:**
```
Perfect for:
📊 Commodity traders
🌾 Agricultural analysts
🚜 Farm managers
📈 Supply chain pros

Repo with full docs:
https://github.com/FrancyJGLisboa/us-crop-monitor-skill

#AI #AgTech #ClaudeCode
```

---

### Instagram Caption

```
🌾 AI-powered crop monitoring is here!

Built a skill for Claude Code that gives instant access to US agricultural data from USDA.

Just ask questions in plain English:
• "What are current corn conditions?"
• "What's the harvest progress?"
• "Show me yield forecasts"

And get real-time analysis with:
✅ Crop quality ratings
✅ Harvest progress by state
✅ Yield & production forecasts
✅ Automatic data validation

Swipe for demo screenshots →

Perfect for traders, analysts, farmers, and anyone in agriculture.

🔗 Link in bio for GitHub repo and installation

Built with Claude Code by @anthropic_ai

#AgTech #AI #Agriculture #DataScience #MachineLearning #CommodityTrading #USDA #Farming #ArtificialIntelligence #TechInnovation
```

---

### YouTube Description

```
Title: US Crop Monitor - AI Skill for Real-Time Agricultural Data Analysis

Description:
Demonstrating the US Crop Monitor skill for Claude Code - an AI-powered tool that provides instant access to USDA NASS agricultural data through natural language queries.

🌾 WHAT IT DOES:
Monitor US crop conditions, harvest progress, and yield forecasts for corn, soybeans, and wheat using simple English questions.

📊 FEATURES SHOWN:
• Real-time crop condition monitoring
• Harvest and planting progress tracking
• Yield forecasts and production estimates
• Year-over-year comparisons
• Comprehensive crop reports
• Multi-layer data validation
• Lightning-fast cached responses

⚡ INSTALLATION:
Step 1: Get free API key from https://quickstats.nass.usda.gov/api/
Step 2: Run in Claude Code:
/plugin marketplace add github:FrancyJGLisboa/us-crop-monitor-skill

🔗 LINKS:
Repository: https://github.com/FrancyJGLisboa/us-crop-monitor-skill
Documentation: Full README with examples
USDA NASS API: https://quickstats.nass.usda.gov/api/

🎯 PERFECT FOR:
• Commodity traders and market analysts
• Agricultural researchers and agronomists
• Farm managers and agricultural consultants
• Supply chain and logistics professionals
• Anyone working with US agricultural data

⚙️ TECHNICAL DETAILS:
• Language: Python with pandas, numpy, scipy
• Data Source: Official USDA NASS QuickStats API
• Caching: Intelligent multi-tier system
• Performance: <200ms for cached queries
• Validation: 4-layer data quality checks

🏗️ BUILT WITH:
• Claude Code by Anthropic
• USDA NASS QuickStats API

📅 TIMESTAMPS:
0:00 - Introduction
0:15 - Current crop conditions query
0:45 - Harvest progress tracking
1:15 - Yield forecast analysis
1:45 - Comprehensive crop report
2:30 - Year-over-year comparison
2:50 - Installation instructions

#AI #Agriculture #ClaudeCode #DataScience #AgTech #USDA #Anthropic #MachineLearning #CommodityTrading #AgriculturalTechnology

---

Questions? Drop them in the comments!

Like and subscribe for more AI + Agriculture content 🌾🤖
```

---

## 🎨 Post-Processing Tips

### If GIF is Too Large for LinkedIn/Twitter

**Optimize GIF:**
```bash
# Install gifsicle
brew install gifsicle

# Optimize (reduce file size)
gifsicle -O3 --colors 256 ~/us-crop-demo.gif -o ~/us-crop-demo-optimized.gif

# Or reduce frame rate
gifsicle --delay=10 ~/us-crop-demo.gif -o ~/us-crop-demo-slower.gif
```

### Convert GIF to MP4 (Better for LinkedIn)

```bash
# Install ffmpeg if needed
brew install ffmpeg

# Convert to MP4
ffmpeg -i ~/us-crop-demo.gif -movflags faststart -pix_fmt yuv420p -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" ~/us-crop-demo.mp4

# Result: Smaller file size, better quality, LinkedIn/YouTube friendly
```

---

## 📏 Platform Specifications

### LinkedIn
- **Format**: MP4 (preferred) or GIF
- **Max size**: 200MB (MP4), 5MB (GIF)
- **Optimal duration**: 30 seconds - 3 minutes
- **Resolution**: 1920x1080 or 1280x720

### Twitter/X
- **Format**: MP4 or GIF
- **Max size**: 512MB (MP4), 5MB (GIF)
- **Optimal duration**: 30-60 seconds
- **Resolution**: 1280x720 recommended

### Instagram
- **Format**: MP4
- **Ratio**: 1:1 (square) or 4:5 (portrait)
- **Duration**: 3-60 seconds (feed), up to 15 min (reels)

### YouTube
- **Format**: MP4
- **Resolution**: 1920x1080 (HD)
- **Duration**: Any (3-5 min recommended for demos)

---

## ✅ Pre-Post Checklist

- [ ] GIF conversion completed
- [ ] File size checked (< 5MB for GIF, < 200MB for MP4)
- [ ] Preview looks good (prompt removed)
- [ ] Post template copied and customized
- [ ] Links tested (GitHub repo, installation command)
- [ ] Hashtags appropriate for platform
- [ ] Tagged relevant accounts (@AnthropicAI on Twitter)

---

## 🎯 Engagement Tips

**Do:**
- ✅ Post during peak hours (9-11am, 1-3pm local time)
- ✅ Ask a question to encourage comments
- ✅ Respond to comments quickly
- ✅ Share in relevant groups (AgTech, AI/ML, Data Science)
- ✅ Cross-post across platforms (LinkedIn, Twitter, etc.)

**Don't:**
- ❌ Post without context (explain what people are seeing)
- ❌ Use too many hashtags (LinkedIn: 3-5, Twitter: 2-3)
- ❌ Forget to include installation instructions
- ❌ Make video too long (attention spans are short!)

---

## 📊 Expected Reach

**LinkedIn** (professional network):
- Target: Agricultural professionals, data scientists, traders
- Typical reach: 500-2000 views (with good hashtags)
- Engagement: 2-5% (likes, comments, shares)

**Twitter/X** (tech community):
- Target: AI enthusiasts, developers, AgTech community
- Typical reach: 200-1000 views (depends on followers)
- Engagement: 1-3%

**GitHub** (developers):
- Stars: 10-50 (if shared well)
- Forks: 2-10
- Issues/PRs: Organic growth

---

**Good luck with your social media launch! 🚀🌾**
