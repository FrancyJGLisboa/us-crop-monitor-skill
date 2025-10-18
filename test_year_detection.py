#!/usr/bin/env python3
"""
Test year detection and auto-fallback functionality.
"""

import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from analyze_crops import current_condition_report
from fetch_nass import NassApiClient

def test_auto_year_detection():
    """Test that year is auto-detected when not specified."""
    print("\n" + "=" * 70)
    print("TEST: Auto Year Detection")
    print("=" * 70)

    try:
        # Call WITHOUT specifying year
        result = current_condition_report(
            commodity='CORN',
            # year parameter omitted - should auto-detect 2025
        )

        print(f"\n✓ Successfully auto-detected year!")
        print(f"  Year used: {result['year']}")
        print(f"  Year requested: {result['year_requested']}")
        print(f"  Fallback used: {result['fallback_used']}")
        print(f"  Year info: {result['year_info']}")
        print(f"  Week: {result['week']}")
        print(f"  Good+Excellent: {result['conditions'].get('good_excellent', 0):.1f}%")

        # Verify it used current year or fallback
        from datetime import datetime
        current_year = datetime.now().year
        assert result['year'] in [current_year, current_year-1], \
            f"Expected year {current_year} or {current_year-1}, got {result['year']}"

        return True

    except Exception as e:
        print(f"\n✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_explicit_year():
    """Test that explicit year still works."""
    print("\n" + "=" * 70)
    print("TEST: Explicit Year Specification")
    print("=" * 70)

    try:
        # Call WITH specific year
        result = current_condition_report(
            commodity='CORN',
            year=2024  # Explicitly request 2024
        )

        print(f"\n✓ Successfully used explicit year!")
        print(f"  Year used: {result['year']}")
        print(f"  Year requested: {result['year_requested']}")
        print(f"  Fallback used: {result['fallback_used']}")
        print(f"  Year info: {result['year_info']}")

        assert result['year'] == 2024, f"Expected 2024, got {result['year']}"
        assert result['year_requested'] == 2024

        return True

    except Exception as e:
        print(f"\n✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run year detection tests."""
    print("\n" + "=" * 70)
    print("YEAR DETECTION TEST SUITE")
    print("=" * 70)

    results = []
    results.append(("Auto Year Detection", test_auto_year_detection()))
    results.append(("Explicit Year", test_explicit_year()))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print("\n" + "-" * 70)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 70)

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
