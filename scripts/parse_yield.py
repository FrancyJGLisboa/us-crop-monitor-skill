#!/usr/bin/env python3
"""
NASS Crop Yield Data Parser

Parses and transforms NASS crop yield data (bushels per acre).

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


def parse_yield_response(response_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Parse NASS yield API response into DataFrame.

    Args:
        response_data: List of response records

    Returns:
        DataFrame with parsed yield data

    Raises:
        ParseError: On parsing failure
    """
    if not response_data:
        raise ParseError("Empty response data")

    try:
        df = pd.DataFrame(response_data)

        # Convert Value to numeric (yield in BU/ACRE)
        df['Value'] = pd.to_numeric(df['Value'], errors='coerce')

        # Convert year to int
        if 'year' in df.columns:
            df['year'] = pd.to_numeric(df['year'], errors='coerce').astype('Int64')

        # Extract reference period (month for yield forecasts)
        if 'reference_period_desc' in df.columns:
            df['period'] = df['reference_period_desc']

        # Rename Value to yield for clarity
        if 'Value' in df.columns:
            df['yield_bu_per_acre'] = df['Value']

        return df

    except Exception as e:
        raise ParseError(f"Failed to parse yield response: {e}")


def aggregate_yield(
    df: pd.DataFrame,
    by: str = 'national'
) -> pd.DataFrame:
    """
    Aggregate yield data by geographic level.

    Args:
        df: DataFrame with parsed yield data
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

    if 'yield_bu_per_acre' not in df.columns and 'Value' not in df.columns:
        raise ParseError("No yield column to aggregate")

    value_col = 'yield_bu_per_acre' if 'yield_bu_per_acre' in df.columns else 'Value'

    # Aggregate
    try:
        aggregated = df.groupby(available_cols, dropna=False)[value_col].mean().reset_index()
        if value_col == 'Value':
            aggregated.rename(columns={'Value': 'yield_bu_per_acre'}, inplace=True)
        return aggregated
    except Exception as e:
        raise ParseError(f"Aggregation failed: {e}")


def compare_yield_forecasts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compare yield forecasts across different months/periods.

    Args:
        df: DataFrame with yield data from multiple periods

    Returns:
        DataFrame showing yield progression
    """
    if df.empty or 'period' not in df.columns:
        return df

    # Pivot to show progression
    try:
        df_pivot = df.pivot_table(
            index=['commodity_desc', 'state_name'] if 'state_name' in df.columns else ['commodity_desc'],
            columns='period',
            values='yield_bu_per_acre',
            aggfunc='first'
        ).reset_index()

        return df_pivot

    except Exception as e:
        print(f"Warning: Could not pivot yield forecasts: {e}")
        return df


def calculate_yield_change(df: pd.DataFrame, current_year: int, previous_year: int) -> pd.DataFrame:
    """
    Calculate year-over-year yield change.

    Args:
        df: DataFrame with yield data for multiple years
        current_year: Current year
        previous_year: Previous year

    Returns:
        DataFrame with yield change calculations
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
        df_previous[merge_on + ['yield_bu_per_acre']],
        on=merge_on,
        how='inner',
        suffixes=('_current', '_previous')
    )

    # Calculate change
    merged['yield_change'] = merged['yield_bu_per_acre_current'] - merged['yield_bu_per_acre_previous']
    merged['yield_change_pct'] = (merged['yield_change'] / merged['yield_bu_per_acre_previous']) * 100

    return merged


def format_yield_report(df: pd.DataFrame) -> str:
    """
    Format yield data as human-readable report.

    Args:
        df: DataFrame with yield data

    Returns:
        Formatted string report
    """
    if df.empty:
        return "No data available"

    lines = []
    lines.append("\nCROP YIELD ESTIMATES")
    lines.append("=" * 60)

    for _, row in df.iterrows():
        commodity = row.get('commodity_desc', 'N/A')
        year = row.get('year', 'N/A')
        state = row.get('state_name', 'US')
        yield_val = row.get('yield_bu_per_acre', row.get('Value', 'N/A'))
        period = row.get('period', '')

        lines.append(f"\n{commodity} - {state} - {year}")
        if period:
            lines.append(f"  Period: {period}")
        lines.append(f"  Yield: {yield_val:.1f} bushels/acre")

        # If YoY comparison available
        if 'yield_change' in row and pd.notna(row['yield_change']):
            change = row['yield_change']
            change_pct = row.get('yield_change_pct', 0)
            symbol = '▲' if change > 0 else '▼'
            lines.append(f"  Change: {symbol} {abs(change):.1f} bu/acre ({change_pct:+.1f}%)")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def main():
    """Test parsing functions."""
    # Sample yield data
    sample_data = [
        {
            'commodity_desc': 'CORN',
            'year': 2025,
            'reference_period_desc': 'YEAR',
            'state_name': 'IOWA',
            'short_desc': 'CORN, GRAIN - YIELD, MEASURED IN BU / ACRE',
            'Value': '185.5',
            'statisticcat_desc': 'YIELD',
            'unit_desc': 'BU / ACRE'
        },
        {
            'commodity_desc': 'CORN',
            'year': 2024,
            'reference_period_desc': 'YEAR',
            'state_name': 'IOWA',
            'short_desc': 'CORN, GRAIN - YIELD, MEASURED IN BU / ACRE',
            'Value': '175.0',
            'statisticcat_desc': 'YIELD',
            'unit_desc': 'BU / ACRE'
        }
    ]

    print("Testing yield parser...")

    # Parse
    df = parse_yield_response(sample_data)
    print(f"\nParsed {len(df)} records")
    print(df[['commodity_desc', 'year', 'state_name', 'yield_bu_per_acre']])

    # Calculate YoY change
    comparison = calculate_yield_change(df, 2025, 2024)
    print(f"\nYear-over-year comparison:")
    print(comparison[['state_name', 'yield_bu_per_acre_current', 'yield_bu_per_acre_previous', 'yield_change', 'yield_change_pct']])

    # Format report
    report = format_yield_report(comparison)
    print(report)


if __name__ == "__main__":
    main()
