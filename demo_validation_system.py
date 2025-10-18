#!/usr/bin/env python3
"""
Demonstration of ALL US Crop Monitor Capabilities

Shows all 11 analysis functions with real data.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from analyze_crops import (
    current_condition_report,
    week_over_week_comparison,
    year_over_year_comparison,
    state_rankings,
    season_trend_analysis,
    harvest_progress_report,
    planting_progress_report,
    yield_analysis,
    production_analysis,
    area_analysis,
    comprehensive_crop_report
)


def demo_condition_analysis():
    """Demo crop condition analysis."""
    print("\n" + "=" * 80)
    print(" 📊 CROP CONDITION ANALYSIS")
    print("=" * 80)

    print("\n🌽 Current Corn Conditions (auto-detected year):")
    result = current_condition_report('CORN')
    print(f"   Year: {result['year']} | Week: {result['week']}")
    print(f"   {result['year_info']}")
    print(f"\n   NATIONAL CONDITIONS:")
    cond = result['conditions']
    print(f"     • Excellent: {cond.get('EXCELLENT', 0):.1f}%")
    print(f"     • Good: {cond.get('GOOD', 0):.1f}%")
    print(f"     • Fair: {cond.get('FAIR', 0):.1f}%")
    print(f"     • Poor: {cond.get('POOR', 0):.1f}%")
    print(f"     • Very Poor: {cond.get('VERY POOR', 0):.1f}%")
    print(f"     ───────────────────────")
    print(f"     → Good+Excellent: {cond.get('good_excellent', 0):.1f}%")

    print(f"\n   TOP 3 STATES:")
    for i, state in enumerate(result.get('top_states', [])[:3], 1):
        print(f"     {i}. {state['state_name']}: {state['good_excellent']:.1f}%")


def demo_comparisons():
    """Demo comparison analyses."""
    print("\n" + "=" * 80)
    print(" 📈 COMPARISONS & TRENDS")
    print("=" * 80)

    # Week-over-Week
    print("\n📅 Week-over-Week Change (CORN):")
    result = week_over_week_comparison('CORN')
    print(f"   Week {result['current_week']} vs Week {result['previous_week']} ({result['year']})")
    delta = result['national']['delta']
    symbol = "▲" if delta > 0 else "▼"
    print(f"   National: {symbol} {abs(delta):.1f} points")

    if result['top_deteriorations']:
        print(f"\n   WORST CHANGES:")
        for state in result['top_deteriorations'][:3]:
            print(f"     • {state['state_name']}: {state['delta']:+.1f} pts")

    # Year-over-Year
    print("\n📊 Year-over-Year Comparison (CORN 2025 vs 2024):")
    result = year_over_year_comparison('CORN', 2025, 2024)
    delta = result['national_delta']['good_excellent']
    symbol = "▲" if delta > 0 else "▼"
    print(f"   {symbol} {abs(delta):.1f} points difference")
    print(f"   2025: {result['national_current']['good_excellent']:.1f}% G+E")
    print(f"   2024: {result['national_previous']['good_excellent']:.1f}% G+E")

    # State Rankings
    print("\n🏆 State Rankings (CORN):")
    result = state_rankings('CORN')
    print(f"   Top 5 States (Week {result['week']}, {result['year']}):")
    for state in result['top_10'][:5]:
        print(f"     #{state['rank']}. {state['state_name']}: {state['good_excellent']:.1f}%")

    # Season Trend
    print("\n📉 Season Trend Analysis (CORN 2025):")
    result = season_trend_analysis('CORN')
    print(f"   Weeks analyzed: {len(result['weeks_available'])}")
    print(f"   Trend: {result['trend_direction']}")
    print(f"   Peak: Week {result['peak']['week']} ({result['peak']['good_excellent']:.1f}%)")
    print(f"   Valley: Week {result['valley']['week']} ({result['valley']['good_excellent']:.1f}%)")
    print(f"   Current: Week {result['current']['week']} ({result['current']['good_excellent']:.1f}%)")


def demo_progress_analysis():
    """Demo progress analysis."""
    print("\n" + "=" * 80)
    print(" 🚜 PLANTING & HARVEST PROGRESS")
    print("=" * 80)

    # Harvest Progress
    print("\n🌾 Harvest Progress (CORN 2025):")
    result = harvest_progress_report('CORN')
    print(f"   Week {result['week']}: {result.get('percent_harvested', 0):.1f}% harvested")
    print(f"   {result['year_info']}")

    if result.get('top_states'):
        print(f"\n   MOST ADVANCED STATES:")
        for state in result['top_states'][:5]:
            print(f"     • {state['state_name']}: {state['Value']:.0f}%")

    # Planting Progress
    print("\n🌱 Planting Progress (CORN 2025):")
    result = planting_progress_report('CORN')
    print(f"   Week {result['week']}: {result.get('percent_planted', 0):.1f}% planted")

    if result.get('top_states'):
        print(f"\n   MOST ADVANCED STATES:")
        for state in result['top_states'][:5]:
            print(f"     • {state['state_name']}: {state['Value']:.0f}%")


def demo_yield_production():
    """Demo yield and production analysis."""
    print("\n" + "=" * 80)
    print(" 🌾 YIELD & PRODUCTION ESTIMATES")
    print("=" * 80)

    # Yield
    print("\n📊 Yield Analysis (CORN 2025):")
    result = yield_analysis('CORN')
    print(f"   National Yield: {result.get('yield_bu_per_acre', 0):.1f} bushels/acre")
    print(f"   {result['year_info']}")

    if result.get('comparison'):
        print(f"   Year-over-year comparison available ✓")

    # Production
    print("\n🏭 Production Estimates (CORN 2025):")
    result = production_analysis('CORN')
    prod = result.get('production_bu', 0)
    if prod > 0:
        print(f"   National Production: {prod/1e9:.2f} billion bushels")
    else:
        print(f"   Production data not yet available for 2025")

    # Area
    print("\n🗺️  Area Analysis (CORN 2025):")
    result = area_analysis('CORN', area_type='PLANTED')
    acres = result.get('acres', 0)
    if acres > 0:
        print(f"   Acres Planted: {acres/1e6:.2f} million acres")
    else:
        print(f"   Area data not yet finalized for 2025")


def demo_comprehensive_report():
    """Demo comprehensive multi-metric report."""
    print("\n" + "=" * 80)
    print(" 📋 COMPREHENSIVE CROP REPORT")
    print("=" * 80)

    print("\n🌽 Complete CORN Report (all metrics):")
    result = comprehensive_crop_report('CORN')

    print(f"\n   Year: {result['year']}")
    print(f"   Generated: {result['generated_at']}")
    print(f"\n   METRICS AVAILABLE:")

    metrics = result['metrics']

    # Condition
    if 'condition' in metrics and 'error' not in metrics['condition']:
        cond = metrics['condition']
        print(f"     ✓ Condition: {cond['good_excellent']:.1f}% G+E (Week {cond['week']})")

    # Progress
    if 'harvest_progress' in metrics and 'error' not in metrics['harvest_progress']:
        prog = metrics['harvest_progress']
        print(f"     ✓ Harvest: {prog['percent_harvested']:.1f}% (Week {prog['week']})")

    if 'planting_progress' in metrics and 'error' not in metrics['planting_progress']:
        prog = metrics['planting_progress']
        print(f"     ✓ Planting: {prog['percent_planted']:.1f}% (Week {prog['week']})")

    # Yield
    if 'yield' in metrics and 'error' not in metrics['yield']:
        yield_val = metrics['yield']['yield_bu_per_acre']
        if yield_val and yield_val > 0:
            print(f"     ✓ Yield: {yield_val:.1f} bu/acre")

    # Production
    if 'production' in metrics and 'error' not in metrics['production']:
        prod = metrics['production']['production_bu']
        if prod and prod > 0:
            print(f"     ✓ Production: {prod/1e9:.2f}B bu")

    # Area
    if 'area_planted' in metrics and 'error' not in metrics['area_planted']:
        acres = metrics['area_planted']['acres']
        if acres and acres > 0:
            print(f"     ✓ Area Planted: {acres/1e6:.2f}M acres")


def main():
    """Run full demonstration."""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "US CROP MONITOR - FULL CAPABILITIES DEMO" + " " * 22 + "║")
    print("╚" + "=" * 78 + "╝")

    print("\n✨ This demo shows ALL analysis functions with REAL USDA NASS data")
    print("   All queries use AUTO-DETECTED year (2025) with smart fallback\n")

    try:
        demo_condition_analysis()
        demo_comparisons()
        demo_progress_analysis()
        demo_yield_production()
        demo_comprehensive_report()

        print("\n" + "=" * 80)
        print(" ✅ DEMONSTRATION COMPLETE")
        print("=" * 80)

        print("\n📝 SUMMARY:")
        print("   • 11 analysis functions available")
        print("   • Auto-year detection for all functions")
        print("   • Covers: Condition, Progress, Yield, Production, Area")
        print("   • Smart fallback to previous year when needed")
        print("   • Comprehensive validation system (v2.0)")
        print("\n   Ready for production use! 🚀")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
