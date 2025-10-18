#!/usr/bin/env python3
"""
Metadata Manager

Manages metadata and transparency information for crop data.

Author: Enhanced by Claude
Version: 2.0.0
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def enrich_with_metadata(
    data: pd.DataFrame,
    metadata: Dict[str, Any],
    report: Any  # ValidationReport
) -> pd.DataFrame:
    """
    Enrich data with metadata information.

    Args:
        data: DataFrame to enrich
        metadata: Metadata dict
        report: ValidationReport to add info to

    Returns:
        Enriched DataFrame
    """
    if data.empty:
        return data

    # Extract metadata info
    fetched_at = metadata.get('fetched_at')
    from_cache = metadata.get('from_cache', False)
    published_at = metadata.get('published_at')

    # Add informational messages to report
    if fetched_at:
        if isinstance(fetched_at, str):
            fetched_at = datetime.fromisoformat(fetched_at)

        age_str = _format_time_ago(fetched_at)
        report.add_info(
            "metadata",
            f"Dados buscados {age_str}"
        )

    source = "Cache" if from_cache else "API do USDA"
    report.add_info("metadata", f"Fonte: {source}")

    if published_at:
        if isinstance(published_at, str):
            published_at = datetime.fromisoformat(published_at)

        pub_age_str = _format_time_ago(published_at)
        report.add_info(
            "metadata",
            f"Publicado pelo USDA {pub_age_str}"
        )

    return data


def extract_publication_date(data: pd.DataFrame) -> Optional[datetime]:
    """
    Extract publication date from NASS data (load_time field).

    Args:
        data: DataFrame with NASS data

    Returns:
        Publication datetime or None
    """
    if data.empty or 'load_time' not in data.columns:
        return None

    load_time = data['load_time'].iloc[0]

    if pd.isna(load_time):
        return None

    try:
        return pd.to_datetime(load_time)
    except Exception as e:
        logger.warning(f"Could not parse load_time: {e}")
        return None


def calculate_data_age(week_ending: Optional[datetime]) -> Optional[int]:
    """
    Calculate age of data in days.

    Args:
        week_ending: Week ending date

    Returns:
        Age in days or None
    """
    if not week_ending:
        return None

    if isinstance(week_ending, str):
        week_ending = pd.to_datetime(week_ending)

    now = datetime.now()
    age = (now - week_ending).days

    return age


def _format_time_ago(dt: datetime) -> str:
    """
    Format datetime as human-readable 'time ago' string.

    Args:
        dt: Datetime to format

    Returns:
        String like "há 2 horas" or "há 3 dias"
    """
    now = datetime.now()
    delta = now - dt

    if delta.total_seconds() < 60:
        return "há menos de 1 minuto"
    elif delta.total_seconds() < 3600:
        minutes = int(delta.total_seconds() / 60)
        return f"há {minutes} minuto{'s' if minutes > 1 else ''}"
    elif delta.total_seconds() < 86400:
        hours = int(delta.total_seconds() / 3600)
        return f"há {hours} hora{'s' if hours > 1 else ''}"
    else:
        days = delta.days
        if days == 1:
            return "há 1 dia"
        elif days < 7:
            return f"há {days} dias"
        elif days < 30:
            weeks = days // 7
            return f"há {weeks} semana{'s' if weeks > 1 else ''}"
        elif days < 365:
            months = days // 30
            return f"há {months} {'mês' if months == 1 else 'meses'}"
        else:
            years = days // 365
            return f"há {years} ano{'s' if years > 1 else ''}"


def create_metadata_dict(
    fetched_at: Optional[datetime] = None,
    from_cache: bool = False,
    cached_at: Optional[datetime] = None,
    published_at: Optional[datetime] = None,
    **extra
) -> Dict[str, Any]:
    """
    Create standardized metadata dictionary.

    Args:
        fetched_at: When data was fetched from API
        from_cache: Whether data came from cache
        cached_at: When data was cached
        published_at: When USDA published the data
        **extra: Additional metadata fields

    Returns:
        Metadata dict
    """
    metadata = {
        'fetched_at': fetched_at or datetime.now(),
        'from_cache': from_cache,
        'version': '2.0.0'
    }

    if cached_at:
        metadata['cached_at'] = cached_at

    if published_at:
        metadata['published_at'] = published_at

    # Add any extra fields
    metadata.update(extra)

    return metadata


def add_metadata_to_report(
    report: Any,  # ValidationReport
    metadata: Dict[str, Any]
) -> None:
    """
    Add metadata information to validation report.

    Args:
        report: ValidationReport
        metadata: Metadata dict
    """
    # Store in report
    report.data_metadata.update(metadata)

    # Add as informational results
    fetched_at = metadata.get('fetched_at')
    if fetched_at and isinstance(fetched_at, datetime):
        age_str = _format_time_ago(fetched_at)
        report.add_info("metadata", f"Dados obtidos {age_str}")

    from_cache = metadata.get('from_cache', False)
    source = "cache local" if from_cache else "API do USDA"
    report.add_info("metadata", f"Fonte: {source}")

    published_at = metadata.get('published_at')
    if published_at and isinstance(published_at, datetime):
        pub_age = _format_time_ago(published_at)
        report.add_info("metadata", f"Publicado pelo USDA {pub_age}")


if __name__ == "__main__":
    # Test
    print("Testing metadata_manager...")

    # Test time ago formatting
    now = datetime.now()
    test_times = [
        now - timedelta(minutes=5),
        now - timedelta(hours=2),
        now - timedelta(days=3),
        now - timedelta(days=10),
        now - timedelta(days=45),
        now - timedelta(days=400)
    ]

    for dt in test_times:
        print(f"  {dt.strftime('%Y-%m-%d %H:%M')} -> {_format_time_ago(dt)}")

    # Test metadata creation
    metadata = create_metadata_dict(
        fetched_at=now - timedelta(hours=2),
        from_cache=True,
        cached_at=now - timedelta(days=1),
        published_at=now - timedelta(days=7),
        custom_field="test value"
    )

    print("\nCreated metadata:")
    for key, value in metadata.items():
        print(f"  {key}: {value}")

    print("\n✓ Metadata manager tests complete")
