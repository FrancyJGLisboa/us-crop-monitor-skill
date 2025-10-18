#!/usr/bin/env python3
"""
Query corn harvest progress for major Cornbelt states.

This script fetches harvest progress (% harvested) data from USDA NASS,
rather than condition (quality) data.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from fetch_nass import NassApiClient, DataNotFoundError

def get_harvest_progress(commodity='CORN', year=None):
    """
    Get harvest progress (% harvested) for corn.

    Args:
        commodity: Crop name (default: CORN)
        year: Year (default: current year)

    Returns:
        Dictionary with harvest progress data
    """
    if year is None:
        year = datetime.now().year

    # Initialize client
    client = NassApiClient()

    # Build API params for PROGRESS (not CONDITION)
    api_params = {
        'source_desc': 'SURVEY',
        'sector_desc': 'CROPS',
        'commodity_desc': commodity,
        'statisticcat_desc': 'PROGRESS',  # PROGRESS instead of CONDITION
        'year': year,
        'freq_desc': 'WEEKLY',
        'agg_level_desc': 'STATE'
    }

    # We want harvest progress specifically
    # This is typically measured as "PCT HARVESTED"

    print(f"Fetching {commodity} harvest progress for {year}...")
    print("=" * 70)

    try:
        # Make request
        response_data = client._make_request('api_GET', api_params)

        # Extract data
        if 'data' in response_data:
            data = response_data['data']
        else:
            data = response_data

        if not data:
            print(f"No harvest progress data found for {commodity} {year}")
            return

        # Filter for "HARVESTED" data
        harvest_data = [
            record for record in data
            if 'HARVESTED' in record.get('short_desc', '').upper()
        ]

        if not harvest_data:
            print("No HARVESTED data found in response")
            print("\nAvailable descriptions:")
            unique_descs = set(record.get('short_desc', '') for record in data[:10])
            for desc in sorted(unique_descs):
                print(f"  - {desc}")
            return

        # Find the most recent week
        weeks_data = {}
        for record in harvest_data:
            week = record.get('week_ending', '')
            state = record.get('state_name', '')
            value = record.get('Value', '0')
            ref_period = record.get('reference_period_desc', '')

            try:
                value_num = float(value)
            except (ValueError, TypeError):
                continue

            if week not in weeks_data:
                weeks_data[week] = {}

            weeks_data[week][state] = {
                'value': value_num,
                'reference_period': ref_period
            }

        # Get the latest week
        if not weeks_data:
            print("No valid harvest data found")
            return

        latest_week = max(weeks_data.keys())
        latest_data = weeks_data[latest_week]

        print(f"\nCORN HARVEST PROGRESS - Latest Data")
        print(f"Week ending: {latest_week}")
        print(f"Reference: {list(latest_data.values())[0]['reference_period']}")
        print("\n" + "=" * 70)

        # Major Cornbelt states
        cornbelt_states = [
            'IOWA', 'ILLINOIS', 'NEBRASKA', 'INDIANA', 'MINNESOTA',
            'KANSAS', 'MISSOURI', 'OHIO', 'SOUTH DAKOTA', 'NORTH DAKOTA',
            'WISCONSIN', 'MICHIGAN'
        ]

        # Sort states by harvest progress
        state_progress = []
        for state, info in latest_data.items():
            if state in cornbelt_states:
                state_progress.append((state, info['value']))

        state_progress.sort(key=lambda x: x[1], reverse=True)

        print("\nMAJOR CORNBELT STATES - HARVEST PROGRESS:")
        print(f"{'State':<20} {'% Harvested':>15}")
        print("-" * 40)

        total_progress = 0
        count = 0

        for state, progress in state_progress:
            print(f"{state:<20} {progress:>14.0f}%")
            total_progress += progress
            count += 1

        if count > 0:
            avg_progress = total_progress / count
            print("-" * 40)
            print(f"{'AVERAGE':<20} {avg_progress:>14.1f}%")

        # National data (if available)
        print("\n" + "=" * 70)

        # Try to get national data
        national_params = api_params.copy()
        national_params['agg_level_desc'] = 'NATIONAL'

        try:
            national_response = client._make_request('api_GET', national_params)
            if 'data' in national_response:
                national_data = national_response['data']
            else:
                national_data = national_response

            national_harvest = [
                record for record in national_data
                if 'HARVESTED' in record.get('short_desc', '').upper()
            ]

            if national_harvest:
                # Get most recent
                latest_national = max(national_harvest, key=lambda x: x.get('week_ending', ''))
                national_pct = latest_national.get('Value', '0')
                national_week = latest_national.get('week_ending', '')

                print(f"\nNATIONAL (US) HARVEST PROGRESS:")
                print(f"Week ending: {national_week}")
                print(f"Percent harvested: {national_pct}%")

        except Exception as e:
            print(f"\nCould not fetch national data: {e}")

        print("\n" + "=" * 70)

        # Historical comparison (try to get same week last year)
        try:
            last_year = year - 1
            last_year_params = api_params.copy()
            last_year_params['year'] = last_year

            print(f"\nComparing with {last_year} (same week)...")

            last_year_response = client._make_request('api_GET', last_year_params)
            if 'data' in last_year_response:
                last_year_data = last_year_response['data']
            else:
                last_year_data = last_year_response

            last_year_harvest = [
                record for record in last_year_data
                if 'HARVESTED' in record.get('short_desc', '').upper()
            ]

            # Try to match the week
            # Get the reference period from current year
            current_ref_period = list(latest_data.values())[0]['reference_period']

            matching_records = [
                record for record in last_year_harvest
                if record.get('reference_period_desc', '') == current_ref_period
            ]

            if matching_records:
                print(f"\n{year} vs {last_year} COMPARISON:")
                print(f"{'State':<20} {year:>10} {last_year:>10} {'Change':>10}")
                print("-" * 55)

                ly_by_state = {
                    record.get('state_name', ''): float(record.get('Value', 0))
                    for record in matching_records
                    if record.get('state_name', '') in cornbelt_states
                }

                for state, current_pct in state_progress:
                    if state in ly_by_state:
                        last_year_pct = ly_by_state[state]
                        change = current_pct - last_year_pct
                        change_str = f"{change:+.0f}%"
                        print(f"{state:<20} {current_pct:>9.0f}% {last_year_pct:>9.0f}% {change_str:>10}")

        except Exception as e:
            print(f"\nCould not fetch year-over-year comparison: {e}")

        print("\n" + "=" * 70)

    except DataNotFoundError:
        print(f"No data found for {commodity} {year}")
        print("\nNote: Harvest progress data is typically available from September onwards.")
        print("If it's early in the year, try checking condition data instead.")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Query corn harvest progress')
    parser.add_argument('--commodity', default='CORN', help='Commodity (default: CORN)')
    parser.add_argument('--year', type=int, help='Year (default: current year)')

    args = parser.parse_args()

    get_harvest_progress(args.commodity, args.year)
