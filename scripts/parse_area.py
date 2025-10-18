#!/usr/bin/env python3
"""
NASS Crop Area Data Parser

Parses and transforms NASS crop area data (acres planted/harvested).

Author: Agent Creator
Version: 2.0.0
"""

import sys
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))


class ParseError(Exception):
    """Exception for parsing errors."""
    pass


def parse_area_response(response_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Parse NASS area API response into DataFrame.

    Args:
        response_data: List of response records

    Returns:
        DataFrame with parsed area data

    Raises:
        ParseError: On parsing failure
    """
    if not response_data:
        raise ParseError("Empty response data")

    try:
        df = pd.DataFrame(response_data)

        # Convert Value to numeric (acres)
        df['Value'] = pd.to_numeric(df['Value'], errors='coerce')

        # Convert year to int
        if 'year' in df.columns:
            df['year'] = pd.to_numeric(df['year'], errors='coerce').astype('Int64')

        # Determine if planted or harvested
        if 'statisticcat_desc' in df.columns:
            df['area_type'] = df['statisticcat_desc'].apply(extract_area_type)

        # Check units and normalize to acres
        if 'unit_desc' in df.columns:
            df['acres'] = df.apply(normalize_area_units, axis=1)
        else:
            df['acres'] = df['Value']

        return df

    except Exception as e:
        raise ParseError(f"Failed to parse area response: {e}")


def extract_area_type(statisticcat: str) -> Optional[str]:
    """
    Extract area type from statisticcat_desc.

    Args:
        statisticcat: String like "AREA PLANTED" or "AREA HARVESTED"

    Returns:
        'PLANTED' or 'HARVESTED'
    """
    if not isinstance(statisticcat, str):
        return None

    upper = statisticcat.upper()
    if 'PLANTED' in upper:
        return 'PLANTED'
    elif 'HARVESTED' in upper:
        return 'HARVESTED'
    else:
        return None


def normalize_area_units(row) -> float:
    """
    Normalize area units to acres.

    Args:
        row: DataFrame row

    Returns:
        Area in acres
    """
    value = row.get('Value', 0)
    unit = row.get('unit_desc', '')

    if pd.isna(value):
        return np.nan

    unit_upper = str(unit).upper()

    if 'ACRES' in unit_upper:
        return value
    else:
        # Assume acres if not specified
        return value


def aggregate_area(
    df: pd.DataFrame,
    by: str = 'national',
    area_type: Optional[str] = None
) -> pd.DataFrame:
    """
    Aggregate area data by geographic level.

    Args:
        df: DataFrame with parsed area data
        by: Aggregation level ('national', 'state')
        area_type: Filter to 'PLANTED' or 'HARVESTED' (None for all)

    Returns:
        Aggregated DataFrame

    Raises:
        ParseError: On aggregation failure
    """
    if df.empty:
        raise ParseError("Cannot aggregate empty DataFrame")

    # Filter by area type if specified
    if area_type is not None:
        df = df[df['area_type'] == area_type.upper()].copy()

    if df.empty:
        raise ParseError(f"No data for area type {area_type}")

    # Group columns based on aggregation level
    if by == 'national':
        group_cols = ['commodity_desc', 'year', 'area_type']
    elif by == 'state':
        group_cols = ['commodity_desc', 'year', 'state_name', 'area_type']
    else:
        raise ParseError(f"Invalid aggregation level: {by}")

    # Filter to columns that exist
    available_cols = [col for col in group_cols if col in df.columns]

    if 'acres' not in df.columns:
        raise ParseError("No acres column to aggregate")

    # Sum acres
    try:
        aggregated = df.groupby(available_cols, dropna=False)['acres'].sum().reset_index()
        return aggregated
    except Exception as e:
        raise ParseError(f"Aggregation failed: {e}")


def compare_planted_vs_harvested(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compare planted acres vs harvested acres.

    Args:
        df: DataFrame with both planted and harvested data

    Returns:
        DataFrame with comparison
    """
    if df.empty or 'area_type' not in df.columns:
        return df

    df_planted = df[df['area_type'] == 'PLANTED'].copy()
    df_harvested = df[df['area_type'] == 'HARVESTED'].copy()

    if df_planted.empty or df_harvested.empty:
        return df

    # Merge on state or national
    if 'state_name' in df_planted.columns:
        merge_on = ['commodity_desc', 'year', 'state_name']
    else:
        merge_on = ['commodity_desc', 'year']

    merged = df_planted.merge(
        df_harvested[merge_on + ['acres']],
        on=merge_on,
        how='outer',
        suffixes=('_planted', '_harvested')
    )

    # Calculate difference (abandoned/prevented from planting)
    merged['acres_not_harvested'] = merged['acres_planted'] - merged['acres_harvested'].fillna(0)
    merged['harvest_rate_pct'] = (merged['acres_harvested'] / merged['acres_planted']) * 100

    return merged


def calculate_area_change(
    df: pd.DataFrame,
    current_year: int,
    previous_year: int,
    area_type: str = 'PLANTED'
) -> pd.DataFrame:
    """
    Calculate year-over-year area change.

    Args:
        df: DataFrame with area data for multiple years
        current_year: Current year
        previous_year: Previous year
        area_type: 'PLANTED' or 'HARVESTED'

    Returns:
        DataFrame with area change calculations
    """
    if df.empty or 'year' not in df.columns:
        return df

    # Filter by area type
    df = df[df['area_type'] == area_type.upper()].copy()

    df_current = df[df['year'] == current_year].copy()
    df_previous = df[df['year'] == previous_year].copy()

    if df_current.empty or df_previous.empty:
        return df_current

    # Merge on state or just compare national
    if 'state_name' in df_current.columns:
        merge_on = ['commodity_desc', 'state_name']
    else:
        merge_on = ['commodity_desc']

    merged = df_current.merge(
        df_previous[merge_on + ['acres']],
        on=merge_on,
        how='inner',
        suffixes=('_current', '_previous')
    )

    # Calculate change
    merged['acres_change'] = merged['acres_current'] - merged['acres_previous']
    merged['acres_change_pct'] = (merged['acres_change'] / merged['acres_previous']) * 100

    return merged


def format_acres_millions(value: float) -> str:
    """
    Format acres value in millions.

    Args:
        value: Acres

    Returns:
        Formatted string
    """
    if pd.isna(value):
        return 'N/A'
    millions = value / 1_000_000
    return f"{millions:.2f}M acres"


def format_area_report(df: pd.DataFrame) -> str:
    """
    Format area data as human-readable report.

    Args:
        df: DataFrame with area data

    Returns:
        Formatted string report
    """
    if df.empty:
        return "No data available"

    lines = []
    lines.append("\nCROP AREA ESTIMATES")
    lines.append("=" * 60)

    for _, row in df.iterrows():
        commodity = row.get('commodity_desc', 'N/A')
        year = row.get('year', 'N/A')
        state = row.get('state_name', 'US')
        area_type = row.get('area_type', 'N/A')
        acres = row.get('acres', row.get('acres_current', 0))

        lines.append(f"\n{commodity} - {state} - {year}")
        lines.append(f"  {area_type}: {format_acres_millions(acres)}")

        # If YoY comparison available
        if 'acres_change' in row and pd.notna(row['acres_change']):
            change = row['acres_change']
            change_pct = row.get('acres_change_pct', 0)
            symbol = '▲' if change > 0 else '▼'
            lines.append(f"  Change: {symbol} {format_acres_millions(abs(change))} ({change_pct:+.1f}%)")

        # If planted vs harvested comparison
        if 'harvest_rate_pct' in row and pd.notna(row['harvest_rate_pct']):
            rate = row['harvest_rate_pct']
            not_harvested = row.get('acres_not_harvested', 0)
            lines.append(f"  Harvest rate: {rate:.1f}%")
            if not_harvested > 0:
                lines.append(f"  Not harvested: {format_acres_millions(not_harvested)}")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def main():
    """Test parsing functions."""
    # Sample area data
    sample_data = [
        {
            'commodity_desc': 'CORN',
            'year': 2025,
            'state_name': 'IOWA',
            'short_desc': 'CORN, GRAIN - ACRES PLANTED',
            'Value': '12800000',  # 12.8 million acres
            'statisticcat_desc': 'AREA PLANTED',
            'unit_desc': 'ACRES'
        },
        {
            'commodity_desc': 'CORN',
            'year': 2025,
            'state_name': 'IOWA',
            'short_desc': 'CORN, GRAIN - ACRES HARVESTED',
            'Value': '12700000',  # 12.7 million acres
            'statisticcat_desc': 'AREA HARVESTED',
            'unit_desc': 'ACRES'
        }
    ]

    print("Testing area parser...")

    # Parse
    df = parse_area_response(sample_data)
    print(f"\nParsed {len(df)} records")
    print(df[['commodity_desc', 'year', 'state_name', 'area_type', 'acres']])

    # Compare planted vs harvested
    comparison = compare_planted_vs_harvested(df)
    print(f"\nPlanted vs Harvested:")
    print(comparison[['state_name', 'acres_planted', 'acres_harvested', 'harvest_rate_pct']])

    # Format report
    report = format_area_report(comparison)
    print(report)


if __name__ == "__main__":
    main()
