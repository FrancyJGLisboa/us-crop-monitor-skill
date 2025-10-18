#!/usr/bin/env python3
"""
Validation Formatter

Formats validation reports for visual display.

Author: Enhanced by Claude
Version: 2.0.0
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


def format_validation_section(
    report: Any,  # ValidationReport
    config: Optional[Dict[str, Any]] = None,
    verbose: bool = False
) -> str:
    """
    Format validation report as visual section.

    Args:
        report: ValidationReport
        config: Display configuration
        verbose: Show all details

    Returns:
        Formatted string
    """
    if not report.results:
        return "✅ Nenhuma validação executada"

    config = config or {}
    display_config = config.get("display", {})

    show_info = display_config.get("show_info", True) or verbose
    show_warnings = display_config.get("show_warnings", True)
    show_summary = display_config.get("show_validation_summary", True)

    lines = []

    # Summary line
    if show_summary:
        lines.append(f"📊 Validações: {report.get_summary_line()}")
        lines.append("")

    # Group by severity
    from data_validator import Severity

    criticals = report.get_by_severity(Severity.CRITICAL)
    errors = report.get_by_severity(Severity.ERROR)
    warnings = report.get_by_severity(Severity.WARNING)
    infos = report.get_by_severity(Severity.INFO)

    # Show criticals first (always)
    if criticals:
        lines.append("🚫 PROBLEMAS CRÍTICOS:")
        for result in criticals:
            lines.append(f"  {result.icon} {result.message}")
            if verbose and result.details:
                for key, value in result.details.items():
                    lines.append(f"      {key}: {value}")
        lines.append("")

    # Show errors (always)
    if errors:
        lines.append("❌ ERROS:")
        for result in errors:
            lines.append(f"  {result.icon} {result.message}")
            if verbose and result.details:
                for key, value in result.details.items():
                    lines.append(f"      {key}: {value}")
        lines.append("")

    # Show warnings (if enabled)
    if warnings and show_warnings:
        lines.append("⚠️  AVISOS:")
        for result in warnings:
            lines.append(f"  {result.icon} {result.message}")
            if verbose and result.details:
                for key, value in result.details.items():
                    lines.append(f"      {key}: {value}")
        lines.append("")

    # Show info (if enabled and verbose)
    if infos and show_info:
        lines.append("ℹ️  INFORMAÇÕES:")
        for result in infos:
            lines.append(f"  {result.icon} {result.message}")
        lines.append("")

    return "\n".join(lines)


def format_inline_alerts(
    report: Any,  # ValidationReport
    max_inline: int = 3
) -> List[str]:
    """
    Format top N alerts as inline messages.

    Args:
        report: ValidationReport
        max_inline: Maximum number to show inline

    Returns:
        List of formatted alert strings
    """
    from data_validator import Severity

    alerts = []

    # Prioritize critical and errors
    critical_and_errors = (
        report.get_by_severity(Severity.CRITICAL) +
        report.get_by_severity(Severity.ERROR)
    )

    for result in critical_and_errors[:max_inline]:
        alerts.append(f"{result.icon} {result.message}")

    # Fill with warnings if space
    if len(alerts) < max_inline:
        warnings = report.get_by_severity(Severity.WARNING)
        remaining = max_inline - len(alerts)
        for result in warnings[:remaining]:
            alerts.append(f"{result.icon} {result.message}")

    return alerts


def format_summary_badge(report: Any) -> str:
    """
    Format validation summary as compact badge.

    Args:
        report: ValidationReport

    Returns:
        Badge string like "✅ 15 | ⚠️ 2"
    """
    return report.get_summary_line()


def format_detailed_report(
    report: Any,
    title: str = "RELATÓRIO DE VALIDAÇÃO"
) -> str:
    """
    Format complete detailed validation report.

    Args:
        report: ValidationReport
        title: Report title

    Returns:
        Formatted detailed report
    """
    lines = [
        "",
        "=" * 70,
        f" {title}",
        "=" * 70,
        ""
    ]

    if not report.results:
        lines.append("✅ Nenhum problema encontrado - todos os dados validados")
        lines.append("")
        lines.append("=" * 70)
        return "\n".join(lines)

    # Summary
    counts = report.get_summary_counts()
    lines.append(f"Total de validações: {counts['total']}")
    lines.append(f"  🚫 Críticos: {counts['critical']}")
    lines.append(f"  ❌ Erros: {counts['error']}")
    lines.append(f"  ⚠️  Avisos: {counts['warning']}")
    lines.append(f"  ℹ️  Informações: {counts['info']}")
    lines.append("")
    lines.append("-" * 70)
    lines.append("")

    # Group by category
    from data_validator import Severity

    categories = {}
    for result in report.results:
        if result.category not in categories:
            categories[result.category] = []
        categories[result.category].append(result)

    # Display by category
    for category, results in sorted(categories.items()):
        lines.append(f"📂 {category.upper()}")
        lines.append("")

        for result in results:
            lines.append(f"  {result.icon} [{result.severity.value}] {result.message}")

            if result.details:
                lines.append("      Detalhes:")
                for key, value in result.details.items():
                    # Handle lists
                    if isinstance(value, list):
                        lines.append(f"        {key}:")
                        for item in value[:5]:  # Max 5 items
                            lines.append(f"          - {item}")
                        if len(value) > 5:
                            lines.append(f"          ... e mais {len(value) - 5}")
                    else:
                        lines.append(f"        {key}: {value}")

            lines.append("")

        lines.append("")

    lines.append("=" * 70)
    lines.append("")

    return "\n".join(lines)


def should_show_validation_section(report: Any, config: Dict[str, Any]) -> bool:
    """
    Determine if validation section should be shown.

    Args:
        report: ValidationReport
        config: Configuration

    Returns:
        True if should show section
    """
    display_config = config.get("display", {})

    # Always show if there are criticals or errors
    if report.has_critical or report.has_errors:
        return True

    # Show if warnings and warnings are enabled
    if report.has_warnings and display_config.get("show_warnings", True):
        return True

    # Show if verbose mode
    if display_config.get("verbose_mode", False):
        return True

    return False


if __name__ == "__main__":
    # Test
    print("Testing validation_formatter...")

    from data_validator import ValidationReport, Severity, ValidationResult

    # Create test report
    report = ValidationReport()

    report.add(ValidationResult(
        Severity.INFO,
        "metadata",
        "Dados buscados há 2 horas"
    ))

    report.add(ValidationResult(
        Severity.INFO,
        "temporal",
        "Dados são do ano atual (2024)"
    ))

    report.add(ValidationResult(
        Severity.WARNING,
        "temporal",
        "Dados têm 25 dias de idade",
        {"age_days": 25, "recommendation": "Verificar atualizações"}
    ))

    report.add(ValidationResult(
        Severity.ERROR,
        "completeness",
        "Categoria POOR ausente",
        {"missing": ["POOR"], "present": ["EXCELLENT", "GOOD", "FAIR", "VERY POOR"]}
    ))

    report.add(ValidationResult(
        Severity.CRITICAL,
        "temporal",
        "Ano solicitado (2025) != ano retornado (2024)",
        {
            "year_requested": 2025,
            "year_returned": 2024,
            "possible_reasons": ["Dados de 2025 não disponíveis", "Erro na API"]
        }
    ))

    # Test different formats
    print("\n" + "="*70)
    print("1. SUMMARY BADGE:")
    print(format_summary_badge(report))

    print("\n" + "="*70)
    print("2. INLINE ALERTS (max 3):")
    for alert in format_inline_alerts(report, max_inline=3):
        print(f"  {alert}")

    print("\n" + "="*70)
    print("3. VALIDATION SECTION:")
    print(format_validation_section(report, verbose=False))

    print("\n" + "="*70)
    print("4. DETAILED REPORT:")
    print(format_detailed_report(report))

    print("\n✓ Validation formatter tests complete")
