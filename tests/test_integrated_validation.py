#!/usr/bin/env python3
"""
Comprehensive integration test for all analysis functions.

Tests all 8 analysis functions with real NASS data.
"""

import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

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


def test_condition_functions():
    """Test the 5 original condition-based functions."""
    print("\n" + "=" * 70)
    print("TESTING CONDITION FUNCTIONS")
    print("=" * 70)

    results = []

    # 1. Current Conditions
    print("\n1. current_condition_report()...")
    try:
        result = current_condition_report('CORN')
        print(f"   ✓ Year: {result['year']} | Week: {result['week']}")
        print(f"   ✓ Good+Excellent: {result['conditions'].get('good_excellent', 0):.1f}%")
        results.append(True)
    except Exception as e:
        print(f"   ✗ {e}")
        results.append(False)

    # 2. Week-over-Week
    print("\n2. week_over_week_comparison()...")
    try:
        result = week_over_week_comparison('CORN')
        print(f"   ✓ Year: {result['year']} | Weeks: {result['current_week']} vs {result['previous_week']}")
        print(f"   ✓ Delta: {result['national']['delta']:+.1f} pts")
        results.append(True)
    except Exception as e:
        print(f"   ✗ {e}")
        results.append(False)

    # 3. Year-over-Year
    print("\n3. year_over_year_comparison()...")
    try:
        result = year_over_year_comparison('CORN', 2025, 2024)
        print(f"   ✓ Years: {result['current_year']} vs {result['previous_year']}")
        print(f"   ✓ Delta: {result['national_delta']['good_excellent']:+.1f} pts")
        results.append(True)
    except Exception as e:
        print(f"   ✗ {e}")
        results.append(False)

    # 4. State Rankings
    print("\n4. state_rankings()...")
    try:
        result = state_rankings('CORN')
        print(f"   ✓ Year: {result['year']} | States: {len(result['rankings'])}")
        top = result['top_10'][0] if result['top_10'] else {}
        print(f"   ✓ #1: {top.get('state_name', 'N/A')} ({top.get('good_excellent', 0):.1f}%)")
        results.append(True)
    except Exception as e:
        print(f"   ✗ {e}")
        results.append(False)

    # 5. Season Trend
    print("\n5. season_trend_analysis()...")
    try:
        result = season_trend_analysis('CORN')
        print(f"   ✓ Year: {result['year']} | Weeks: {len(result['weeks_available'])}")
        print(f"   ✓ Trend: {result['trend_direction']}")
        results.append(True)
    except Exception as e:
        print(f"   ✗ {e}")
        results.append(False)

    return results


def test_progress_functions():
    """Test progress analysis functions."""
    print("\n" + "=" * 70)
    print("TESTING PROGRESS FUNCTIONS")
    print("=" * 70)

    results = []

    # 6. Harvest Progress
    print("\n6. harvest_progress_report()...")
    try:
        result = harvest_progress_report('CORN')
        print(f"   ✓ Year: {result['year']} | Week: {result['week']}")
        print(f"   ✓ Harvested: {result.get('percent_harvested', 0):.1f}%")
        results.append(True)
    except Exception as e:
        print(f"   ✗ {e}")
        results.append(False)

    # 7. Planting Progress
    print("\n7. planting_progress_report()...")
    try:
        result = planting_progress_report('CORN')
        print(f"   ✓ Year: {result['year']} | Week: {result['week']}")
        print(f"   ✓ Planted: {result.get('percent_planted', 0):.1f}%")
        results.append(True)
    except Exception as e:
        print(f"   ✗ {e}")
        results.append(False)

    return results


def test_yield_production_area_functions():
    """Test yield, production, and area functions."""
    print("\n" + "=" * 70)
    print("TESTING YIELD/PRODUCTION/AREA FUNCTIONS")
    print("=" * 70)

    results = []

    # 8. Yield
    print("\n8. yield_analysis()...")
    try:
        result = yield_analysis('CORN')
        print(f"   ✓ Year: {result['year']}")
        print(f"   ✓ Yield: {result.get('yield_bu_per_acre', 0):.1f} bu/acre")
        results.append(True)
    except Exception as e:
        print(f"   ✗ {e}")
        results.append(False)

    # 9. Production
    print("\n9. production_analysis()...")
    try:
        result = production_analysis('CORN')
        print(f"   ✓ Year: {result['year']}")
        prod = result.get('production_bu', 0)
        print(f"   ✓ Production: {prod/1e9:.2f} billion bu")
        results.append(True)
    except Exception as e:
        print(f"   ✗ {e}")
        results.append(False)

    # 10. Area
    print("\n10. area_analysis()...")
    try:
        result = area_analysis('CORN', area_type='PLANTED')
        print(f"   ✓ Year: {result['year']}")
        acres = result.get('acres', 0)
        print(f"   ✓ Acres: {acres/1e6:.2f} million")
        results.append(True)
    except Exception as e:
        print(f"   ✗ {e}")
        results.append(False)

    return results


def test_comprehensive_report():
    """Test comprehensive multi-metric report."""
    print("\n" + "=" * 70)
    print("TESTING COMPREHENSIVE REPORT")
    print("=" * 70)

    print("\n11. comprehensive_crop_report()...")
    try:
        result = comprehensive_crop_report('CORN')
        print(f"   ✓ Year: {result['year']}")
        print(f"   ✓ Generated: {result['generated_at']}")
        print(f"   ✓ Metrics included: {len(result['metrics'])}")

        for metric_name, metric_data in result['metrics'].items():
            if 'error' not in metric_data:
                print(f"      ✓ {metric_name}")
            else:
                print(f"      ⚠ {metric_name}: {metric_data['error']}")

        return [True]
    except Exception as e:
        print(f"   ✗ {e}")
        import traceback
        traceback.print_exc()
        return [False]


def main():
    """Run all integration tests."""
    print("\n" + "=" * 70)
    print("US CROP MONITOR - COMPREHENSIVE INTEGRATION TEST")
    print("=" * 70)

    all_results = []

    all_results.extend(test_condition_functions())
    all_results.extend(test_progress_functions())
    all_results.extend(test_yield_production_area_functions())
    all_results.extend(test_comprehensive_report())

    # Summary
    print("\n" + "=" * 70)
    print("FINAL TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for r in all_results if r)
    total = len(all_results)

    print(f"\n✓ Passed: {passed}/{total} tests")
    print(f"✗ Failed: {total - passed}/{total} tests")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! SKILL IS FULLY FUNCTIONAL!")
    else:
        print(f"\n⚠ {total - passed} test(s) failed")

    print("=" * 70)

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
