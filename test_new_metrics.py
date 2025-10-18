#!/usr/bin/env python3
"""
Test script for new metric types (PROGRESS, YIELD, PRODUCTION, AREA).

This script tests all the new fetch methods and parsers.
"""

import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from fetch_nass import NassApiClient, DataNotFoundError
from parse_progress import parse_progress_response, get_harvest_progress, format_progress_report
from parse_yield import parse_yield_response, format_yield_report
from parse_production import parse_production_response, format_production_report
from parse_area import parse_area_response, compare_planted_vs_harvested, format_area_report


def test_progress():
    """Test progress data fetching and parsing."""
    print("\n" + "=" * 70)
    print("TEST 1: CROP PROGRESS (Harvest)")
    print("=" * 70)

    try:
        client = NassApiClient()

        # Fetch corn harvest progress for 2025
        result = client.get_crop_progress(
            commodity='CORN',
            year=2025,
            agg_level='STATE'
        )

        data = result['data']
        metadata = result['metadata']

        print(f"\n✓ Fetched {len(data)} progress records")
        print(f"  Metric type: {metadata['metric_type']}")
        print(f"  From cache: {metadata['from_cache']}")

        # Parse
        df = parse_progress_response(data)
        print(f"\n✓ Parsed {len(df)} records")

        # Get harvest progress
        harvest_df = get_harvest_progress(df, commodity='CORN', latest_only=True)
        print(f"✓ Filtered to {len(harvest_df)} harvest records")

        # Show sample
        if not harvest_df.empty:
            print("\nSample data:")
            print(harvest_df[['state_name', 'week_number', 'Value']].head(5))

            # Format report
            report = format_progress_report(harvest_df.head(3))
            print(report)

        return True

    except Exception as e:
        print(f"\n✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_yield():
    """Test yield data fetching and parsing."""
    print("\n" + "=" * 70)
    print("TEST 2: CROP YIELD")
    print("=" * 70)

    try:
        client = NassApiClient()

        # Fetch corn yield for 2024 (2025 might not be final yet)
        result = client.get_crop_yield(
            commodity='CORN',
            year=2024,
            agg_level='STATE'
        )

        data = result['data']
        metadata = result['metadata']

        print(f"\n✓ Fetched {len(data)} yield records")
        print(f"  Metric type: {metadata['metric_type']}")
        print(f"  From cache: {metadata['from_cache']}")

        # Parse
        df = parse_yield_response(data)
        print(f"✓ Parsed {len(df)} records")

        # Show sample
        if not df.empty:
            print("\nSample data:")
            print(df[['state_name', 'yield_bu_per_acre']].head(5))

            # Format report
            report = format_yield_report(df.head(3))
            print(report)

        return True

    except DataNotFoundError as e:
        print(f"\n⚠ No data found: {e}")
        print("  (This is expected if final yield data isn't published yet)")
        return True  # Not a failure
    except Exception as e:
        print(f"\n✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_production():
    """Test production data fetching and parsing."""
    print("\n" + "=" * 70)
    print("TEST 3: CROP PRODUCTION")
    print("=" * 70)

    try:
        client = NassApiClient()

        # Fetch corn production for 2024
        result = client.get_crop_production(
            commodity='CORN',
            year=2024,
            agg_level='STATE'
        )

        data = result['data']
        metadata = result['metadata']

        print(f"\n✓ Fetched {len(data)} production records")
        print(f"  Metric type: {metadata['metric_type']}")
        print(f"  From cache: {metadata['from_cache']}")

        # Parse
        df = parse_production_response(data)
        print(f"✓ Parsed {len(df)} records")

        # Show sample
        if not df.empty:
            print("\nSample data:")
            print(df[['state_name', 'production_bu']].head(5))

            # Format report
            report = format_production_report(df.head(3))
            print(report)

        return True

    except DataNotFoundError as e:
        print(f"\n⚠ No data found: {e}")
        return True  # Not a failure
    except Exception as e:
        print(f"\n✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_area():
    """Test area data fetching and parsing."""
    print("\n" + "=" * 70)
    print("TEST 4: CROP AREA (Planted & Harvested)")
    print("=" * 70)

    try:
        client = NassApiClient()

        # Fetch corn area planted for 2025
        result_planted = client.get_crop_area(
            commodity='CORN',
            year=2025,
            area_type='PLANTED',
            agg_level='STATE'
        )

        data_planted = result_planted['data']
        metadata = result_planted['metadata']

        print(f"\n✓ Fetched {len(data_planted)} PLANTED records")
        print(f"  Metric type: {metadata['metric_type']}")

        # Parse
        df_planted = parse_area_response(data_planted)
        print(f"✓ Parsed {len(df_planted)} planted records")

        # Try to get harvested data (might not be available for current year)
        try:
            result_harvested = client.get_crop_area(
                commodity='CORN',
                year=2024,  # Use previous year for harvested
                area_type='HARVESTED',
                agg_level='STATE'
            )
            data_harvested = result_harvested['data']
            df_harvested = parse_area_response(data_harvested)
            print(f"✓ Parsed {len(df_harvested)} harvested records (2024)")

        except DataNotFoundError:
            df_harvested = None
            print("⚠ Harvested data not available for comparison")

        # Show sample
        if not df_planted.empty:
            print("\nSample PLANTED data:")
            print(df_planted[['state_name', 'acres']].head(5))

            # Format report
            report = format_area_report(df_planted.head(3))
            print(report)

        return True

    except DataNotFoundError as e:
        print(f"\n⚠ No data found: {e}")
        return True  # Not a failure
    except Exception as e:
        print(f"\n✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_unified_get_crop_data():
    """Test the unified get_crop_data method."""
    print("\n" + "=" * 70)
    print("TEST 5: UNIFIED get_crop_data() METHOD")
    print("=" * 70)

    try:
        client = NassApiClient()

        # Test each metric type through unified method
        metrics_to_test = [
            ('CONDITION', 2024, {'week': 32, 'agg_level': 'NATIONAL'}),
            ('PROGRESS', 2025, {'agg_level': 'NATIONAL'}),
        ]

        for metric_type, year, kwargs in metrics_to_test:
            print(f"\n  Testing metric_type='{metric_type}'...")
            result = client.get_crop_data(
                metric_type=metric_type,
                commodity='CORN',
                year=year,
                **kwargs
            )

            data = result['data']
            metadata = result['metadata']

            print(f"    ✓ {len(data)} records fetched")
            print(f"    ✓ Metric type in metadata: {metadata['metric_type']}")

        return True

    except Exception as e:
        print(f"\n✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("US CROP MONITOR - NEW METRICS TEST SUITE")
    print("=" * 70)

    results = []

    # Run tests
    results.append(("Progress (Harvest)", test_progress()))
    results.append(("Yield", test_yield()))
    results.append(("Production", test_production()))
    results.append(("Area (Planted/Harvested)", test_area()))
    results.append(("Unified get_crop_data()", test_unified_get_crop_data()))

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
