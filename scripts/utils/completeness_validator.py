#!/usr/bin/env python3
"""
Completeness Validator

Validates completeness of crop condition data.

Author: Enhanced by Claude
Version: 2.0.0
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)


# Major crop-producing states by commodity
MAJOR_PRODUCERS = {
    'CORN': ['IOWA', 'ILLINOIS', 'NEBRASKA', 'MINNESOTA', 'INDIANA', 'SOUTH DAKOTA', 'KANSAS', 'OHIO', 'MISSOURI', 'WISCONSIN'],
    'SOYBEANS': ['ILLINOIS', 'IOWA', 'MINNESOTA', 'NEBRASKA', 'INDIANA', 'MISSOURI', 'OHIO', 'SOUTH DAKOTA', 'ARKANSAS', 'NORTH DAKOTA'],
    'WHEAT': ['KANSAS', 'NORTH DAKOTA', 'MONTANA', 'WASHINGTON', 'OKLAHOMA', 'TEXAS', 'COLORADO', 'IDAHO', 'SOUTH DAKOTA', 'NEBRASKA']
}


def validate_completeness(
    data: pd.DataFrame,
    report: Any,  # ValidationReport
    config: Dict[str, Any]
) -> None:
    """
    Validate data completeness.

    Checks:
    - All 5 condition categories present
    - Expected states present (major producers)
    - No missing critical fields

    Args:
        data: DataFrame with crop data
        report: ValidationReport
        config: Configuration
    """
    if data.empty:
        report.add_critical("completeness", "Data is empty")
        return

    completeness_config = config.get("completeness", {})

    # Check condition categories
    _validate_categories(data, report, completeness_config)

    # Check required fields
    _validate_required_fields(data, report)

    # Check for major producers (if state-level data)
    _validate_major_producers(data, report, completeness_config)


def _validate_categories(
    data: pd.DataFrame,
    report: Any,
    config: Dict[str, Any]
) -> None:
    """Validate that all condition categories are present."""
    required_categories = config.get(
        "required_categories",
        ["EXCELLENT", "GOOD", "FAIR", "POOR", "VERY POOR"]
    )

    require_all = config.get("require_all_categories", True)

    present_categories = [cat for cat in required_categories if cat in data.columns]
    missing_categories = [cat for cat in required_categories if cat not in data.columns]

    if missing_categories:
        if require_all:
            report.add_error(
                "completeness",
                f"Categorias de condição faltando: {', '.join(missing_categories)}",
                missing=missing_categories,
                present=present_categories
            )
        else:
            report.add_warning(
                "completeness",
                f"Algumas categorias ausentes: {', '.join(missing_categories)}"
            )
    else:
        report.add_info(
            "completeness",
            "Todas 5 categorias de condição presentes"
        )

    # Check for null values in present categories
    for cat in present_categories:
        null_count = data[cat].isna().sum()
        if null_count > 0:
            total = len(data)
            pct = (null_count / total) * 100
            report.add_warning(
                "completeness",
                f"Categoria '{cat}' tem {null_count}/{total} ({pct:.1f}%) valores nulos"
            )


def _validate_required_fields(
    data: pd.DataFrame,
    report: Any
) -> None:
    """Validate required fields are present and non-null."""
    required_fields = ['commodity_desc', 'year']

    missing_fields = [field for field in required_fields if field not in data.columns]

    if missing_fields:
        report.add_error(
            "completeness",
            f"Campos obrigatórios faltando: {', '.join(missing_fields)}"
        )
        return

    # Check for null values in required fields
    for field in required_fields:
        null_count = data[field].isna().sum()
        if null_count > 0:
            report.add_warning(
                "completeness",
                f"Campo obrigatório '{field}' tem {null_count} valores nulos"
            )


def _validate_major_producers(
    data: pd.DataFrame,
    report: Any,
    config: Dict[str, Any]
) -> None:
    """Validate that major producing states are present."""
    if 'state_name' not in data.columns or 'commodity_desc' not in data.columns:
        return  # Not state-level data

    commodity = data['commodity_desc'].iloc[0] if not data.empty else None

    if not commodity or commodity not in MAJOR_PRODUCERS:
        return

    major_states = MAJOR_PRODUCERS[commodity]
    present_states = data['state_name'].dropna().unique().tolist()

    # Normalize for comparison
    present_states_upper = [s.upper() for s in present_states]

    missing_major = [s for s in major_states if s not in present_states_upper]

    if missing_major:
        # Check how many are missing
        if len(missing_major) > 5:
            # Many major producers missing - critical
            report.add_error(
                "completeness",
                f"{len(missing_major)} grandes produtores de {commodity} ausentes",
                missing_states=missing_major[:5],
                note="Dados incompletos podem afetar análises nacionais"
            )
        else:
            # Few missing
            report.add_warning(
                "completeness",
                f"Alguns grandes produtores de {commodity} ausentes: {', '.join(missing_major)}"
            )
    else:
        # All major producers present
        report.add_info(
            "completeness",
            f"Todos os {len(major_states)} maiores produtores de {commodity} presentes nos dados"
        )


def validate_percentage_sum(
    data: pd.DataFrame,
    report: Any,
    tolerance: float = 2.0
) -> None:
    """
    Validate that condition percentages sum to ~100%.

    Args:
        data: DataFrame with condition columns
        report: ValidationReport
        tolerance: Allowed deviation from 100
    """
    categories = ['EXCELLENT', 'GOOD', 'FAIR', 'POOR', 'VERY POOR']
    present = [cat for cat in categories if cat in data.columns]

    if len(present) < 2:
        return  # Not enough data

    # Calculate sum for each row
    data_copy = data.copy()
    data_copy['total_pct'] = data_copy[present].sum(axis=1)

    # Check for invalid sums
    invalid = data_copy[
        (data_copy['total_pct'] < 100 - tolerance) |
        (data_copy['total_pct'] > 100 + tolerance)
    ]

    if len(invalid) > 0:
        total_rows = len(data)
        pct_invalid = (len(invalid) / total_rows) * 100

        if pct_invalid > 10:
            # More than 10% invalid - error
            report.add_error(
                "completeness",
                f"{len(invalid)}/{total_rows} ({pct_invalid:.1f}%) registros com soma != 100%",
                invalid_count=len(invalid),
                total_count=total_rows,
                percentage=f"{pct_invalid:.1f}%"
            )
        else:
            # Few invalid - warning
            report.add_warning(
                "completeness",
                f"{len(invalid)} registros com soma de categorias fora de 100% ±{tolerance}%"
            )

        # Show examples
        if 'state_name' in invalid.columns:
            examples = invalid.head(3)
            for _, row in examples.iterrows():
                state = row.get('state_name', 'N/A')
                total = row['total_pct']
                report.add_info(
                    "completeness",
                    f"  Exemplo: {state} soma = {total:.1f}%"
                )
    else:
        report.add_info(
            "completeness",
            f"Consistência OK: Todas somas de categorias dentro de 100% ±{tolerance}%"
        )


if __name__ == "__main__":
    # Test
    print("Testing completeness_validator...")

    from data_validator import ValidationReport, DataValidator

    # Create test data - complete
    complete_data = pd.DataFrame({
        'commodity_desc': ['CORN'] * 5,
        'year': [2024] * 5,
        'state_name': ['IOWA', 'ILLINOIS', 'NEBRASKA', 'MINNESOTA', 'INDIANA'],
        'EXCELLENT': [20, 21, 19, 22, 18],
        'GOOD': [55, 54, 56, 53, 57],
        'FAIR': [20, 20, 20, 20, 20],
        'POOR': [4, 4, 4, 4, 4],
        'VERY POOR': [1, 1, 1, 1, 1]
    })

    report = ValidationReport()
    config = DataValidator._default_config()

    validate_completeness(complete_data, report, config)
    validate_percentage_sum(complete_data, report, tolerance=2.0)

    print("\nValidation Results (Complete Data):")
    for result in report.results:
        print(f"  {result}")

    # Test incomplete data
    print("\n" + "="*60)
    incomplete_data = pd.DataFrame({
        'commodity_desc': ['CORN'] * 2,
        'year': [2024] * 2,
        'state_name': ['WYOMING', 'VERMONT'],  # Not major producers
        'EXCELLENT': [20, 21],
        'GOOD': [55, 54],
        'FAIR': [20, 20]
        # Missing POOR and VERY POOR
    })

    report2 = ValidationReport()
    validate_completeness(incomplete_data, report2, config)

    print("\nValidation Results (Incomplete Data):")
    for result in report2.results:
        print(f"  {result}")

    print(f"\nSummary: {report2.get_summary_line()}")
    print("\n✓ Completeness validator tests complete")
