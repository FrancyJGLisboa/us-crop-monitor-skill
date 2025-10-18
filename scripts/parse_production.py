#!/usr/bin/env python3
"""
NASS Crop Production Data Parser

Parses and transforms NASS crop production data (total bushels).

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


def parse_production_response(response_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Parse NASS production API response into DataFrame.

    Args:
        response_data: List of response records

    Returns:
        DataFrame with parsed production data

    Raises:
        ParseError: On parsing failure
    """
    if not response_data:
        raise ParseError("Empty response data")

    try:
        df = pd.DataFrame(response_data)

        # Convert Value to numeric (production in BU or 1000 BU)
        df['Value'] = pd.to_numeric(df['Value'], errors='coerce')

        # Convert year to int
        if 'year' in df.columns:
            df['year'] = pd.to_numeric(df['year'], errors='coerce').astype('Int64')

        # Extract reference period
        if 'reference_period_desc' in df.columns:
            df['period'] = df['reference_period_desc']

        # Check units and normalize to bushels
        if 'unit_desc' in df.columns:
            # Sometimes production is in BU, sometimes in 1000 BU
            df['production_bu'] = df.apply(normalize_production_units, axis=1)
        else:
            df['production_bu'] = df['Value']

        return df

    except Exception as e:
        raise ParseError(f"Failed to parse production response: {e}")


def normalize_production_units(row) -> float:
    """
    Normalize production units to bushels.

    Args:
        row: DataFrame row

    Returns:
        Production in bushels
    """
    value = row.get('Value', 0)
    unit = row.get('unit_desc', '')

    if pd.isna(value):
        return np.nan

    unit_upper = str(unit).upper()

    if '1000 BU' in unit_upper or '1,000 BU' in unit_upper:
        return value * 1000
    else:
        # Assume BU if not specified
        return value


def aggregate_production(
    df: pd.DataFrame,
    by: str = 'national'
) -> pd.DataFrame:
    """
    Aggregate production data by geographic level.

    Args:
        df: DataFrame with parsed production data
        by: Aggregation level ('national', 'state')

    Returns:
        Aggregated DataFrame

    Raises:
        ParseError: On aggregation failure
    """
    if df.empty:
        raise ParseError("Cannot aggregate empty DataFrame")

    # Group columns based on aggregation level
    if by == 'national':
        group_cols = ['commodity_desc', 'year']
    elif by == 'state':
        group_cols = ['commodity_desc', 'year', 'state_name']
    else:
        raise ParseError(f"Invalid aggregation level: {by}")

    # Add period if available
    if 'period' in df.columns:
        group_cols.append('period')

    # Filter to columns that exist
    available_cols = [col for col in group_cols if col in df.columns]

    if 'production_bu' not in df.columns:
        raise ParseError("No production column to aggregate")

    # Sum production
    try:
        aggregated = df.groupby(available_cols, dropna=False)['production_bu'].sum().reset_index()
        return aggregated
    except Exception as e:
        raise ParseError(f"Aggregation failed: {e}")


def calculate_production_change(
    df: pd.DataFrame,
    current_year: int,
    previous_year: int
) -> pd.DataFrame:
    """
    Calculate year-over-year production change.

    Args:
        df: DataFrame with production data for multiple years
        current_year: Current year
        previous_year: Previous year

    Returns:
        DataFrame with production change calculations
    """
    if df.empty or 'year' not in df.columns:
        return df

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
        df_previous[merge_on + ['production_bu']],
        on=merge_on,
        how='inner',
        suffixes=('_current', '_previous')
    )

    # Calculate change
    merged['production_change'] = merged['production_bu_current'] - merged['production_bu_previous']
    merged['production_change_pct'] = (merged['production_change'] / merged['production_bu_previous']) * 100

    return merged


def format_production_millions(value: float) -> str:
    """
    Format production value in millions of bushels.

    Args:
        value: Production in bushels

    Returns:
        Formatted string
    """
    if pd.isna(value):
        return 'N/A'
    millions = value / 1_000_000
    return f"{millions:.1f}M bu"


def format_production_report(df: pd.DataFrame) -> str:
    """
    Format production data as human-readable report.

    Args:
        df: DataFrame with production data

    Returns:
        Formatted string report
    """
    if df.empty:
        return "No data available"

    lines = []
    lines.append("\nCROP PRODUCTION ESTIMATES")
    lines.append("=" * 60)

    for _, row in df.iterrows():
        commodity = row.get('commodity_desc', 'N/A')
        year = row.get('year', 'N/A')
        state = row.get('state_name', 'US')
        production = row.get('production_bu', row.get('production_bu_current', 0))
        period = row.get('period', '')

        lines.append(f"\n{commodity} - {state} - {year}")
        if period:
            lines.append(f"  Period: {period}")
        lines.append(f"  Production: {format_production_millions(production)}")

        # If YoY comparison available
        if 'production_change' in row and pd.notna(row['production_change']):
            change = row['production_change']
            change_pct = row.get('production_change_pct', 0)
            symbol = '▲' if change > 0 else '▼'
            lines.append(f"  Change: {symbol} {format_production_millions(abs(change))} ({change_pct:+.1f}%)")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def main():
    """Test parsing functions."""
    # Sample production data
    sample_data = [
        {
            'commodity_desc': 'CORN',
            'year': 2025,
            'reference_period_desc': 'YEAR',
            'state_name': 'IOWA',
            'short_desc': 'CORN, GRAIN - PRODUCTION, MEASURED IN BU',
            'Value': '2450000000',  # 2.45 billion bushels
            'statisticcat_desc': 'PRODUCTION',
            'unit_desc': 'BU'
        },
        {
            'commodity_desc': 'CORN',
            'year': 2024,
            'reference_period_desc': 'YEAR',
            'state_name': 'IOWA',
            'short_desc': 'CORN, GRAIN - PRODUCTION, MEASURED IN BU',
            'Value': '2300000000',  # 2.3 billion bushels
            'statisticcat_desc': 'PRODUCTION',
            'unit_desc': 'BU'
        }
    ]

    print("Testing production parser...")

    # Parse
    df = parse_production_response(sample_data)
    print(f"\nParsed {len(df)} records")
    print(df[['commodity_desc', 'year', 'state_name', 'production_bu']])

    # Calculate YoY change
    comparison = calculate_production_change(df, 2025, 2024)
    print(f"\nYear-over-year comparison:")
    print(comparison[['state_name', 'production_bu_current', 'production_bu_previous', 'production_change_pct']])

    # Format report
    report = format_production_report(comparison)
    print(report)


if __name__ == "__main__":
    main()
