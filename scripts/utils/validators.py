#!/usr/bin/env python3
"""
Validators for NASS API Parameters

Provides validation functions to ensure correct parameters before API calls.

Author: Agent Creator
Version: 1.0.0
"""

from datetime import datetime
from typing import Any, List, Optional


# Valid commodities supported by this skill
VALID_COMMODITIES = ['CORN', 'SOYBEANS', 'WHEAT', 'WHEAT, WINTER', 'WHEAT, SPRING']

# Valid US state codes
VALID_STATE_CODES = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
]

# Valid state names (subset of major crop-producing states)
VALID_STATE_NAMES = [
    'ALABAMA', 'ARKANSAS', 'CALIFORNIA', 'COLORADO', 'GEORGIA',
    'IDAHO', 'ILLINOIS', 'INDIANA', 'IOWA', 'KANSAS',
    'KENTUCKY', 'LOUISIANA', 'MICHIGAN', 'MINNESOTA', 'MISSISSIPPI',
    'MISSOURI', 'MONTANA', 'NEBRASKA', 'NEW YORK', 'NORTH CAROLINA',
    'NORTH DAKOTA', 'OHIO', 'OKLAHOMA', 'OREGON', 'PENNSYLVANIA',
    'SOUTH CAROLINA', 'SOUTH DAKOTA', 'TENNESSEE', 'TEXAS',
    'WASHINGTON', 'WISCONSIN'
]


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_commodity(commodity: str) -> str:
    """
    Validate commodity name.

    Args:
        commodity: Commodity name to validate

    Returns:
        Validated commodity (uppercase)

    Raises:
        ValidationError: If commodity is invalid
    """
    if not isinstance(commodity, str):
        raise ValidationError(f"Commodity must be string, got {type(commodity)}")

    commodity_upper = commodity.upper()

    if commodity_upper not in VALID_COMMODITIES:
        raise ValidationError(
            f"Invalid commodity: '{commodity}'. "
            f"Valid commodities: {', '.join(VALID_COMMODITIES)}"
        )

    return commodity_upper


def validate_year(year: int, allow_future: bool = False) -> int:
    """
    Validate year.

    Args:
        year: Year to validate
        allow_future: Whether to allow future years

    Returns:
        Validated year

    Raises:
        ValidationError: If year is invalid
    """
    if not isinstance(year, int):
        raise ValidationError(f"Year must be integer, got {type(year)}")

    current_year = datetime.now().year

    # NASS data available from 1866
    min_year = 1866

    if year < min_year:
        raise ValidationError(
            f"Year {year} is too old. NASS data available from {min_year}."
        )

    if not allow_future and year > current_year:
        raise ValidationError(
            f"Year {year} is in the future. Current year is {current_year}."
        )

    if allow_future and year > current_year + 10:
        raise ValidationError(
            f"Year {year} is too far in the future (max {current_year + 10})."
        )

    return year


def validate_week(week: int) -> int:
    """
    Validate week number.

    Args:
        week: Week number to validate (1-53)

    Returns:
        Validated week

    Raises:
        ValidationError: If week is invalid
    """
    if not isinstance(week, int):
        raise ValidationError(f"Week must be integer, got {type(week)}")

    if week < 1 or week > 53:
        raise ValidationError(
            f"Week {week} is invalid. Valid range: 1-53."
        )

    return week


def validate_state(state: str) -> str:
    """
    Validate state code or name.

    Args:
        state: State code (e.g., 'IA') or name (e.g., 'IOWA')

    Returns:
        Validated state (uppercase)

    Raises:
        ValidationError: If state is invalid
    """
    if not isinstance(state, str):
        raise ValidationError(f"State must be string, got {type(state)}")

    state_upper = state.upper()

    # Check if it's a valid code or name
    if state_upper in VALID_STATE_CODES or state_upper in VALID_STATE_NAMES:
        return state_upper

    raise ValidationError(
        f"Invalid state: '{state}'. "
        f"Provide 2-letter code (e.g., 'IA') or full name (e.g., 'IOWA')."
    )


def validate_api_key(api_key: Optional[str]) -> str:
    """
    Validate API key.

    Args:
        api_key: API key to validate

    Returns:
        Validated API key

    Raises:
        ValidationError: If API key is invalid
    """
    if not api_key:
        raise ValidationError(
            "API key is required. Set NASS_API_KEY environment variable."
        )

    if not isinstance(api_key, str):
        raise ValidationError(f"API key must be string, got {type(api_key)}")

    if len(api_key) < 10:
        raise ValidationError(
            "API key appears too short. Check NASS_API_KEY value."
        )

    return api_key


def validate_agg_level(agg_level: str) -> str:
    """
    Validate aggregation level.

    Args:
        agg_level: Aggregation level

    Returns:
        Validated agg_level (uppercase)

    Raises:
        ValidationError: If agg_level is invalid
    """
    valid_levels = ['NATIONAL', 'STATE', 'COUNTY', 'REGION', 'WATERSHED']

    if not isinstance(agg_level, str):
        raise ValidationError(f"Agg level must be string, got {type(agg_level)}")

    agg_level_upper = agg_level.upper()

    if agg_level_upper not in valid_levels:
        raise ValidationError(
            f"Invalid aggregation level: '{agg_level}'. "
            f"Valid levels: {', '.join(valid_levels)}"
        )

    return agg_level_upper


def validate_response_data(data: Any) -> List[dict]:
    """
    Validate API response data structure.

    Args:
        data: Response data to validate

    Returns:
        Validated data as list of dicts

    Raises:
        ValidationError: If data structure is invalid
    """
    if data is None:
        raise ValidationError("Response data is None")

    if not isinstance(data, list):
        raise ValidationError(
            f"Response data must be list, got {type(data)}"
        )

    if len(data) == 0:
        raise ValidationError("Response data is empty")

    # Check first element has expected structure
    if not isinstance(data[0], dict):
        raise ValidationError(
            f"Response elements must be dicts, got {type(data[0])}"
        )

    # Check for required fields
    required_fields = ['commodity_desc', 'year', 'Value']
    missing_fields = [f for f in required_fields if f not in data[0]]

    if missing_fields:
        raise ValidationError(
            f"Response missing required fields: {', '.join(missing_fields)}"
        )

    return data


def validate_percentage(value: float, allow_none: bool = False) -> Optional[float]:
    """
    Validate percentage value.

    Args:
        value: Percentage value to validate
        allow_none: Whether None is allowed

    Returns:
        Validated percentage

    Raises:
        ValidationError: If percentage is invalid
    """
    if value is None and allow_none:
        return None

    if value is None:
        raise ValidationError("Percentage value is None")

    if not isinstance(value, (int, float)):
        raise ValidationError(
            f"Percentage must be numeric, got {type(value)}"
        )

    if value < 0 or value > 100:
        raise ValidationError(
            f"Percentage {value} is out of range (0-100)"
        )

    return float(value)


if __name__ == "__main__":
    # Test validators
    print("Testing validators...")

    # Test commodity
    try:
        assert validate_commodity('corn') == 'CORN'
        print("✓ Commodity validation passed")
    except AssertionError:
        print("✗ Commodity validation failed")

    # Test year
    try:
        validate_year(2024)
        print("✓ Year validation passed")
    except ValidationError as e:
        print(f"✗ Year validation failed: {e}")

    # Test invalid year
    try:
        validate_year(2030)
        print("✗ Future year should have failed")
    except ValidationError:
        print("✓ Future year correctly rejected")

    # Test week
    try:
        validate_week(32)
        print("✓ Week validation passed")
    except ValidationError as e:
        print(f"✗ Week validation failed: {e}")

    # Test state
    try:
        assert validate_state('ia') == 'IA'
        assert validate_state('Iowa') == 'IOWA'
        print("✓ State validation passed")
    except (ValidationError, AssertionError) as e:
        print(f"✗ State validation failed: {e}")

    # Test percentage
    try:
        validate_percentage(75.5)
        print("✓ Percentage validation passed")
    except ValidationError as e:
        print(f"✗ Percentage validation failed: {e}")

    print("\nAll tests completed!")
