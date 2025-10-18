#!/usr/bin/env python3
"""
Helper Utilities for US Crop Monitor

Common utility functions used across the skill.

Author: Agent Creator
Version: 2.0.0
"""

from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def get_current_crop_year() -> int:
    """
    Get the current crop year.
    
    Returns the current calendar year, which is appropriate for:
    - Crop conditions (reported throughout growing season)
    - Harvest progress (reported in fall)
    - Yield estimates (forecasted during season, final after harvest)
    
    For off-season queries (Jan-Apr), data from previous year
    is often more relevant and will be used as fallback.
    
    Returns:
        Current year as integer
        
    Examples:
        >>> # If today is October 18, 2025
        >>> get_current_crop_year()
        2025
    """
    return datetime.now().year


def get_crop_year_with_fallback(
    requested_year: Optional[int] = None,
    allow_previous_year: bool = True
) -> tuple[int, int]:
    """
    Get crop year with intelligent fallback.
    
    Args:
        requested_year: Specific year requested (None for current)
        allow_previous_year: Whether to allow falling back to previous year
        
    Returns:
        Tuple of (primary_year, fallback_year)
        
    Examples:
        >>> get_crop_year_with_fallback()  # Today is Oct 2025
        (2025, 2024)
        
        >>> get_crop_year_with_fallback(2023)
        (2023, 2022)
        
        >>> get_crop_year_with_fallback(2025, allow_previous_year=False)
        (2025, None)
    """
    if requested_year is None:
        primary_year = get_current_crop_year()
    else:
        primary_year = requested_year
    
    fallback_year = primary_year - 1 if allow_previous_year else None
    
    return primary_year, fallback_year


def is_current_crop_season(month: Optional[int] = None) -> bool:
    """
    Determine if we're in the active crop growing/monitoring season.
    
    Args:
        month: Month to check (1-12), None for current month
        
    Returns:
        True if in active crop season (May-December)
        
    Notes:
        - May-July: Planting and emergence
        - August-September: Peak condition monitoring
        - October-November: Harvest season
        - December-April: Off-season (limited new data)
    """
    if month is None:
        month = datetime.now().month
    
    # Active season: May (5) through December (12)
    return 5 <= month <= 12


def should_try_previous_year(year: Optional[int] = None) -> bool:
    """
    Determine if we should automatically try previous year as fallback.
    
    Args:
        year: Year to check (None for current)
        
    Returns:
        True if previous year fallback recommended
        
    Logic:
        - In off-season (Jan-Apr): Yes, likely need previous year data
        - In early season (May-Jun): Maybe, current year data might not exist yet
        - In late season (Jul-Dec): No, current year data should be available
    """
    if year is None:
        year = get_current_crop_year()
    
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    # If requesting a past year, don't need fallback logic
    if year < current_year:
        return False
    
    # If requesting current year
    if year == current_year:
        # Off-season: definitely try previous year
        if current_month < 5:
            logger.info(f"Off-season month {current_month}, recommending fallback to {year-1}")
            return True
        
        # Early season: maybe try previous year
        if current_month < 7:
            logger.info(f"Early season month {current_month}, may fallback to {year-1}")
            return True
        
        # Late season: current year data should exist
        return False
    
    # If requesting future year, no fallback
    return False


def format_year_message(
    year_used: int,
    year_requested: Optional[int] = None,
    reason: str = "current year"
) -> str:
    """
    Format a user-friendly message explaining which year's data is being shown.
    
    Args:
        year_used: Year of data actually returned
        year_requested: Year originally requested (None if auto-detected)
        reason: Reason for year selection
        
    Returns:
        Formatted message string
        
    Examples:
        >>> format_year_message(2025, None, "auto-detected")
        "Showing 2025 data (auto-detected current year)"
        
        >>> format_year_message(2024, 2025, "fallback")
        "⚠ Showing 2024 data (2025 data not yet available)"
    """
    if year_requested is None or year_requested == year_used:
        return f"Showing {year_used} data ({reason})"
    else:
        # Fallback scenario
        return f"⚠ Showing {year_used} data ({year_requested} data not yet available)"


def main():
    """Test helper functions."""
    print("Testing helper functions...\n")
    
    print(f"Current crop year: {get_current_crop_year()}")
    print(f"Is crop season?: {is_current_crop_season()}")
    print(f"Should try previous year?: {should_try_previous_year()}")
    
    primary, fallback = get_crop_year_with_fallback()
    print(f"\nYear with fallback: primary={primary}, fallback={fallback}")
    
    msg = format_year_message(2025, None, "auto-detected")
    print(f"\nYear message: {msg}")
    
    msg_fallback = format_year_message(2024, 2025, "fallback")
    print(f"Fallback message: {msg_fallback}")


if __name__ == "__main__":
    main()
