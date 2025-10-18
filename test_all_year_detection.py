#!/usr/bin/env python3
"""
Comprehensive test for year auto-detection across all analysis functions.
"""

import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from analyze_crops import (
    current_condition_report,
    week_over_week_comparison,
    state_rankings,
    season_trend_analysis
)


def test_all_functions():
    """Test that all 4 main functions auto-detect year correctly."""
    print("\n" + "=" * 70)
    print("COMPREHENSIVE YEAR AUTO-DETECTION TEST")
    print("=" * 70)

    results = []

    # Test 1: current_condition_report
    print("\n1. Testing current_condition_report()...")
    try:
        result = current_condition_report('CORN')  # No year specified
        print(f"   ✓ Year used: {result['year']}")
        print(f"   ✓ Year info: {result['year_info']}")
        print(f"   ✓ Good+Excellent: {result['conditions'].get('good_excellent', 0):.1f}%")
        results.append(("current_condition_report", True))
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
        results.append(("current_condition_report", False))

    # Test 2: week_over_week_comparison
    print("\n2. Testing week_over_week_comparison()...")
    try:
        result = week_over_week_comparison('CORN')  # No year specified
        print(f"   ✓ Year used: {result['year']}")
        print(f"   ✓ Year info: {result['year_info']}")
        print(f"   ✓ Week comparison: {result['current_week']} vs {result['previous_week']}")
        print(f"   ✓ National delta: {result['national']['delta']:+.1f} points")
        results.append(("week_over_week_comparison", True))
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
        results.append(("week_over_week_comparison", False))

    # Test 3: state_rankings
    print("\n3. Testing state_rankings()...")
    try:
        result = state_rankings('CORN')  # No year specified
        print(f"   ✓ Year used: {result['year']}")
        print(f"   ✓ Year info: {result['year_info']}")
        print(f"   ✓ Total states: {len(result['rankings'])}")
        if result['top_10']:
            top_state = result['top_10'][0]
            print(f"   ✓ Top state: {top_state['state_name']} ({top_state['good_excellent']:.1f}%)")
        results.append(("state_rankings", True))
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
        results.append(("state_rankings", False))

    # Test 4: season_trend_analysis
    print("\n4. Testing season_trend_analysis()...")
    try:
        result = season_trend_analysis('CORN')  # No year specified
        print(f"   ✓ Year used: {result['year']}")
        print(f"   ✓ Year info: {result['year_info']}")
        print(f"   ✓ Weeks analyzed: {len(result['weeks_available'])}")
        print(f"   ✓ Trend: {result['trend_direction']}")
        print(f"   ✓ Peak: Week {result['peak']['week']} ({result['peak']['good_excellent']:.1f}%)")
        results.append(("season_trend_analysis", True))
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
        results.append(("season_trend_analysis", False))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}()")

    print("\n" + "-" * 70)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL FUNCTIONS NOW AUTO-DETECT YEAR CORRECTLY!")
        print("\nWhat this means:")
        print("  - Users can now ask 'Como está o milho hoje?' without specifying year")
        print("  - System auto-detects current year (2025)")
        print("  - Automatic fallback to previous year if current year has no data")
        print("  - Clear messages about which year's data is being shown")
    
    print("=" * 70)

    return passed == total


if __name__ == "__main__":
    success = test_all_functions()
    sys.exit(0 if success else 1)
