#!/usr/bin/env python3
"""
Crop Condition Analysis Functions

Implements the 6 main analyses for crop monitoring.

Author: Agent Creator
Version: 1.0.0
"""

import sys
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'utils'))

from fetch_nass import NassApiClient, DataNotFoundError
from parse_conditions import (
    parse_api_response, aggregate_conditions,
    pivot_conditions_table, calculate_good_excellent,
    format_condition_report
)

# Import validation system
from utils.data_validator import DataValidator, ValidationReport
from utils.temporal_validator import validate_temporal_consistency, validate_year_consistency
from utils.completeness_validator import validate_completeness, validate_percentage_sum
from utils.anomaly_detector import detect_anomalies, detect_week_over_week_anomalies, detect_year_over_year_anomalies
from utils.validation_formatter import format_validation_section

# Import year detection helpers
from utils.helpers import (
    get_current_crop_year, get_crop_year_with_fallback,
    should_try_previous_year, format_year_message
)

# Import new parsers for expanded metrics
from parse_progress import parse_progress_response, get_harvest_progress, get_planting_progress
from parse_yield import parse_yield_response, calculate_yield_change
from parse_production import parse_production_response, calculate_production_change
from parse_area import parse_area_response, compare_planted_vs_harvested, calculate_area_change


class AnalysisError(Exception):
    """Exception for analysis errors."""
    pass


def current_condition_report(
    commodity: str,
    year: Optional[int] = None,
    week: Optional[int] = None,
    level: str = 'national',
    state: Optional[str] = None,
    client: Optional[NassApiClient] = None
) -> Dict:
    """
    Generate current condition report.

    Args:
        commodity: Crop name
        year: Year (None for current year with auto-fallback)
        week: Week number (None for latest)
        level: Geographic level ('national' or 'state')
        state: Specific state (if level='state')
        client: API client (None to create new)

    Returns:
        Dictionary with report data including year_info
    """
    if client is None:
        client = NassApiClient()

    # Auto-detect year if not specified
    year_requested = year
    if year is None:
        year = get_current_crop_year()

    # Try to get data for requested year, fallback to previous if needed
    year_used = year
    fallback_attempted = False

    # Get latest week if not specified
    week_for_year = client.get_latest_week(commodity, year)

    # If no data for current year and we should try previous year
    if week_for_year is None and should_try_previous_year(year):
        fallback_year = year - 1
        week_for_year = client.get_latest_week(commodity, fallback_year)
        if week_for_year is not None:
            year_used = fallback_year
            fallback_attempted = True
            import logging
            logging.info(f"No data for {year}, using {fallback_year} instead")

    if week_for_year is None:
        raise AnalysisError(f"No data available for {commodity} {year}")

    # Use specific week if provided, otherwise use latest found
    if week is None:
        week = week_for_year

    # Fetch data WITH metadata
    try:
        agg_level = 'STATE' if level == 'state' else 'NATIONAL'
        result = client.get_crop_conditions_with_metadata(
            commodity=commodity,
            year=year_used,  # Use the year that actually has data
            week=week,
            state=state,
            agg_level=agg_level
        )
        data = result['data']
        metadata = result['metadata']
    except DataNotFoundError as e:
        raise AnalysisError(str(e))

    # Parse and aggregate
    df = parse_api_response(data)
    df_pivot = pivot_conditions_table(df)
    df_with_ge = calculate_good_excellent(df_pivot)

    # Create year info message
    year_info = format_year_message(
        year_used,
        year_requested,
        "auto-detected current year" if year_requested is None else "requested year"
    )

    # Run validations
    report = ValidationReport()
    report.data_metadata = metadata

    validator = DataValidator()
    config = validator.config

    validate_temporal_consistency(df_with_ge, report, config)
    validate_year_consistency(year_used, df_with_ge, report, config)
    validate_completeness(df_with_ge, report, config)
    validate_percentage_sum(df_with_ge, report, tolerance=2.0)
    detect_anomalies(df_with_ge, report, config)

    # National summary
    if level == 'national':
        national = df_with_ge[df_with_ge.get('state_name', None).isna() |
                              (df_with_ge.get('agg_level_desc', '') == 'NATIONAL')]

        if national.empty:
            # Calculate from state data
            categories = ['EXCELLENT', 'GOOD', 'FAIR', 'POOR', 'VERY POOR']
            state_data = df_with_ge[df_with_ge.get('state_name', None).notna()]

            if not state_data.empty:
                national_summary = {cat: state_data[cat].mean() for cat in categories if cat in state_data.columns}
                national_summary['good_excellent'] = national_summary.get('GOOD', 0) + national_summary.get('EXCELLENT', 0)
            else:
                raise AnalysisError("No national or state data available")
        else:
            national_summary = national.iloc[0].to_dict()

        # Top states
        state_data = df_with_ge[df_with_ge.get('state_name', None).notna()]
        if not state_data.empty:
            top_states = state_data.nlargest(5, 'good_excellent')[
                ['state_name', 'good_excellent']
            ].to_dict('records')
        else:
            top_states = []

        return {
            'commodity': commodity,
            'year': year_used,
            'year_requested': year_requested,
            'year_info': year_info,
            'fallback_used': fallback_attempted,
            'week': week,
            'level': 'NATIONAL',
            'conditions': national_summary,
            'top_states': top_states,
            'validation': {
                'report': report,
                'summary': report.get_summary_line(),
                'formatted': format_validation_section(report, config),
                'should_block': report.should_block(),
                'blocking_message': report.get_blocking_message() if report.should_block() else None
            }
        }

    else:  # state level
        if state:
            state_row = df_with_ge[df_with_ge['state_name'] == state.upper()]
            if state_row.empty:
                raise AnalysisError(f"No data for state {state}")

            return {
                'commodity': commodity,
                'year': year_used,
                'year_requested': year_requested,
                'year_info': year_info,
                'fallback_used': fallback_attempted,
                'week': week,
                'level': 'STATE',
                'state': state,
                'conditions': state_row.iloc[0].to_dict(),
                'validation': {
                    'report': report,
                    'summary': report.get_summary_line(),
                    'formatted': format_validation_section(report, config),
                    'should_block': report.should_block(),
                    'blocking_message': report.get_blocking_message() if report.should_block() else None
                }
            }
        else:
            # All states
            return {
                'commodity': commodity,
                'year': year_used,
                'year_requested': year_requested,
                'year_info': year_info,
                'fallback_used': fallback_attempted,
                'week': week,
                'level': 'STATE',
                'states': df_with_ge.to_dict('records'),
                'validation': {
                    'report': report,
                    'summary': report.get_summary_line(),
                    'formatted': format_validation_section(report, config),
                    'should_block': report.should_block(),
                    'blocking_message': report.get_blocking_message() if report.should_block() else None
                }
            }


def week_over_week_comparison(
    commodity: str,
    year: Optional[int] = None,
    current_week: Optional[int] = None,
    previous_week: Optional[int] = None,
    client: Optional[NassApiClient] = None
) -> Dict:
    """
    Compare current week vs previous week.

    Args:
        commodity: Crop name
        year: Year (None for current year with auto-fallback)
        current_week: Current week (None for latest)
        previous_week: Previous week (None for current-1)
        client: API client

    Returns:
        Dictionary with comparison data including year_info
    """
    if client is None:
        client = NassApiClient()

    # Auto-detect year if not specified
    year_requested = year
    if year is None:
        year = get_current_crop_year()

    # Try to get data for requested year, fallback to previous if needed
    year_used = year
    fallback_attempted = False

    # Get current week
    if current_week is None:
        current_week = client.get_latest_week(commodity, year)

        # If no data for current year, try previous year
        if current_week is None and should_try_previous_year(year):
            fallback_year = year - 1
            current_week = client.get_latest_week(commodity, fallback_year)
            if current_week is not None:
                year_used = fallback_year
                fallback_attempted = True
                import logging
                logging.info(f"No data for {year}, using {fallback_year} instead")

        if current_week is None:
            raise AnalysisError(f"No data available for {commodity} {year}")

    # Previous week
    if previous_week is None:
        previous_week = current_week - 1

    # Create year info message
    year_info = format_year_message(
        year_used,
        year_requested,
        "auto-detected current year" if year_requested is None else "requested year"
    )

    # Fetch both weeks WITH metadata
    try:
        current_result = client.get_crop_conditions_with_metadata(commodity, year_used, current_week, agg_level='STATE')
        previous_result = client.get_crop_conditions_with_metadata(commodity, year_used, previous_week, agg_level='STATE')

        current_data = current_result['data']
        previous_data = previous_result['data']
        metadata = current_result['metadata']
    except DataNotFoundError as e:
        raise AnalysisError(f"Could not fetch data: {e}")

    # Parse
    df_current = parse_api_response(current_data)
    df_previous = parse_api_response(previous_data)

    # Aggregate and pivot
    df_current_pivot = calculate_good_excellent(pivot_conditions_table(df_current))
    df_previous_pivot = calculate_good_excellent(pivot_conditions_table(df_previous))

    # Run validations
    report = ValidationReport()
    report.data_metadata = metadata

    validator = DataValidator()
    config = validator.config

    validate_temporal_consistency(df_current_pivot, report, config)
    validate_completeness(df_current_pivot, report, config)
    validate_percentage_sum(df_current_pivot, report, tolerance=2.0)
    detect_week_over_week_anomalies(df_current_pivot, df_previous_pivot, report, config)

    # Merge on state
    merged = df_current_pivot.merge(
        df_previous_pivot[['state_name', 'good_excellent']],
        on='state_name',
        how='inner',
        suffixes=('_current', '_previous')
    )

    # Calculate delta
    merged['delta'] = merged['good_excellent_current'] - merged['good_excellent_previous']

    # National average
    national_current = merged['good_excellent_current'].mean()
    national_previous = merged['good_excellent_previous'].mean()
    national_delta = national_current - national_previous

    # Top improvements and deteriorations
    improvements = merged.nlargest(5, 'delta')[
        ['state_name', 'good_excellent_current', 'good_excellent_previous', 'delta']
    ].to_dict('records')

    deteriorations = merged.nsmallest(5, 'delta')[
        ['state_name', 'good_excellent_current', 'good_excellent_previous', 'delta']
    ].to_dict('records')

    return {
        'commodity': commodity,
        'year': year_used,
        'year_requested': year_requested,
        'year_info': year_info,
        'fallback_used': fallback_attempted,
        'current_week': current_week,
        'previous_week': previous_week,
        'national': {
            'current': national_current,
            'previous': national_previous,
            'delta': national_delta
        },
        'top_improvements': improvements,
        'top_deteriorations': deteriorations,
        'all_states': merged.to_dict('records'),
        'validation': {
            'report': report,
            'summary': report.get_summary_line(),
            'formatted': format_validation_section(report, config),
            'should_block': report.should_block(),
            'blocking_message': report.get_blocking_message() if report.should_block() else None
        }
    }


def year_over_year_comparison(
    commodity: str,
    current_year: int,
    previous_year: Optional[int] = None,
    week: Optional[int] = None,
    client: Optional[NassApiClient] = None
) -> Dict:
    """
    Compare current year vs previous year.

    Args:
        commodity: Crop name
        current_year: Current year
        previous_year: Previous year (None for current-1)
        week: Week number to compare (None for latest)
        client: API client

    Returns:
        Dictionary with YoY comparison
    """
    if client is None:
        client = NassApiClient()

    if previous_year is None:
        previous_year = current_year - 1

    # Get week
    if week is None:
        week = client.get_latest_week(commodity, current_year)
        if week is None:
            raise AnalysisError(f"No data for {commodity} {current_year}")

    # Fetch both years WITH metadata
    try:
        current_result = client.get_crop_conditions_with_metadata(commodity, current_year, week, agg_level='STATE')
        previous_result = client.get_crop_conditions_with_metadata(commodity, previous_year, week, agg_level='STATE')

        current_data = current_result['data']
        previous_data = previous_result['data']
        metadata = current_result['metadata']
    except DataNotFoundError as e:
        raise AnalysisError(f"Could not fetch data: {e}")

    # Parse
    df_current = calculate_good_excellent(pivot_conditions_table(parse_api_response(current_data)))
    df_previous = calculate_good_excellent(pivot_conditions_table(parse_api_response(previous_data)))

    # Run validations
    report = ValidationReport()
    report.data_metadata = metadata

    validator = DataValidator()
    config = validator.config

    validate_temporal_consistency(df_current, report, config)
    validate_year_consistency(current_year, df_current, report, config)
    validate_completeness(df_current, report, config)
    validate_percentage_sum(df_current, report, tolerance=2.0)
    detect_year_over_year_anomalies(df_current, df_previous, report, config)

    # Merge
    merged = df_current.merge(
        df_previous[['state_name', 'good_excellent', 'EXCELLENT', 'GOOD', 'FAIR', 'POOR', 'VERY POOR']],
        on='state_name',
        how='inner',
        suffixes=('_current', '_previous')
    )

    # Calculate deltas
    merged['delta_ge'] = merged['good_excellent_current'] - merged['good_excellent_previous']

    # National
    categories = ['EXCELLENT', 'GOOD', 'FAIR', 'POOR', 'VERY POOR']
    national_current = {cat: merged[f'{cat}_current'].mean() for cat in categories}
    national_previous = {cat: merged[f'{cat}_previous'].mean() for cat in categories}
    national_current['good_excellent'] = merged['good_excellent_current'].mean()
    national_previous['good_excellent'] = merged['good_excellent_previous'].mean()

    national_delta = {
        cat: national_current[cat] - national_previous[cat]
        for cat in categories + ['good_excellent']
    }

    # Top changes
    improvements = merged.nlargest(5, 'delta_ge')[
        ['state_name', 'good_excellent_current', 'good_excellent_previous', 'delta_ge']
    ].to_dict('records')

    deteriorations = merged.nsmallest(5, 'delta_ge')[
        ['state_name', 'good_excellent_current', 'good_excellent_previous', 'delta_ge']
    ].to_dict('records')

    return {
        'commodity': commodity,
        'current_year': current_year,
        'previous_year': previous_year,
        'week': week,
        'national_current': national_current,
        'national_previous': national_previous,
        'national_delta': national_delta,
        'top_improvements': improvements,
        'top_deteriorations': deteriorations,
        'validation': {
            'report': report,
            'summary': report.get_summary_line(),
            'formatted': format_validation_section(report, config),
            'should_block': report.should_block(),
            'blocking_message': report.get_blocking_message() if report.should_block() else None
        }
    }


def state_rankings(
    commodity: str,
    year: Optional[int] = None,
    week: Optional[int] = None,
    client: Optional[NassApiClient] = None
) -> Dict:
    """
    Rank states by crop condition.

    Args:
        commodity: Crop name
        year: Year (None for current year with auto-fallback)
        week: Week number (None for latest)
        client: API client

    Returns:
        Dictionary with rankings including year_info
    """
    if client is None:
        client = NassApiClient()

    # Auto-detect year if not specified
    year_requested = year
    if year is None:
        year = get_current_crop_year()

    # Try to get data for requested year, fallback to previous if needed
    year_used = year
    fallback_attempted = False

    if week is None:
        week = client.get_latest_week(commodity, year)

        # If no data for current year, try previous year
        if week is None and should_try_previous_year(year):
            fallback_year = year - 1
            week = client.get_latest_week(commodity, fallback_year)
            if week is not None:
                year_used = fallback_year
                fallback_attempted = True
                import logging
                logging.info(f"No data for {year}, using {fallback_year} instead")

        if week is None:
            raise AnalysisError(f"No data available for {commodity} {year}")

    # Create year info message
    year_info = format_year_message(
        year_used,
        year_requested,
        "auto-detected current year" if year_requested is None else "requested year"
    )

    # Fetch state data WITH metadata
    try:
        result = client.get_crop_conditions_with_metadata(commodity, year_used, week, agg_level='STATE')
        data = result['data']
        metadata = result['metadata']
    except DataNotFoundError as e:
        raise AnalysisError(str(e))

    # Parse
    df = calculate_good_excellent(pivot_conditions_table(parse_api_response(data)))

    # Run validations
    report = ValidationReport()
    report.data_metadata = metadata

    validator = DataValidator()
    config = validator.config

    validate_temporal_consistency(df, report, config)
    validate_year_consistency(year_used, df, report, config)
    validate_completeness(df, report, config)
    validate_percentage_sum(df, report, tolerance=2.0)
    detect_anomalies(df, report, config)

    # Filter to states only
    df_states = df[df.get('state_name', None).notna()].copy()

    if df_states.empty:
        raise AnalysisError("No state data available")

    # Sort by good_excellent
    df_states = df_states.sort_values('good_excellent', ascending=False).reset_index(drop=True)
    df_states['rank'] = range(1, len(df_states) + 1)

    # Format output
    rankings = df_states[['rank', 'state_name', 'good_excellent', 'EXCELLENT', 'GOOD', 'FAIR', 'POOR', 'VERY POOR']].to_dict('records')

    return {
        'commodity': commodity,
        'year': year_used,
        'year_requested': year_requested,
        'year_info': year_info,
        'fallback_used': fallback_attempted,
        'week': week,
        'rankings': rankings,
        'top_10': rankings[:10],
        'bottom_10': rankings[-10:],
        'validation': {
            'report': report,
            'summary': report.get_summary_line(),
            'formatted': format_validation_section(report, config),
            'should_block': report.should_block(),
            'blocking_message': report.get_blocking_message() if report.should_block() else None
        }
    }


def season_trend_analysis(
    commodity: str,
    year: Optional[int] = None,
    client: Optional[NassApiClient] = None
) -> Dict:
    """
    Analyze trend across entire season.

    Args:
        commodity: Crop name
        year: Year (None for current year with auto-fallback)
        client: API client

    Returns:
        Dictionary with trend analysis including year_info
    """
    if client is None:
        client = NassApiClient()

    # Auto-detect year if not specified
    year_requested = year
    if year is None:
        year = get_current_crop_year()

    # Try to get data for requested year, fallback to previous if needed
    year_used = year
    fallback_attempted = False

    # Fetch all weeks for the year WITH metadata
    try:
        result = client.get_crop_conditions_with_metadata(commodity, year, agg_level='NATIONAL')
        data = result['data']
        metadata = result['metadata']
    except DataNotFoundError:
        # Try previous year if auto-detecting and should fallback
        if should_try_previous_year(year):
            fallback_year = year - 1
            try:
                result = client.get_crop_conditions_with_metadata(commodity, fallback_year, agg_level='NATIONAL')
                data = result['data']
                metadata = result['metadata']
                year_used = fallback_year
                fallback_attempted = True
                import logging
                logging.info(f"No data for {year}, using {fallback_year} instead")
            except DataNotFoundError as e:
                raise AnalysisError(str(e))
        else:
            raise AnalysisError(f"No data available for {commodity} {year}")

    # Create year info message
    year_info = format_year_message(
        year_used,
        year_requested,
        "auto-detected current year" if year_requested is None else "requested year"
    )

    # Parse
    df = parse_api_response(data)

    # Run validations on full dataset
    df_for_validation = calculate_good_excellent(pivot_conditions_table(df))

    report = ValidationReport()
    report.data_metadata = metadata

    validator = DataValidator()
    config = validator.config

    validate_temporal_consistency(df_for_validation, report, config)
    validate_year_consistency(year_used, df_for_validation, report, config)
    validate_completeness(df_for_validation, report, config)

    # Get unique weeks
    weeks = sorted(df['week_number'].unique())

    if len(weeks) < 2:
        raise AnalysisError("Not enough weeks for trend analysis")

    # Calculate G+E for each week
    weekly_data = []

    for week in weeks:
        df_week = df[df['week_number'] == week]
        df_pivot = pivot_conditions_table(df_week)
        df_ge = calculate_good_excellent(df_pivot)

        # National average
        ge_value = df_ge['good_excellent'].mean()

        weekly_data.append({
            'week': week,
            'good_excellent': ge_value
        })

    df_trend = pd.DataFrame(weekly_data)

    # Find peak and valley
    peak_idx = df_trend['good_excellent'].idxmax()
    valley_idx = df_trend['good_excellent'].idxmin()

    peak = df_trend.loc[peak_idx].to_dict()
    valley = df_trend.loc[valley_idx].to_dict()

    # Calculate trend (linear regression)
    from scipy import stats
    slope, intercept, r_value, p_value, std_err = stats.linregress(df_trend['week'], df_trend['good_excellent'])

    trend_direction = 'IMPROVING' if slope > 0 else 'DETERIORATING' if slope < 0 else 'STABLE'

    return {
        'commodity': commodity,
        'year': year_used,
        'year_requested': year_requested,
        'year_info': year_info,
        'fallback_used': fallback_attempted,
        'weeks_available': weeks,
        'weekly_data': weekly_data,
        'peak': peak,
        'valley': valley,
        'amplitude': peak['good_excellent'] - valley['good_excellent'],
        'current': weekly_data[-1] if weekly_data else None,
        'trend_slope': slope,
        'trend_direction': trend_direction,
        'r_squared': r_value ** 2,
        'validation': {
            'report': report,
            'summary': report.get_summary_line(),
            'formatted': format_validation_section(report, config),
            'should_block': report.should_block(),
            'blocking_message': report.get_blocking_message() if report.should_block() else None
        }
    }


def multi_crop_dashboard(
    crops: List[str] = ['CORN', 'SOYBEANS', 'WHEAT'],
    year: Optional[int] = None,
    week: Optional[int] = None,
    client: Optional[NassApiClient] = None
) -> Dict:
    """
    Generate multi-crop dashboard.

    Args:
        crops: List of commodity names
        year: Year (None for current)
        week: Week (None for latest)
        client: API client

    Returns:
        Dictionary with dashboard data
    """
    if client is None:
        client = NassApiClient()

    if year is None:
        from datetime import datetime
        year = datetime.now().year

    dashboard_data = {}
    all_validations = {}  # Collect validations from all crops

    for commodity in crops:
        try:
            # Current conditions
            current = current_condition_report(commodity, year, week, client=client)

            # WoW if available
            try:
                wow = week_over_week_comparison(commodity, year, client=client)
                wow_delta = wow['national']['delta']
            except AnalysisError:
                wow_delta = None

            # YoY if available
            try:
                yoy = year_over_year_comparison(commodity, year, client=client)
                yoy_delta = yoy['national_delta']['good_excellent']
            except AnalysisError:
                yoy_delta = None

            # Top 3 states
            top_states = current.get('top_states', [])[:3]

            # Extract validation from current conditions
            validation = current.get('validation', {})

            dashboard_data[commodity] = {
                'good_excellent': current['conditions'].get('good_excellent'),
                'week': current['week'],
                'wow_delta': wow_delta,
                'yoy_delta': yoy_delta,
                'top_states': top_states,
                'validation_summary': validation.get('summary', '')
            }

            # Store full validation for this crop
            all_validations[commodity] = validation

        except AnalysisError as e:
            dashboard_data[commodity] = {
                'error': str(e)
            }

    # Create consolidated validation report
    consolidated_report = ValidationReport()
    for commodity, validation in all_validations.items():
        if 'report' in validation:
            # Add all results from this crop's validation
            for result in validation['report'].results:
                # Add commodity context to the result
                result.details = result.details or {}
                result.details['commodity'] = commodity
                consolidated_report.results.append(result)

    validator = DataValidator()
    config = validator.config

    return {
        'year': year,
        'crops': dashboard_data,
        'validation': {
            'report': consolidated_report,  # Main report (for consistency with other functions)
            'consolidated_report': consolidated_report,  # Alias for clarity
            'summary': consolidated_report.get_summary_line(),
            'formatted': format_validation_section(consolidated_report, config),
            'should_block': consolidated_report.should_block(),
            'blocking_message': consolidated_report.get_blocking_message() if consolidated_report.should_block() else None,
            'by_crop': all_validations
        }
    }


# ============================================================================
# PROGRESS ANALYSIS FUNCTIONS
# ============================================================================

def harvest_progress_report(
    commodity: str,
    year: Optional[int] = None,
    week: Optional[int] = None,
    level: str = 'national',
    state: Optional[str] = None,
    client: Optional[NassApiClient] = None
) -> Dict:
    """
    Generate harvest progress report.

    Args:
        commodity: Crop name
        year: Year (None for current year with auto-fallback)
        week: Week number (None for latest)
        level: Geographic level ('national' or 'state')
        state: Specific state (if level='state')
        client: API client

    Returns:
        Dictionary with harvest progress data
    """
    if client is None:
        client = NassApiClient()

    # Auto-detect year if not specified
    year_requested = year
    if year is None:
        year = get_current_crop_year()

    year_used = year
    fallback_attempted = False

    # Fetch progress data
    try:
        agg_level = 'STATE' if level == 'state' else 'NATIONAL'
        result = client.get_crop_progress(
            commodity=commodity,
            year=year,
            week=week,
            state=state,
            agg_level=agg_level
        )
        data = result['data']
        metadata = result['metadata']
    except DataNotFoundError:
        # Try previous year if should fallback
        if should_try_previous_year(year):
            fallback_year = year - 1
            try:
                result = client.get_crop_progress(
                    commodity=commodity,
                    year=fallback_year,
                    week=week,
                    state=state,
                    agg_level=agg_level
                )
                data = result['data']
                metadata = result['metadata']
                year_used = fallback_year
                fallback_attempted = True
                import logging
                logging.info(f"No data for {year}, using {fallback_year} instead")
            except DataNotFoundError as e:
                raise AnalysisError(str(e))
        else:
            raise AnalysisError(f"No progress data available for {commodity} {year}")

    # Create year info message
    year_info = format_year_message(
        year_used,
        year_requested,
        "auto-detected current year" if year_requested is None else "requested year"
    )

    # Parse progress data
    df = parse_progress_response(data)

    # Get harvest progress specifically
    df_harvest = get_harvest_progress(df, commodity=commodity, latest_only=(week is None))

    if df_harvest.empty:
        raise AnalysisError(f"No harvest progress data available for {commodity}")

    # Extract latest week if not specified
    if week is None and 'week_number' in df_harvest.columns:
        week = df_harvest['week_number'].max()

    # Aggregate results
    if level == 'national':
        national_pct = df_harvest['Value'].mean() if not df_harvest.empty else 0

        # Get state data for rankings
        state_data = df_harvest.sort_values('Value', ascending=False)
        top_states = state_data.head(5)[['state_name', 'Value']].to_dict('records')

        return {
            'commodity': commodity,
            'year': year_used,
            'year_requested': year_requested,
            'year_info': year_info,
            'fallback_used': fallback_attempted,
            'week': week,
            'metric_type': 'HARVEST_PROGRESS',
            'level': 'NATIONAL',
            'percent_harvested': national_pct,
            'top_states': top_states
        }
    else:  # state level
        if state:
            state_row = df_harvest[df_harvest['state_name'] == state.upper()]
            if state_row.empty:
                raise AnalysisError(f"No data for state {state}")

            return {
                'commodity': commodity,
                'year': year_used,
                'year_requested': year_requested,
                'year_info': year_info,
                'fallback_used': fallback_attempted,
                'week': week,
                'metric_type': 'HARVEST_PROGRESS',
                'level': 'STATE',
                'state': state,
                'percent_harvested': state_row.iloc[0]['Value']
            }
        else:
            # All states
            return {
                'commodity': commodity,
                'year': year_used,
                'year_requested': year_requested,
                'year_info': year_info,
                'fallback_used': fallback_attempted,
                'week': week,
                'metric_type': 'HARVEST_PROGRESS',
                'level': 'STATE',
                'states': df_harvest.to_dict('records')
            }


def planting_progress_report(
    commodity: str,
    year: Optional[int] = None,
    week: Optional[int] = None,
    level: str = 'national',
    state: Optional[str] = None,
    client: Optional[NassApiClient] = None
) -> Dict:
    """
    Generate planting progress report.

    Args:
        commodity: Crop name
        year: Year (None for current year with auto-fallback)
        week: Week number (None for latest)
        level: Geographic level ('national' or 'state')
        state: Specific state (if level='state')
        client: API client

    Returns:
        Dictionary with planting progress data
    """
    if client is None:
        client = NassApiClient()

    # Auto-detect year if not specified
    year_requested = year
    if year is None:
        year = get_current_crop_year()

    year_used = year
    fallback_attempted = False

    # Fetch progress data
    try:
        agg_level = 'STATE' if level == 'state' else 'NATIONAL'
        result = client.get_crop_progress(
            commodity=commodity,
            year=year,
            week=week,
            state=state,
            agg_level=agg_level
        )
        data = result['data']
        metadata = result['metadata']
    except DataNotFoundError:
        # Try previous year if should fallback
        if should_try_previous_year(year):
            fallback_year = year - 1
            try:
                result = client.get_crop_progress(
                    commodity=commodity,
                    year=fallback_year,
                    week=week,
                    state=state,
                    agg_level=agg_level
                )
                data = result['data']
                metadata = result['metadata']
                year_used = fallback_year
                fallback_attempted = True
                import logging
                logging.info(f"No data for {year}, using {fallback_year} instead")
            except DataNotFoundError as e:
                raise AnalysisError(str(e))
        else:
            raise AnalysisError(f"No progress data available for {commodity} {year}")

    # Create year info message
    year_info = format_year_message(
        year_used,
        year_requested,
        "auto-detected current year" if year_requested is None else "requested year"
    )

    # Parse progress data
    df = parse_progress_response(data)

    # Get planting progress specifically
    df_planting = get_planting_progress(df, commodity=commodity, latest_only=(week is None))

    if df_planting.empty:
        raise AnalysisError(f"No planting progress data available for {commodity}")

    # Extract latest week if not specified
    if week is None and 'week_number' in df_planting.columns:
        week = df_planting['week_number'].max()

    # Aggregate results
    if level == 'national':
        national_pct = df_planting['Value'].mean() if not df_planting.empty else 0

        # Get state data for rankings
        state_data = df_planting.sort_values('Value', ascending=False)
        top_states = state_data.head(5)[['state_name', 'Value']].to_dict('records')

        return {
            'commodity': commodity,
            'year': year_used,
            'year_requested': year_requested,
            'year_info': year_info,
            'fallback_used': fallback_attempted,
            'week': week,
            'metric_type': 'PLANTING_PROGRESS',
            'level': 'NATIONAL',
            'percent_planted': national_pct,
            'top_states': top_states
        }
    else:  # state level
        if state:
            state_row = df_planting[df_planting['state_name'] == state.upper()]
            if state_row.empty:
                raise AnalysisError(f"No data for state {state}")

            return {
                'commodity': commodity,
                'year': year_used,
                'year_requested': year_requested,
                'year_info': year_info,
                'fallback_used': fallback_attempted,
                'week': week,
                'metric_type': 'PLANTING_PROGRESS',
                'level': 'STATE',
                'state': state,
                'percent_planted': state_row.iloc[0]['Value']
            }
        else:
            # All states
            return {
                'commodity': commodity,
                'year': year_used,
                'year_requested': year_requested,
                'year_info': year_info,
                'fallback_used': fallback_attempted,
                'week': week,
                'metric_type': 'PLANTING_PROGRESS',
                'level': 'STATE',
                'states': df_planting.to_dict('records')
            }


# ============================================================================
# YIELD & PRODUCTION ANALYSIS FUNCTIONS
# ============================================================================

def yield_analysis(
    commodity: str,
    year: Optional[int] = None,
    compare_previous: bool = True,
    level: str = 'national',
    state: Optional[str] = None,
    client: Optional[NassApiClient] = None
) -> Dict:
    """
    Analyze crop yield estimates.

    Args:
        commodity: Crop name
        year: Year (None for current year with auto-fallback)
        compare_previous: Whether to compare with previous year
        level: Geographic level ('national' or 'state')
        state: Specific state (if level='state')
        client: API client

    Returns:
        Dictionary with yield analysis
    """
    if client is None:
        client = NassApiClient()

    # Auto-detect year if not specified
    year_requested = year
    if year is None:
        year = get_current_crop_year()

    year_used = year
    fallback_attempted = False

    # Fetch yield data
    try:
        agg_level = 'STATE' if level == 'state' else 'NATIONAL'
        result = client.get_crop_yield(
            commodity=commodity,
            year=year,
            state=state,
            agg_level=agg_level
        )
        data = result['data']
        metadata = result['metadata']
    except DataNotFoundError:
        # Try previous year if should fallback
        if should_try_previous_year(year):
            fallback_year = year - 1
            try:
                result = client.get_crop_yield(
                    commodity=commodity,
                    year=fallback_year,
                    state=state,
                    agg_level=agg_level
                )
                data = result['data']
                metadata = result['metadata']
                year_used = fallback_year
                fallback_attempted = True
                import logging
                logging.info(f"No data for {year}, using {fallback_year} instead")
            except DataNotFoundError as e:
                raise AnalysisError(str(e))
        else:
            raise AnalysisError(f"No yield data available for {commodity} {year}")

    # Create year info message
    year_info = format_year_message(
        year_used,
        year_requested,
        "auto-detected current year" if year_requested is None else "requested year"
    )

    # Parse yield data
    df = parse_yield_response(data)

    # Compare with previous year if requested
    comparison_data = None
    if compare_previous:
        previous_year = year_used - 1
        try:
            prev_result = client.get_crop_yield(
                commodity=commodity,
                year=previous_year,
                state=state,
                agg_level=agg_level
            )
            df_prev = parse_yield_response(prev_result['data'])

            # Calculate changes
            df_comparison = calculate_yield_change(
                pd.concat([df, df_prev]),
                year_used,
                previous_year
            )

            if not df_comparison.empty:
                comparison_data = {
                    'previous_year': previous_year,
                    'states': df_comparison.to_dict('records')
                }
        except (DataNotFoundError, AnalysisError):
            pass  # Comparison optional

    if level == 'national':
        national_yield = df['yield_bu_per_acre'].mean() if not df.empty else 0

        return {
            'commodity': commodity,
            'year': year_used,
            'year_requested': year_requested,
            'year_info': year_info,
            'fallback_used': fallback_attempted,
            'metric_type': 'YIELD',
            'level': 'NATIONAL',
            'yield_bu_per_acre': national_yield,
            'comparison': comparison_data
        }
    else:
        return {
            'commodity': commodity,
            'year': year_used,
            'year_requested': year_requested,
            'year_info': year_info,
            'fallback_used': fallback_attempted,
            'metric_type': 'YIELD',
            'level': 'STATE',
            'states': df.to_dict('records'),
            'comparison': comparison_data
        }


def production_analysis(
    commodity: str,
    year: Optional[int] = None,
    compare_previous: bool = True,
    level: str = 'national',
    state: Optional[str] = None,
    client: Optional[NassApiClient] = None
) -> Dict:
    """
    Analyze crop production (total bushels).

    Args:
        commodity: Crop name
        year: Year (None for current year with auto-fallback)
        compare_previous: Whether to compare with previous year
        level: Geographic level ('national' or 'state')
        state: Specific state (if level='state')
        client: API client

    Returns:
        Dictionary with production analysis
    """
    if client is None:
        client = NassApiClient()

    # Auto-detect year if not specified
    year_requested = year
    if year is None:
        year = get_current_crop_year()

    year_used = year
    fallback_attempted = False

    # Fetch production data
    try:
        agg_level = 'STATE' if level == 'state' else 'NATIONAL'
        result = client.get_crop_production(
            commodity=commodity,
            year=year,
            state=state,
            agg_level=agg_level
        )
        data = result['data']
        metadata = result['metadata']
    except DataNotFoundError:
        # Try previous year if should fallback
        if should_try_previous_year(year):
            fallback_year = year - 1
            try:
                result = client.get_crop_production(
                    commodity=commodity,
                    year=fallback_year,
                    state=state,
                    agg_level=agg_level
                )
                data = result['data']
                metadata = result['metadata']
                year_used = fallback_year
                fallback_attempted = True
                import logging
                logging.info(f"No data for {year}, using {fallback_year} instead")
            except DataNotFoundError as e:
                raise AnalysisError(str(e))
        else:
            raise AnalysisError(f"No production data available for {commodity} {year}")

    # Create year info message
    year_info = format_year_message(
        year_used,
        year_requested,
        "auto-detected current year" if year_requested is None else "requested year"
    )

    # Parse production data
    df = parse_production_response(data)

    # Compare with previous year if requested
    comparison_data = None
    if compare_previous:
        previous_year = year_used - 1
        try:
            prev_result = client.get_crop_production(
                commodity=commodity,
                year=previous_year,
                state=state,
                agg_level=agg_level
            )
            df_prev = parse_production_response(prev_result['data'])

            # Calculate changes
            df_comparison = calculate_production_change(
                pd.concat([df, df_prev]),
                year_used,
                previous_year
            )

            if not df_comparison.empty:
                comparison_data = {
                    'previous_year': previous_year,
                    'states': df_comparison.to_dict('records')
                }
        except (DataNotFoundError, AnalysisError):
            pass  # Comparison optional

    if level == 'national':
        national_production = df['production_bu'].sum() if not df.empty else 0

        return {
            'commodity': commodity,
            'year': year_used,
            'year_requested': year_requested,
            'year_info': year_info,
            'fallback_used': fallback_attempted,
            'metric_type': 'PRODUCTION',
            'level': 'NATIONAL',
            'production_bu': national_production,
            'comparison': comparison_data
        }
    else:
        return {
            'commodity': commodity,
            'year': year_used,
            'year_requested': year_requested,
            'year_info': year_info,
            'fallback_used': fallback_attempted,
            'metric_type': 'PRODUCTION',
            'level': 'STATE',
            'states': df.to_dict('records'),
            'comparison': comparison_data
        }


def area_analysis(
    commodity: str,
    year: Optional[int] = None,
    area_type: str = 'PLANTED',
    compare_planted_vs_harvested: bool = False,
    level: str = 'national',
    state: Optional[str] = None,
    client: Optional[NassApiClient] = None
) -> Dict:
    """
    Analyze crop area (acres planted or harvested).

    Args:
        commodity: Crop name
        year: Year (None for current year with auto-fallback)
        area_type: 'PLANTED' or 'HARVESTED'
        compare_planted_vs_harvested: Whether to compare planted vs harvested
        level: Geographic level ('national' or 'state')
        state: Specific state (if level='state')
        client: API client

    Returns:
        Dictionary with area analysis
    """
    if client is None:
        client = NassApiClient()

    # Auto-detect year if not specified
    year_requested = year
    if year is None:
        year = get_current_crop_year()

    year_used = year
    fallback_attempted = False

    # Fetch area data
    try:
        agg_level = 'STATE' if level == 'state' else 'NATIONAL'
        result = client.get_crop_area(
            commodity=commodity,
            year=year,
            area_type=area_type,
            state=state,
            agg_level=agg_level
        )
        data = result['data']
        metadata = result['metadata']
    except DataNotFoundError:
        # Try previous year if should fallback
        if should_try_previous_year(year):
            fallback_year = year - 1
            try:
                result = client.get_crop_area(
                    commodity=commodity,
                    year=fallback_year,
                    area_type=area_type,
                    state=state,
                    agg_level=agg_level
                )
                data = result['data']
                metadata = result['metadata']
                year_used = fallback_year
                fallback_attempted = True
                import logging
                logging.info(f"No data for {year}, using {fallback_year} instead")
            except DataNotFoundError as e:
                raise AnalysisError(str(e))
        else:
            raise AnalysisError(f"No area data available for {commodity} {year}")

    # Create year info message
    year_info = format_year_message(
        year_used,
        year_requested,
        "auto-detected current year" if year_requested is None else "requested year"
    )

    # Parse area data
    df = parse_area_response(data)

    # Compare planted vs harvested if requested
    comparison_data = None
    if compare_planted_vs_harvested:
        try:
            # Get the other area type
            other_type = 'HARVESTED' if area_type == 'PLANTED' else 'PLANTED'
            other_result = client.get_crop_area(
                commodity=commodity,
                year=year_used,
                area_type=other_type,
                state=state,
                agg_level=agg_level
            )
            df_other = parse_area_response(other_result['data'])

            # Combine both datasets
            df_combined = pd.concat([df, df_other])

            # Calculate comparison
            df_comparison = compare_planted_vs_harvested(df_combined)

            if not df_comparison.empty:
                comparison_data = {
                    'type': 'planted_vs_harvested',
                    'states': df_comparison.to_dict('records')
                }
        except (DataNotFoundError, AnalysisError):
            pass  # Comparison optional

    if level == 'national':
        national_acres = df['acres'].sum() if not df.empty else 0

        return {
            'commodity': commodity,
            'year': year_used,
            'year_requested': year_requested,
            'year_info': year_info,
            'fallback_used': fallback_attempted,
            'metric_type': f'AREA_{area_type}',
            'level': 'NATIONAL',
            'acres': national_acres,
            'area_type': area_type,
            'comparison': comparison_data
        }
    else:
        return {
            'commodity': commodity,
            'year': year_used,
            'year_requested': year_requested,
            'year_info': year_info,
            'fallback_used': fallback_attempted,
            'metric_type': f'AREA_{area_type}',
            'level': 'STATE',
            'area_type': area_type,
            'states': df.to_dict('records'),
            'comparison': comparison_data
        }


# ============================================================================
# COMPREHENSIVE MULTI-METRIC REPORT
# ============================================================================

def comprehensive_crop_report(
    commodity: str,
    year: Optional[int] = None,
    include_metrics: Optional[List[str]] = None,
    client: Optional[NassApiClient] = None
) -> Dict:
    """
    Generate comprehensive report combining all available metrics.

    Args:
        commodity: Crop name
        year: Year (None for current year with auto-fallback)
        include_metrics: List of metrics to include. None = all available.
                        Options: 'condition', 'progress', 'yield', 'production', 'area'
        client: API client

    Returns:
        Dictionary with all metrics combined
    """
    if client is None:
        client = NassApiClient()

    # Auto-detect year if not specified
    if year is None:
        year = get_current_crop_year()

    # Default to all metrics
    if include_metrics is None:
        include_metrics = ['condition', 'progress', 'yield', 'production', 'area']

    # Normalize metric names
    include_metrics = [m.lower() for m in include_metrics]

    report = {
        'commodity': commodity,
        'year': year,
        'generated_at': pd.Timestamp.now().isoformat(),
        'metrics': {}
    }

    # Condition
    if 'condition' in include_metrics:
        try:
            condition = current_condition_report(commodity, year, client=client)
            report['metrics']['condition'] = {
                'week': condition['week'],
                'good_excellent': condition['conditions'].get('good_excellent'),
                'breakdown': {
                    'excellent': condition['conditions'].get('EXCELLENT'),
                    'good': condition['conditions'].get('GOOD'),
                    'fair': condition['conditions'].get('FAIR'),
                    'poor': condition['conditions'].get('POOR'),
                    'very_poor': condition['conditions'].get('VERY POOR')
                },
                'top_states': condition.get('top_states', [])[:3],
                'year_info': condition['year_info']
            }
        except AnalysisError as e:
            report['metrics']['condition'] = {'error': str(e)}

    # Progress (Harvest)
    if 'progress' in include_metrics:
        try:
            harvest = harvest_progress_report(commodity, year, client=client)
            report['metrics']['harvest_progress'] = {
                'week': harvest['week'],
                'percent_harvested': harvest.get('percent_harvested'),
                'top_states': harvest.get('top_states', [])[:3],
                'year_info': harvest['year_info']
            }
        except AnalysisError:
            report['metrics']['harvest_progress'] = {'error': 'Not available'}

        try:
            planting = planting_progress_report(commodity, year, client=client)
            report['metrics']['planting_progress'] = {
                'week': planting['week'],
                'percent_planted': planting.get('percent_planted'),
                'top_states': planting.get('top_states', [])[:3],
                'year_info': planting['year_info']
            }
        except AnalysisError:
            report['metrics']['planting_progress'] = {'error': 'Not available'}

    # Yield
    if 'yield' in include_metrics:
        try:
            yield_data = yield_analysis(commodity, year, client=client)
            report['metrics']['yield'] = {
                'yield_bu_per_acre': yield_data.get('yield_bu_per_acre'),
                'has_comparison': yield_data.get('comparison') is not None,
                'year_info': yield_data['year_info']
            }
        except AnalysisError as e:
            report['metrics']['yield'] = {'error': str(e)}

    # Production
    if 'production' in include_metrics:
        try:
            production = production_analysis(commodity, year, client=client)
            report['metrics']['production'] = {
                'production_bu': production.get('production_bu'),
                'has_comparison': production.get('comparison') is not None,
                'year_info': production['year_info']
            }
        except AnalysisError as e:
            report['metrics']['production'] = {'error': str(e)}

    # Area
    if 'area' in include_metrics:
        try:
            area_planted = area_analysis(commodity, year, area_type='PLANTED', client=client)
            report['metrics']['area_planted'] = {
                'acres': area_planted.get('acres'),
                'year_info': area_planted['year_info']
            }
        except AnalysisError:
            report['metrics']['area_planted'] = {'error': 'Not available'}

        try:
            area_harvested = area_analysis(commodity, year, area_type='HARVESTED', client=client)
            report['metrics']['area_harvested'] = {
                'acres': area_harvested.get('acres'),
                'year_info': area_harvested['year_info']
            }
        except AnalysisError:
            report['metrics']['area_harvested'] = {'error': 'Not available'}

    return report


def main():
    """Test analysis functions."""
    import os

    if 'NASS_API_KEY' not in os.environ:
        print("Error: Set NASS_API_KEY environment variable")
        return

    print("Testing analysis functions...\n")

    client = NassApiClient()

    # Test current conditions
    print("1. Current Condition Report:")
    try:
        report = current_condition_report('CORN', 2024, client=client)
        print(f"   Week: {report['week']}")
        print(f"   Good+Excellent: {report['conditions'].get('good_excellent', 0):.1f}%")
        print(f"   Top state: {report['top_states'][0]['state_name'] if report['top_states'] else 'N/A'}")
    except AnalysisError as e:
        print(f"   Error: {e}")

    print("\n2. Week-over-Week:")
    try:
        wow = week_over_week_comparison('SOYBEANS', 2024, client=client)
        print(f"   Current week: {wow['current_week']}")
        print(f"   National delta: {wow['national']['delta']:+.1f} points")
        if wow['top_deteriorations']:
            print(f"   Worst state: {wow['top_deteriorations'][0]['state_name']}")
    except AnalysisError as e:
        print(f"   Error: {e}")

    print("\n3. Year-over-Year:")
    try:
        yoy = year_over_year_comparison('CORN', 2024, 2023, client=client)
        print(f"   Week: {yoy['week']}")
        print(f"   Delta: {yoy['national_delta']['good_excellent']:+.1f} points")
    except AnalysisError as e:
        print(f"   Error: {e}")

    print("\nDone!")


if __name__ == "__main__":
    main()
