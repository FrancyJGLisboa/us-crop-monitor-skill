#!/usr/bin/env python3
"""
Temporal Validator

Validates temporal aspects of crop condition data.

Author: Enhanced by Claude
Version: 2.0.0
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def validate_temporal_consistency(
    data: pd.DataFrame,
    report: Any,  # ValidationReport
    config: Dict[str, Any]
) -> None:
    """
    Validate temporal aspects of data.

    Checks:
    - Year requested vs year in data vs current year
    - Data age (freshness)
    - Week number makes sense for current date
    - Week within crop season

    Args:
        data: DataFrame with crop data
        report: ValidationReport to add results to
        config: Configuration dict
    """
    if data.empty:
        report.add_error("temporal", "Cannot validate temporal consistency of empty data")
        return

    temporal_config = config.get("temporal", {})
    current_date = datetime.now()
    current_year = current_date.year
    current_week = current_date.isocalendar()[1]

    # Extract year from data
    if 'year' in data.columns:
        data_year = int(data['year'].iloc[0]) if not data['year'].isna().all() else None
    else:
        data_year = None

    if data_year is None:
        report.add_warning("temporal", "No year found in data")
        return

    # Check year discrepancy
    year_diff = current_year - data_year

    if year_diff < 0:
        # Future year
        report.add_critical(
            "temporal",
            f"Dados são do futuro: {data_year} (ano atual: {current_year})",
            year_data=data_year,
            year_current=current_year,
            discrepancy=abs(year_diff)
        )

    elif year_diff == 0:
        # Current year - good
        report.add_info(
            "temporal",
            f"Dados são do ano atual ({data_year})"
        )

    elif year_diff == 1:
        # Last year - warning if we're early in current year
        if current_date.month <= 6:
            # Early in year, last year's data might be latest available
            report.add_warning(
                "temporal",
                f"Dados são de {data_year} (ano passado). Dados de {current_year} podem não estar disponíveis ainda."
            )
        else:
            # Late in year, should have current year data
            report.add_error(
                "temporal",
                f"Dados são de {data_year}, mas estamos em {current_year}. Dados mais recentes podem estar disponíveis.",
                year_data=data_year,
                year_current=current_year
            )

    elif year_diff >= 2:
        # Data is 2+ years old - critical
        report.add_critical(
            "temporal",
            f"Dados têm {year_diff} anos de idade ({data_year} vs {current_year})",
            year_data=data_year,
            year_current=current_year,
            discrepancy=year_diff,
            recommendation="Verifique se dados mais recentes estão disponíveis"
        )

    # Check week number consistency
    if 'week_number' in data.columns:
        data_week = int(data['week_number'].iloc[0]) if not data['week_number'].isna().all() else None

        if data_week:
            # Validate week within crop season
            commodity = data['commodity_desc'].iloc[0] if 'commodity_desc' in data.columns else None

            if commodity:
                _validate_crop_season(
                    commodity=commodity,
                    week=data_week,
                    year=data_year,
                    current_year=current_year,
                    current_week=current_week,
                    report=report,
                    config=temporal_config
                )

    # Check data freshness based on timestamps
    if 'week_ending' in data.columns:
        week_ending = pd.to_datetime(data['week_ending'].iloc[0], errors='coerce')

        if pd.notna(week_ending):
            age_days = (current_date - week_ending).days

            _validate_data_age(
                age_days=age_days,
                report=report,
                config=temporal_config
            )

    # Check published date if available (load_time from NASS API)
    metadata = report.data_metadata
    if 'fetched_at' in metadata:
        fetched_at = metadata['fetched_at']
        if isinstance(fetched_at, str):
            fetched_at = datetime.fromisoformat(fetched_at)

        fetch_age_hours = (current_date - fetched_at).total_seconds() / 3600

        if fetch_age_hours < 1:
            report.add_info("temporal", f"Dados buscados há {int(fetch_age_hours * 60)} minutos")
        elif fetch_age_hours < 24:
            report.add_info("temporal", f"Dados buscados há {int(fetch_age_hours)} horas")
        else:
            report.add_info("temporal", f"Dados buscados há {int(fetch_age_hours / 24)} dias")


def _validate_crop_season(
    commodity: str,
    week: int,
    year: int,
    current_year: int,
    current_week: int,
    report: Any,
    config: Dict[str, Any]
) -> None:
    """Validate week is within expected crop season."""
    crop_seasons = config.get("crop_seasons", {})

    if commodity not in crop_seasons:
        return  # No season info available

    season = crop_seasons[commodity]
    start_week = season.get("start_week")
    end_week = season.get("end_week")

    if not (start_week and end_week):
        return

    # Check if week is within season
    if start_week <= week <= end_week:
        report.add_info(
            "temporal",
            f"Semana #{week} está dentro da temporada de {commodity} (semanas {start_week}-{end_week})"
        )
    else:
        # Out of season
        if week < start_week:
            report.add_warning(
                "temporal",
                f"Semana #{week} é ANTES da temporada típica de {commodity} (inicia na semana {start_week})",
                week=week,
                season_start=start_week,
                season_end=end_week
            )
        else:
            report.add_warning(
                "temporal",
                f"Semana #{week} é APÓS a temporada típica de {commodity} (termina na semana {end_week})",
                week=week,
                season_start=start_week,
                season_end=end_week
            )

    # If data is from current year, check if week is future
    if year == current_year and week > current_week + 1:
        report.add_critical(
            "temporal",
            f"Semana #{week} é no futuro (semana atual: #{current_week})",
            week_data=week,
            week_current=current_week
        )


def _validate_data_age(
    age_days: int,
    report: Any,
    config: Dict[str, Any]
) -> None:
    """Validate data freshness based on age."""
    max_age_warning = config.get("max_age_warning_days", 30)
    max_age_error = config.get("max_age_error_days", 90)

    if age_days < 0:
        report.add_critical(
            "temporal",
            f"Data de término da semana é no futuro (daqui a {abs(age_days)} dias)",
            age_days=age_days
        )

    elif age_days <= 7:
        report.add_info(
            "temporal",
            f"Dados são recentes ({age_days} dias de idade)"
        )

    elif age_days <= max_age_warning:
        report.add_info(
            "temporal",
            f"Dados têm {age_days} dias de idade"
        )

    elif age_days <= max_age_error:
        # Between warning and error threshold
        report.add_warning(
            "temporal",
            f"Dados têm {age_days} dias de idade - podem estar desatualizados",
            age_days=age_days,
            recommendation="Próxima atualização do USDA normalmente é às segundas-feiras"
        )

    else:
        # Older than error threshold
        report.add_error(
            "temporal",
            f"Dados têm {age_days} dias ({age_days // 7} semanas) de idade",
            age_days=age_days,
            age_weeks=age_days // 7,
            recommendation="Verifique se há dados mais recentes disponíveis"
        )


def validate_year_consistency(
    requested_year: Optional[int],
    data: pd.DataFrame,
    report: Any,
    config: Dict[str, Any]
) -> None:
    """
    Validate that requested year matches data year.

    Args:
        requested_year: Year user requested (None if not specified)
        data: DataFrame with data
        report: ValidationReport
        config: Configuration
    """
    if requested_year is None or data.empty:
        return

    if 'year' not in data.columns:
        report.add_warning("temporal", "Cannot validate year consistency - no year column in data")
        return

    data_year = int(data['year'].iloc[0]) if not data['year'].isna().all() else None

    if data_year is None:
        report.add_warning("temporal", "Cannot validate year consistency - year is null in data")
        return

    if requested_year != data_year:
        year_diff = abs(requested_year - data_year)

        if year_diff >= 2:
            # Critical discrepancy
            report.add_critical(
                "temporal",
                f"DISCREPÂNCIA: Solicitado ano {requested_year}, mas recebeu ano {data_year}",
                year_requested=requested_year,
                year_returned=data_year,
                discrepancy=year_diff,
                possible_reasons=[
                    f"Dados de {requested_year} ainda não publicados pelo USDA",
                    "Erro na consulta à API",
                    "Problema de configuração"
                ]
            )
        else:
            # Minor discrepancy
            report.add_error(
                "temporal",
                f"Solicitado ano {requested_year}, mas recebeu ano {data_year}",
                year_requested=requested_year,
                year_returned=data_year
            )


if __name__ == "__main__":
    # Test
    print("Testing temporal_validator...")

    from data_validator import ValidationReport
    import numpy as np

    # Create test data
    test_data = pd.DataFrame({
        'year': [2024] * 5,
        'week_number': [32] * 5,
        'week_ending': ['2024-08-11'] * 5,
        'commodity_desc': ['CORN'] * 5,
        'Value': [15, 54, 25, 5, 1]
    })

    # Create report
    report = ValidationReport()
    report.data_metadata = {
        'fetched_at': datetime.now() - timedelta(hours=2)
    }

    # Get config
    from data_validator import DataValidator
    config = DataValidator._default_config()

    # Run validation
    validate_temporal_consistency(test_data, report, config)

    print("\nValidation Results:")
    for result in report.results:
        print(f"  {result}")

    print(f"\nSummary: {report.get_summary_line()}")
    print("\n✓ Temporal validator tests complete")
