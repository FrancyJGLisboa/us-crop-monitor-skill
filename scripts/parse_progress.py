#!/usr/bin/env python3
"""
NASS Crop Progress Data Parser

Parses and transforms NASS crop progress (planting, harvest, etc.) data.

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

from utils.validators import validate_percentage


class ParseError(Exception):
    """Exception for parsing errors."""
    pass


def parse_progress_response(response_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Parse NASS progress API response into DataFrame.

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

        # Extract progress type from short_desc (PLANTED, HARVESTED, etc.)
        if 'short_desc' in df.columns:
            df['progress_type'] = df['short_desc'].apply(extract_progress_type)

        return df

    except Exception as e:
        raise ParseError(f"Failed to parse progress response: {e}")


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


def extract_progress_type(short_desc: str) -> Optional[str]:
    """
    Extract progress type from short description.

    Args:
        short_desc: String like "CORN - PROGRESS, MEASURED IN PCT PLANTED"

    Returns:
        Progress type (PLANTED, HARVESTED, EMERGED, etc.)
    """
    if not isinstance(short_desc, str):
        return None

    short_desc_upper = short_desc.upper()

    # Common progress types
    progress_types = [
        'HARVESTED',
        'PLANTED',
        'EMERGED',
        'SILKING',
        'DOUGH',
        'DENTED',
        'MATURE',
        'BLOOMING',
        'SETTING PODS',
        'DROPPING LEAVES',
        'COLORING',
        'HEADED',
        'BOOTING'
    ]

    for ptype in progress_types:
        if ptype in short_desc_upper:
            return ptype

    return None


def aggregate_progress(
    df: pd.DataFrame,
    by: str = 'national',
    week: Optional[int] = None
) -> pd.DataFrame:
    """
    Aggregate progress data by geographic level.

    Args:
        df: DataFrame with parsed progress data
        by: Aggregation level ('national', 'state')
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
        group_cols = ['commodity_desc', 'year', 'week_number', 'progress_type']
    elif by == 'state':
        group_cols = ['commodity_desc', 'year', 'week_number', 'state_name', 'progress_type']
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


def pivot_progress_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot progress data from long to wide format.

    Args:
        df: DataFrame in long format (progress_type as column)

    Returns:
        DataFrame in wide format (progress types as columns)
    """
    if 'progress_type' not in df.columns:
        return df

    # Determine index columns
    value_col = 'Value'
    category_col = 'progress_type'

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

        # Fill missing columns with NaN (progress types vary by crop and timing)
        return df_pivot

    except Exception as e:
        print(f"Warning: Pivot failed: {e}")
        return df


def get_harvest_progress(
    df: pd.DataFrame,
    commodity: Optional[str] = None,
    latest_only: bool = True
) -> pd.DataFrame:
    """
    Extract harvest progress data.

    Args:
        df: DataFrame with progress data
        commodity: Filter to commodity (None for all)
        latest_only: Return only latest week

    Returns:
        DataFrame with harvest progress
    """
    if df.empty:
        return df

    df_filtered = df.copy()

    # Filter commodity
    if commodity is not None:
        df_filtered = df_filtered[
            df_filtered['commodity_desc'] == commodity
        ]

    # Filter to harvested data
    if 'progress_type' in df_filtered.columns:
        df_filtered = df_filtered[
            df_filtered['progress_type'] == 'HARVESTED'
        ]

    # Get latest week only
    if latest_only and 'week_number' in df_filtered.columns:
        latest_week = df_filtered['week_number'].max()
        df_filtered = df_filtered[df_filtered['week_number'] == latest_week]

    return df_filtered


def get_planting_progress(
    df: pd.DataFrame,
    commodity: Optional[str] = None,
    latest_only: bool = True
) -> pd.DataFrame:
    """
    Extract planting progress data.

    Args:
        df: DataFrame with progress data
        commodity: Filter to commodity (None for all)
        latest_only: Return only latest week

    Returns:
        DataFrame with planting progress
    """
    if df.empty:
        return df

    df_filtered = df.copy()

    # Filter commodity
    if commodity is not None:
        df_filtered = df_filtered[
            df_filtered['commodity_desc'] == commodity
        ]

    # Filter to planted data
    if 'progress_type' in df_filtered.columns:
        df_filtered = df_filtered[
            df_filtered['progress_type'] == 'PLANTED'
        ]

    # Get latest week only
    if latest_only and 'week_number' in df_filtered.columns:
        latest_week = df_filtered['week_number'].max()
        df_filtered = df_filtered[df_filtered['week_number'] == latest_week]

    return df_filtered


def format_progress_report(df: pd.DataFrame, progress_type: str = 'HARVESTED') -> str:
    """
    Format progress data as human-readable report.

    Args:
        df: DataFrame with progress data
        progress_type: Type of progress to report

    Returns:
        Formatted string report
    """
    if df.empty:
        return "No data available"

    lines = []

    for _, row in df.iterrows():
        # Header
        commodity = row.get('commodity_desc', 'N/A')
        year = row.get('year', 'N/A')
        week = row.get('week_number', 'N/A')
        state = row.get('state_name', 'NATIONAL')

        lines.append(f"\n{commodity} - {state} - {year} Week #{week}")
        lines.append("-" * 50)

        # Progress value
        value = row.get('Value', row.get(progress_type, 'N/A'))
        lines.append(f"  {progress_type}: {value}%")

    return "\n".join(lines)


def main():
    """Test parsing functions."""
    # Sample progress data
    sample_data = [
        {
            'commodity_desc': 'CORN',
            'year': 2025,
            'reference_period_desc': 'WEEK #39',
            'week_ending': '2025-09-28',
            'state_name': 'IOWA',
            'short_desc': 'CORN, GRAIN - PROGRESS, MEASURED IN PCT HARVESTED',
            'Value': '15',
            'statisticcat_desc': 'PROGRESS'
        },
        {
            'commodity_desc': 'CORN',
            'year': 2025,
            'reference_period_desc': 'WEEK #39',
            'week_ending': '2025-09-28',
            'state_name': 'ILLINOIS',
            'short_desc': 'CORN, GRAIN - PROGRESS, MEASURED IN PCT HARVESTED',
            'Value': '21',
            'statisticcat_desc': 'PROGRESS'
        }
    ]

    print("Testing progress parser...")

    # Parse
    df = parse_progress_response(sample_data)
    print(f"\nParsed {len(df)} records")
    print(df[['commodity_desc', 'week_number', 'progress_type', 'Value']].head())

    # Get harvest progress
    harvest = get_harvest_progress(df)
    print(f"\nHarvest progress:")
    print(harvest[['state_name', 'Value']])

    # Format report
    report = format_progress_report(harvest)
    print(f"\nFormatted Report:")
    print(report)


if __name__ == "__main__":
    main()
