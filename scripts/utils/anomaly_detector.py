#!/usr/bin/env python3
"""
Anomaly Detector

Detects anomalous patterns in crop condition data.

Author: Enhanced by Claude
Version: 2.0.0
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def detect_anomalies(
    data: pd.DataFrame,
    report: Any,  # ValidationReport
    config: Dict[str, Any]
) -> None:
    """
    Detect anomalies in crop condition data.

    Checks for:
    - Extreme values (100% or 0% in categories)
    - Impossible patterns
    - Suspicious distributions

    Args:
        data: DataFrame with crop data
        report: ValidationReport
        config: Configuration
    """
    if data.empty:
        return

    anomaly_config = config.get("anomaly", {})

    # Check for extreme values
    _detect_extreme_values(data, report, anomaly_config)

    # Check for impossible patterns
    _detect_impossible_patterns(data, report)

    # Check for suspicious distributions
    _detect_suspicious_distributions(data, report, anomaly_config)


def detect_week_over_week_anomalies(
    current_data: pd.DataFrame,
    previous_data: pd.DataFrame,
    report: Any,
    config: Dict[str, Any]
) -> None:
    """
    Detect anomalous changes between weeks.

    Args:
        current_data: Current week data
        previous_data: Previous week data
        report: ValidationReport
        config: Configuration
    """
    if current_data.empty or previous_data.empty:
        return

    anomaly_config = config.get("anomaly", {})
    max_change_warning = anomaly_config.get("max_week_change_warning", 20)
    max_change_critical = anomaly_config.get("max_week_change_critical", 50)

    # Check if both have good_excellent column
    if 'good_excellent' not in current_data.columns or 'good_excellent' not in previous_data.columns:
        return

    # For state-level data, check each state
    if 'state_name' in current_data.columns and 'state_name' in previous_data.columns:
        merged = current_data.merge(
            previous_data[['state_name', 'good_excellent']],
            on='state_name',
            how='inner',
            suffixes=('_current', '_previous')
        )

        if not merged.empty:
            merged['delta'] = merged['good_excellent_current'] - merged['good_excellent_previous']

            # Find extreme changes
            extreme_changes = merged[np.abs(merged['delta']) >= max_change_critical]

            for _, row in extreme_changes.iterrows():
                report.add_critical(
                    "anomaly",
                    f"Mudança EXTREMA em {row['state_name']}: {row['delta']:+.1f} pontos em uma semana",
                    state=row['state_name'],
                    previous=f"{row['good_excellent_previous']:.1f}%",
                    current=f"{row['good_excellent_current']:.1f}%",
                    change=f"{row['delta']:+.1f}",
                    possible_causes=[
                        "Evento climático extremo (seca, enchente, geada)",
                        "Erro nos dados",
                        "Revisão dos dados pelo USDA"
                    ]
                )

            # Find large changes
            large_changes = merged[
                (np.abs(merged['delta']) >= max_change_warning) &
                (np.abs(merged['delta']) < max_change_critical)
            ]

            if len(large_changes) > 3:
                # Many states with large changes
                report.add_warning(
                    "anomaly",
                    f"{len(large_changes)} estados com mudanças grandes (>{max_change_warning} pontos)",
                    count=len(large_changes),
                    states=large_changes['state_name'].tolist()[:5]
                )

    # National level
    if 'good_excellent' in current_data.columns and 'good_excellent' in previous_data.columns:
        current_national = current_data['good_excellent'].mean()
        previous_national = previous_data['good_excellent'].mean()
        delta = current_national - previous_national

        if abs(delta) >= max_change_critical:
            report.add_critical(
                "anomaly",
                f"Mudança EXTREMA nacional: {delta:+.1f} pontos em uma semana",
                previous=f"{previous_national:.1f}%",
                current=f"{current_national:.1f}%",
                change=f"{delta:+.1f}"
            )
        elif abs(delta) >= max_change_warning:
            report.add_warning(
                "anomaly",
                f"Mudança grande nacional: {delta:+.1f} pontos em uma semana",
                previous=f"{previous_national:.1f}%",
                current=f"{current_national:.1f}%",
                change=f"{delta:+.1f}"
            )


def _detect_extreme_values(
    data: pd.DataFrame,
    report: Any,
    config: Dict[str, Any]
) -> None:
    """Detect extreme values (100% or 0% in categories)."""
    categories = ['EXCELLENT', 'GOOD', 'FAIR', 'POOR', 'VERY POOR']
    available_cats = [c for c in categories if c in data.columns]

    if not available_cats:
        return

    # Check each row
    for idx, row in data.iterrows():
        state = row.get('state_name', 'Nacional')

        # Check for 100% in single category
        for cat in available_cats:
            if pd.notna(row[cat]) and row[cat] >= 99.9:
                report.add_warning(
                    "anomaly",
                    f"{state}: 100% na categoria '{cat}' (incomum)",
                    state=state,
                    category=cat,
                    value=f"{row[cat]:.1f}%"
                )

        # Check for 0% in all categories except one
        non_zero_cats = [c for c in available_cats if pd.notna(row[c]) and row[c] > 0.1]

        if len(non_zero_cats) == 1:
            report.add_warning(
                "anomaly",
                f"{state}: Apenas uma categoria não-zero ('{non_zero_cats[0]}')",
                state=state,
                non_zero_category=non_zero_cats[0]
            )


def _detect_impossible_patterns(
    data: pd.DataFrame,
    report: Any
) -> None:
    """Detect impossible patterns (e.g., all zeros)."""
    categories = ['EXCELLENT', 'GOOD', 'FAIR', 'POOR', 'VERY POOR']
    available_cats = [c for c in categories if c in data.columns]

    if len(available_cats) < 2:
        return

    for idx, row in data.iterrows():
        state = row.get('state_name', 'Nacional')

        # Check if all categories are 0
        all_values = [row[c] for c in available_cats if pd.notna(row[c])]

        if all_values and all(v == 0 for v in all_values):
            report.add_critical(
                "anomaly",
                f"{state}: TODAS categorias são 0% (impossível)",
                state=state
            )

        # Check if sum is far from 100
        total = sum(all_values)
        if total < 90 or total > 110:
            report.add_error(
                "anomaly",
                f"{state}: Soma das categorias = {total:.1f}% (deve ser ~100%)",
                state=state,
                sum=f"{total:.1f}%"
            )


def _detect_suspicious_distributions(
    data: pd.DataFrame,
    report: Any,
    config: Dict[str, Any]
) -> None:
    """Detect suspicious distributions."""
    if 'good_excellent' not in data.columns:
        return

    # Calculate statistics
    ge_values = data['good_excellent'].dropna()

    if len(ge_values) < 3:
        return  # Not enough data

    mean_val = ge_values.mean()
    std_val = ge_values.std()

    # Check for outliers (>3 sigma)
    sigma_threshold = config.get("sigma_threshold", 3.0)

    if std_val > 0:
        outliers = data[
            np.abs(data['good_excellent'] - mean_val) > sigma_threshold * std_val
        ]

        for _, row in outliers.iterrows():
            state = row.get('state_name', 'N/A')
            z_score = (row['good_excellent'] - mean_val) / std_val

            report.add_warning(
                "anomaly",
                f"{state}: Valor atípico ({row['good_excellent']:.1f}%) - {abs(z_score):.1f} desvios padrão da média",
                state=state,
                value=f"{row['good_excellent']:.1f}%",
                mean=f"{mean_val:.1f}%",
                z_score=f"{z_score:.2f}"
            )


def detect_year_over_year_anomalies(
    current_data: pd.DataFrame,
    previous_year_data: pd.DataFrame,
    report: Any,
    config: Dict[str, Any]
) -> None:
    """
    Detect anomalous year-over-year changes.

    Args:
        current_data: Current year data
        previous_year_data: Previous year data
        report: ValidationReport
        config: Configuration
    """
    if current_data.empty or previous_year_data.empty:
        return

    # For informational purposes, not blocking
    if 'good_excellent' not in current_data.columns or 'good_excellent' not in previous_year_data.columns:
        return

    # National comparison
    current_national = current_data['good_excellent'].mean()
    previous_national = previous_year_data['good_excellent'].mean()
    yoy_delta = current_national - previous_national

    if abs(yoy_delta) >= 30:
        # Very large year-over-year change
        report.add_warning(
            "anomaly",
            f"Mudança MUITO GRANDE ano a ano: {yoy_delta:+.1f} pontos",
            current_year_avg=f"{current_national:.1f}%",
            previous_year_avg=f"{previous_national:.1f}%",
            change=f"{yoy_delta:+.1f}",
            note="Mudanças grandes YoY podem indicar condições climáticas muito diferentes"
        )


if __name__ == "__main__":
    # Test
    print("Testing anomaly_detector...")

    from data_validator import ValidationReport

    # Create test data with anomalies
    test_data = pd.DataFrame({
        'state_name': ['Iowa', 'Illinois', 'Nebraska', 'Kansas', 'Outlier State'],
        'EXCELLENT': [20, 21, 19, 18, 100],  # Outlier has 100%
        'GOOD': [55, 54, 56, 52, 0],
        'FAIR': [20, 20, 20, 25, 0],
        'POOR': [4, 4, 4, 4, 0],
        'VERY POOR': [1, 1, 1, 1, 0],
        'good_excellent': [75, 75, 75, 70, 100]
    })

    # Create report
    report = ValidationReport()

    # Get config
    from data_validator import DataValidator
    config = DataValidator._default_config()

    # Run detection
    detect_anomalies(test_data, report, config)

    print("\nAnomaly Detection Results:")
    for result in report.results:
        print(f"  {result}")

    print(f"\nSummary: {report.get_summary_line()}")
    print("\n✓ Anomaly detector tests complete")
