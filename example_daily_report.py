#!/usr/bin/env python3
"""
Example: Daily Executive Crop Report

Shows how to use the skill for real-world daily monitoring.
Generates a comprehensive report for commodity traders, analysts, etc.
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from analyze_crops import (
    current_condition_report,
    harvest_progress_report,
    yield_analysis,
    comprehensive_crop_report
)


def generate_daily_report(commodity='CORN'):
    """Generate daily executive report for a crop."""
    
    print("\n" + "╔" + "=" * 78 + "╗")
    print(f"║{f'DAILY CROP REPORT - {commodity}':^78}║")
    print(f"║{f'{datetime.now().strftime('%B %d, %Y')}':^78}║")
    print("╚" + "=" * 78 + "╝")

    # Get comprehensive report (all metrics)
    print("\nℹ️  Fetching data from USDA NASS...")
    report = comprehensive_crop_report(commodity)

    print("\n" + "=" * 80)
    print(" 📋 EXECUTIVE SUMMARY")
    print("=" * 80)

    # Condition
    if 'condition' in report['metrics']:
        cond = report['metrics']['condition']
        if 'error' not in cond:
            print(f"\n🌾 CROP QUALITY (Week {cond['week']}, {report['year']})")
            print(f"   Good+Excellent: {cond['good_excellent']:.1f}%")
            
            # Interpretation
            ge = cond['good_excellent']
            if ge >= 70:
                status = "EXCELLENT ✅"
            elif ge >= 60:
                status = "GOOD ✓"
            elif ge >= 50:
                status = "FAIR ⚠"
            else:
                status = "POOR ❌"
            print(f"   Status: {status}")

            if cond['top_states']:
                top = cond['top_states'][0]
                print(f"   Best state: {top['state_name']} ({top['good_excellent']:.1f}%)")

    # Harvest Progress
    if 'harvest_progress' in report['metrics']:
        prog = report['metrics']['harvest_progress']
        if 'error' not in prog:
            print(f"\n🚜 HARVEST PROGRESS (Week {prog['week']}, {report['year']})")
            pct = prog['percent_harvested']
            print(f"   Completed: {pct:.1f}%")
            
            # Progress interpretation
            if pct < 25:
                stage = "EARLY STAGE"
            elif pct < 50:
                stage = "ADVANCING"
            elif pct < 75:
                stage = "ADVANCED"
            else:
                stage = "NEAR COMPLETE"
            print(f"   Stage: {stage}")

            if prog.get('top_states'):
                top = prog['top_states'][0]
                print(f"   Most advanced: {top['state_name']} ({top['Value']:.0f}%)")

    # Planting Progress
    if 'planting_progress' in report['metrics']:
        prog = report['metrics']['planting_progress']
        if 'error' not in prog:
            print(f"\n🌱 PLANTING PROGRESS (Week {prog['week']}, {report['year']})")
            pct = prog['percent_planted']
            print(f"   Completed: {pct:.1f}%")
            
            if pct >= 95:
                print(f"   Status: PLANTING COMPLETE ✅")
            elif pct >= 75:
                print(f"   Status: WELL ADVANCED ✓")
            else:
                print(f"   Status: IN PROGRESS ⏳")

    # Yield
    if 'yield' in report['metrics']:
        yld = report['metrics']['yield']
        if 'error' not in yld:
            y_val = yld.get('yield_bu_per_acre', 0)
            if y_val > 0:
                print(f"\n📊 YIELD FORECAST ({report['year']})")
                print(f"   Estimate: {y_val:.1f} bushels/acre")
                
                # Historical context
                if y_val > 180:
                    print(f"   Outlook: ABOVE AVERAGE ✅")
                elif y_val > 170:
                    print(f"   Outlook: AVERAGE ✓")
                else:
                    print(f"   Outlook: BELOW AVERAGE ⚠")

    # Production
    if 'production' in report['metrics']:
        prod = report['metrics']['production']
        if 'error' not in prod:
            p_val = prod.get('production_bu', 0)
            if p_val > 0:
                print(f"\n🏭 PRODUCTION FORECAST ({report['year']})")
                print(f"   Total: {p_val/1e9:.2f} billion bushels")

    print("\n" + "=" * 80)
    print(" 💡 KEY INSIGHTS")
    print("=" * 80)

    # Generate insights based on data
    insights = []

    # Condition insights
    if 'condition' in report['metrics']:
        cond = report['metrics']['condition']
        if 'error' not in cond:
            ge = cond['good_excellent']
            if ge >= 70:
                insights.append(f"✓ Crop quality is excellent ({ge:.1f}% G+E)")
            elif ge < 55:
                insights.append(f"⚠ Crop quality below average ({ge:.1f}% G+E) - monitor closely")

    # Harvest insights
    if 'harvest_progress' in report['metrics']:
        prog = report['metrics']['harvest_progress']
        if 'error' not in prog:
            pct = prog['percent_harvested']
            if pct < 10:
                insights.append(f"ℹ️  Harvest just beginning ({pct:.1f}% complete)")
            elif pct > 90:
                insights.append(f"✓ Harvest nearly complete ({pct:.1f}%)")

    # Yield insights
    if 'yield' in report['metrics']:
        yld = report['metrics']['yield']
        if 'error' not in yld:
            y_val = yld.get('yield_bu_per_acre', 0)
            if y_val > 185:
                insights.append(f"✓ Yield forecast strong: {y_val:.1f} bu/acre")

    # Display insights
    if insights:
        for insight in insights:
            print(f"\n   {insight}")
    else:
        print("\n   Data still being collected for current season")

    print("\n" + "=" * 80)
    print(f" 📅 Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" 🔄 Data auto-updated from USDA NASS (with intelligent caching)")
    print("=" * 80 + "\n")


def main():
    """Generate daily reports for all major crops."""
    
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "DAILY CROP MONITORING - EXECUTIVE BRIEF" + " " * 18 + "║")
    print("╚" + "=" * 78 + "╝")

    crops = ['CORN', 'SOYBEANS', 'WHEAT']

    for crop in crops:
        try:
            generate_daily_report(crop)
        except Exception as e:
            print(f"\n❌ Error generating {crop} report: {e}\n")

    print("\n" + "=" * 80)
    print(" ✅ DAILY BRIEF COMPLETE")
    print("=" * 80)
    print("\n💡 TIP: Run this script daily at 9am for automated crop monitoring")
    print("   Example cron: 0 9 * * 1-5 /path/to/example_daily_report.py\n")


if __name__ == "__main__":
    main()
