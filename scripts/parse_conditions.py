#!/usr/bin/env python3
"""
NASS Crop Condition Data Parser

Parses and transforms NASS API responses into structured formats.

Author: Agent Creator
Version: 1.0.0
"""

import sys
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.validators import validate_percentage


class ParseError(Exception):
    """Exception for parsing errors."""
    pass


def parse_api_response(response_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Parse NASS API response into DataFrame.

    Args:
        response_data: List of response records

    Returns:
        DataFrame with parsed data

    Raises:
        ParseError: On parsing failure
    """
    if not response_data:
        raise ParseError("Empty response data")

    try:
        df = pd.DataFrame(response_data)

        # Convert Value to numeric
        df['Value'] = pd.to_numeric(df['Value'], errors='coerce')

        # Convert year to int
        if 'year' in df.columns:
            df['year'] = pd.to_numeric(df['year'], errors='coerce').astype('Int64')

        # Parse week number from reference_period_desc
        if 'reference_period_desc' in df.columns:
            df['week_number'] = df['reference_period_desc'].apply(extract_week_number)

        # Convert week_ending to datetime
        if 'week_ending' in df.columns:
            df['week_ending'] = pd.to_datetime(df['week_ending'], errors='coerce')

        # Extract condition category from short_desc
        if 'short_desc' in df.columns:
            df['condition_category'] = df['short_desc'].apply(extract_condition_category)

        return df

    except Exception as e:
        raise ParseError(f"Failed to parse response: {e}")


def extract_week_number(reference_period: str) -> Optional[int]:
    """
    Extract week number from reference period string.

    Args:
        reference_period: String like "WEEK #32"

    Returns:
        Week number or None
    """
    if not isinstance(reference_period, str):
        return None

    if 'WEEK' not in reference_period:
        return None

    try:
        # Format: "WEEK #32" or "WEEK 32"
        parts = reference_period.replace('#', '').split()
        for part in parts:
            if part.isdigit():
                return int(part)
        return None
    except (ValueError, IndexError):
        return None


def extract_condition_category(short_desc: str) -> Optional[str]:
    """
    Extract condition category from short description.

    Args:
        short_desc: String like "CORN - CONDITION, MEASURED IN PCT EXCELLENT"

    Returns:
        Condition category (EXCELLENT, GOOD, FAIR, POOR, VERY POOR)
    """
    if not isinstance(short_desc, str):
        return None

    short_desc_upper = short_desc.upper()

    # Check for each category
    if 'VERY POOR' in short_desc_upper:
        return 'VERY POOR'
    elif 'EXCELLENT' in short_desc_upper:
        return 'EXCELLENT'
    elif 'GOOD' in short_desc_upper:
        return 'GOOD'
    elif 'FAIR' in short_desc_upper:
        return 'FAIR'
    elif 'POOR' in short_desc_upper:
        return 'POOR'
    else:
        return None


def normalize_commodity_name(name: str) -> str:
    """
    Normalize commodity name.

    Args:
        name: Commodity name

    Returns:
        Normalized name
    """
    name_map = {
        'CORN': 'CORN',
        'CORN, GRAIN': 'CORN',
        'CORN, SILAGE': 'CORN',
        'SOYBEANS': 'SOYBEANS',
        'SOYBEAN': 'SOYBEANS',
        'WHEAT': 'WHEAT',
        'WHEAT, WINTER': 'WHEAT, WINTER',
        'WHEAT, SPRING': 'WHEAT, SPRING'
    }

    name_upper = name.upper()
    return name_map.get(name_upper, name_upper)


def aggregate_conditions(
    df: pd.DataFrame,
    by: str = 'national',
    week: Optional[int] = None
) -> pd.DataFrame:
    """
    Aggregate condition data by geographic level.

    Args:
        df: DataFrame with parsed data
        by: Aggregation level ('national', 'state', 'region')
        week: Filter to specific week (None for all)

    Returns:
        Aggregated DataFrame

    Raises:
        ParseError: On aggregation failure
    """
    if df.empty:
        raise ParseError("Cannot aggregate empty DataFrame")

    # Filter to specific week if provided
    if week is not None:
        df = df[df['week_number'] == week].copy()

    if df.empty:
        raise ParseError(f"No data for week {week}")

    # Group columns based on aggregation level
    if by == 'national':
        group_cols = ['commodity_desc', 'year', 'week_number', 'condition_category']
    elif by == 'state':
        group_cols = ['commodity_desc', 'year', 'week_number', 'state_name', 'condition_category']
    elif by == 'region':
        # Would need region mapping - simplified here
        group_cols = ['commodity_desc', 'year', 'week_number', 'condition_category']
    else:
        raise ParseError(f"Invalid aggregation level: {by}")

    # Filter to columns that exist
    available_cols = [col for col in group_cols if col in df.columns]

    if 'Value' not in df.columns:
        raise ParseError("No 'Value' column to aggregate")

    # Aggregate
    try:
        aggregated = df.groupby(available_cols, dropna=False)['Value'].mean().reset_index()
        return aggregated
    except Exception as e:
        raise ParseError(f"Aggregation failed: {e}")


def calculate_good_excellent(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Good+Excellent percentage.

    Args:
        df: DataFrame with condition categories

    Returns:
        DataFrame with good_excellent column added
    """
    if df.empty:
        return df

    # Pivot to wide format if needed
    if 'condition_category' in df.columns:
        df_pivot = pivot_conditions_table(df)
    else:
        df_pivot = df.copy()

    # Calculate Good + Excellent
    good = df_pivot.get('GOOD', 0)
    excellent = df_pivot.get('EXCELLENT', 0)

    df_pivot['good_excellent'] = good + excellent

    # Also calculate Poor + Very Poor
    poor = df_pivot.get('POOR', 0)
    very_poor = df_pivot.get('VERY POOR', 0)
    df_pivot['poor_very_poor'] = poor + very_poor

    return df_pivot


def pivot_conditions_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot condition data from long to wide format.

    Args:
        df: DataFrame in long format (condition_category as column)

    Returns:
        DataFrame in wide format (categories as columns)
    """
    if 'condition_category' not in df.columns:
        return df

    # Determine index columns (all except condition_category and Value)
    value_col = 'Value'
    category_col = 'condition_category'

    index_cols = [col for col in df.columns
                  if col not in [value_col, category_col, 'short_desc',
                                'statisticcat_desc', 'unit_desc', 'week_ending']]

    # Filter to valid rows
    df_filtered = df[df[category_col].notna()].copy()

    if df_filtered.empty:
        return df

    # Pivot
    try:
        df_pivot = df_filtered.pivot_table(
            index=index_cols,
            columns=category_col,
            values=value_col,
            aggfunc='first'
        ).reset_index()

        # Fill missing categories with 0
        for cat in ['EXCELLENT', 'GOOD', 'FAIR', 'POOR', 'VERY POOR']:
            if cat not in df_pivot.columns:
                df_pivot[cat] = 0.0

        return df_pivot

    except Exception as e:
        print(f"Warning: Pivot failed: {e}")
        return df


def validate_condition_sum(df: pd.DataFrame, tolerance: float = 2.0) -> pd.DataFrame:
    """
    Validate that condition percentages sum to ~100%.

    Args:
        df: DataFrame with condition columns
        tolerance: Allowed deviation from 100

    Returns:
        DataFrame with validation flag
    """
    categories = ['EXCELLENT', 'GOOD', 'FAIR', 'POOR', 'VERY POOR']

    # Check if all categories present
    present = [cat for cat in categories if cat in df.columns]

    if len(present) < 2:
        # Not enough data to validate
        df['valid'] = True
        return df

    # Calculate sum
    df['total_pct'] = df[present].sum(axis=1)

    # Flag invalid (sum not close to 100)
    df['valid'] = np.abs(df['total_pct'] - 100.0) <= tolerance

    # Log invalid rows
    invalid_count = (~df['valid']).sum()
    if invalid_count > 0:
        print(f"Warning: {invalid_count} rows with invalid percentages (sum != 100%)")

    return df


def get_latest_conditions(
    df: pd.DataFrame,
    commodity: Optional[str] = None
) -> pd.DataFrame:
    """
    Get latest week conditions from DataFrame.

    Args:
        df: DataFrame with condition data
        commodity: Filter to commodity (None for all)

    Returns:
        DataFrame with latest week only
    """
    if df.empty:
        return df

    df_filtered = df.copy()

    # Filter commodity
    if commodity is not None:
        df_filtered = df_filtered[
            df_filtered['commodity_desc'] == commodity
        ]

    # Get latest week
    if 'week_number' in df_filtered.columns:
        latest_week = df_filtered['week_number'].max()
        df_filtered = df_filtered[df_filtered['week_number'] == latest_week]

    return df_filtered


def format_condition_report(df: pd.DataFrame) -> str:
    """
    Format condition data as human-readable report.

    Args:
        df: DataFrame with condition data (wide format)

    Returns:
        Formatted string report
    """
    if df.empty:
        return "No data available"

    lines = []

    categories = ['EXCELLENT', 'GOOD', 'FAIR', 'POOR', 'VERY POOR']

    for _, row in df.iterrows():
        # Header
        commodity = row.get('commodity_desc', 'N/A')
        year = row.get('year', 'N/A')
        week = row.get('week_number', 'N/A')
        state = row.get('state_name', 'NATIONAL')

        lines.append(f"\n{commodity} - {state} - {year} Week #{week}")
        lines.append("-" * 50)

        # Conditions
        for cat in categories:
            if cat in row and pd.notna(row[cat]):
                pct = row[cat]
                lines.append(f"  {cat:12s}: {pct:5.1f}%")

        # Good+Excellent
        if 'good_excellent' in row and pd.notna(row['good_excellent']):
            lines.append(f"\n  → Good+Excellent: {row['good_excellent']:.1f}%")

    return "\n".join(lines)


def main():
    """Test parsing functions."""
    # Sample data
    sample_data = [
        {
            'commodity_desc': 'CORN',
            'year': 2024,
            'reference_period_desc': 'WEEK #32',
            'week_ending': '2024-08-11',
            'state_name': 'IOWA',
            'short_desc': 'CORN - CONDITION, MEASURED IN PCT EXCELLENT',
            'Value': '15',
            'statisticcat_desc': 'CONDITION'
        },
        {
            'commodity_desc': 'CORN',
            'year': 2024,
            'reference_period_desc': 'WEEK #32',
            'week_ending': '2024-08-11',
            'state_name': 'IOWA',
            'short_desc': 'CORN - CONDITION, MEASURED IN PCT GOOD',
            'Value': '56',
            'statisticcat_desc': 'CONDITION'
        },
        {
            'commodity_desc': 'CORN',
            'year': 2024,
            'reference_period_desc': 'WEEK #32',
            'week_ending': '2024-08-11',
            'state_name': 'IOWA',
            'short_desc': 'CORN - CONDITION, MEASURED IN PCT FAIR',
            'Value': '24',
            'statisticcat_desc': 'CONDITION'
        },
        {
            'commodity_desc': 'CORN',
            'year': 2024,
            'reference_period_desc': 'WEEK #32',
            'week_ending': '2024-08-11',
            'state_name': 'IOWA',
            'short_desc': 'CORN - CONDITION, MEASURED IN PCT POOR',
            'Value': '4',
            'statisticcat_desc': 'CONDITION'
        },
        {
            'commodity_desc': 'CORN',
            'year': 2024,
            'reference_period_desc': 'WEEK #32',
            'week_ending': '2024-08-11',
            'state_name': 'IOWA',
            'short_desc': 'CORN - CONDITION, MEASURED IN PCT VERY POOR',
            'Value': '1',
            'statisticcat_desc': 'CONDITION'
        }
    ]

    print("Testing parser...")

    # Parse
    df = parse_api_response(sample_data)
    print(f"\nParsed {len(df)} records")
    print(df[['commodity_desc', 'week_number', 'condition_category', 'Value']].head())

    # Aggregate
    agg = aggregate_conditions(df, by='state', week=32)
    print(f"\nAggregated by state:")
    print(agg)

    # Pivot
    pivoted = pivot_conditions_table(agg)
    print(f"\nPivoted to wide format:")
    print(pivoted)

    # Calculate good+excellent
    with_ge = calculate_good_excellent(pivoted)
    print(f"\nWith Good+Excellent:")
    print(with_ge[['state_name', 'EXCELLENT', 'GOOD', 'good_excellent']])

    # Format report
    report = format_condition_report(with_ge)
    print(f"\nFormatted Report:")
    print(report)


if __name__ == "__main__":
    main()
