#!/usr/bin/env python3
"""
Data Validator - Central Orchestrator

Coordinates all validation layers and manages severity-based blocking.

Author: Enhanced by Claude
Version: 2.0.0
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Severity(Enum):
    """Validation severity levels."""
    INFO = "INFO"           # Informational, no action needed
    WARNING = "WARNING"     # Attention needed, but not critical
    ERROR = "ERROR"         # Serious problem, data still usable
    CRITICAL = "CRITICAL"   # Severe problem, should block


@dataclass
class ValidationResult:
    """Result of a single validation check."""
    severity: Severity
    category: str  # e.g., "temporal", "completeness", "anomaly"
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def icon(self) -> str:
        """Get visual icon for severity."""
        return {
            Severity.INFO: "ℹ️",
            Severity.WARNING: "⚠️",
            Severity.ERROR: "❌",
            Severity.CRITICAL: "🚫"
        }[self.severity]

    def __str__(self) -> str:
        """Format as readable string."""
        detail_str = ""
        if self.details:
            detail_str = "\n    " + "\n    ".join(
                f"{k}: {v}" for k, v in self.details.items()
            )
        return f"{self.icon} {self.severity.value}: {self.message}{detail_str}"


@dataclass
class ValidationReport:
    """Consolidated validation report."""
    results: List[ValidationResult] = field(default_factory=list)
    data_metadata: Dict[str, Any] = field(default_factory=dict)

    def add(self, result: ValidationResult) -> None:
        """Add validation result."""
        self.results.append(result)
        logger.debug(f"Added validation: {result.severity.value} - {result.message}")

    def add_info(self, category: str, message: str, **details) -> None:
        """Add INFO level result."""
        self.add(ValidationResult(Severity.INFO, category, message, details or None))

    def add_warning(self, category: str, message: str, **details) -> None:
        """Add WARNING level result."""
        self.add(ValidationResult(Severity.WARNING, category, message, details or None))

    def add_error(self, category: str, message: str, **details) -> None:
        """Add ERROR level result."""
        self.add(ValidationResult(Severity.ERROR, category, message, details or None))

    def add_critical(self, category: str, message: str, **details) -> None:
        """Add CRITICAL level result."""
        self.add(ValidationResult(Severity.CRITICAL, category, message, details or None))

    @property
    def has_critical(self) -> bool:
        """Check if report has critical issues."""
        return any(r.severity == Severity.CRITICAL for r in self.results)

    @property
    def has_errors(self) -> bool:
        """Check if report has errors."""
        return any(r.severity == Severity.ERROR for r in self.results)

    @property
    def has_warnings(self) -> bool:
        """Check if report has warnings."""
        return any(r.severity == Severity.WARNING for r in self.results)

    def get_by_severity(self, severity: Severity) -> List[ValidationResult]:
        """Get all results of specific severity."""
        return [r for r in self.results if r.severity == severity]

    def get_summary_counts(self) -> Dict[str, int]:
        """Get count of each severity level."""
        counts = {
            "info": 0,
            "warning": 0,
            "error": 0,
            "critical": 0,
            "total": len(self.results)
        }
        for result in self.results:
            if result.severity == Severity.INFO:
                counts["info"] += 1
            elif result.severity == Severity.WARNING:
                counts["warning"] += 1
            elif result.severity == Severity.ERROR:
                counts["error"] += 1
            elif result.severity == Severity.CRITICAL:
                counts["critical"] += 1
        return counts

    def get_summary_line(self) -> str:
        """Get one-line summary with icons and counts."""
        counts = self.get_summary_counts()

        # Only show non-zero counts
        parts = []
        if counts["info"] > 0:
            parts.append(f"ℹ️ {counts['info']}")
        if counts["warning"] > 0:
            parts.append(f"⚠️ {counts['warning']}")
        if counts["error"] > 0:
            parts.append(f"❌ {counts['error']}")
        if counts["critical"] > 0:
            parts.append(f"🚫 {counts['critical']}")

        if not parts:
            return "✅ Todas validações aprovadas"

        return " | ".join(parts)

    def should_block(self) -> bool:
        """Determine if execution should be blocked."""
        return self.has_critical

    def get_blocking_message(self) -> str:
        """Get detailed message for blocking scenario."""
        if not self.has_critical:
            return ""

        critical_issues = self.get_by_severity(Severity.CRITICAL)

        lines = [
            "",
            "🚫 VALIDAÇÃO CRÍTICA FALHOU",
            "━" * 60,
            ""
        ]

        for i, issue in enumerate(critical_issues, 1):
            lines.append(f"PROBLEMA #{i}: {issue.message}")
            if issue.details:
                lines.append("")
                lines.append("DETALHES:")
                for key, value in issue.details.items():
                    lines.append(f"  - {key}: {value}")
            lines.append("")

        lines.extend([
            "━" * 60,
            "",
            "Os dados não podem ser exibidos devido a problemas críticos.",
            "Verifique as informações acima e tente novamente.",
            ""
        ])

        return "\n".join(lines)


class DataValidator:
    """
    Central validator that orchestrates all validation layers.

    Coordinates:
    - Temporal validation
    - Completeness validation
    - Anomaly detection
    - Metadata enrichment
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize validator.

        Args:
            config: Configuration dict (uses defaults if None)
        """
        self.config = config or self._default_config()
        self.validators: List[Callable] = []
        logger.info("DataValidator initialized")

    @staticmethod
    def _default_config() -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "temporal": {
                "max_age_warning_days": 30,
                "max_age_error_days": 90,
                "max_age_critical_years": 2,
                "crop_seasons": {
                    "CORN": {"start_week": 18, "end_week": 44},
                    "SOYBEANS": {"start_week": 18, "end_week": 44},
                    "WHEAT": {"start_week": 14, "end_week": 28}
                }
            },
            "anomaly": {
                "max_week_change_warning": 20,
                "max_week_change_critical": 50,
                "sigma_threshold": 3.0
            },
            "completeness": {
                "require_all_categories": True,
                "required_categories": ["EXCELLENT", "GOOD", "FAIR", "POOR", "VERY POOR"],
                "major_producer_threshold_pct": 5.0
            },
            "display": {
                "show_info": True,
                "show_warnings": True,
                "show_validation_summary": True,
                "verbose_mode": False
            }
        }

    def register_validator(self, validator_func: Callable) -> None:
        """
        Register a validation function.

        Args:
            validator_func: Function that takes (data, report, config) and updates report
        """
        self.validators.append(validator_func)
        logger.debug(f"Registered validator: {validator_func.__name__}")

    def validate(
        self,
        data: Any,
        data_type: str = "crop_conditions",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ValidationReport:
        """
        Run all validations on data.

        Args:
            data: Data to validate (DataFrame, dict, etc.)
            data_type: Type of data being validated
            metadata: Additional metadata about the data

        Returns:
            ValidationReport with all results
        """
        report = ValidationReport()
        report.data_metadata = metadata or {}

        logger.info(f"Starting validation for {data_type}")

        # Run all registered validators
        for validator in self.validators:
            try:
                validator(data, report, self.config)
            except Exception as e:
                logger.error(f"Validator {validator.__name__} failed: {e}")
                report.add_error(
                    "system",
                    f"Validation function {validator.__name__} failed",
                    error=str(e)
                )

        logger.info(f"Validation complete: {report.get_summary_line()}")

        return report

    def validate_and_check(
        self,
        data: Any,
        data_type: str = "crop_conditions",
        metadata: Optional[Dict[str, Any]] = None,
        interactive: bool = True
    ) -> tuple[bool, ValidationReport]:
        """
        Validate data and determine if should proceed.

        Args:
            data: Data to validate
            data_type: Type of data
            metadata: Additional metadata
            interactive: If True, can prompt user for confirmation

        Returns:
            (should_proceed, validation_report)
        """
        report = self.validate(data, data_type, metadata)

        if not report.should_block():
            return True, report

        # Has critical issues
        if not interactive:
            logger.warning("Critical issues found but non-interactive mode")
            return False, report

        # Show blocking message
        print(report.get_blocking_message())

        # Ask for confirmation
        try:
            response = input("Deseja continuar mesmo assim? (sim/não): ").strip().lower()
            should_proceed = response in ['sim', 's', 'yes', 'y']
        except (EOFError, KeyboardInterrupt):
            should_proceed = False

        if should_proceed:
            logger.warning("User chose to proceed despite critical issues")
        else:
            logger.info("User chose to abort due to critical issues")

        return should_proceed, report


def create_default_validator() -> DataValidator:
    """
    Create validator with default configuration and all validators registered.

    Returns:
        Configured DataValidator instance
    """
    validator = DataValidator()

    # Validators will be registered in other modules
    # This is just the orchestrator

    return validator


if __name__ == "__main__":
    # Test validator
    print("Testing DataValidator...")

    # Create validator
    validator = DataValidator()

    # Create test report
    report = ValidationReport()
    report.add_info("test", "This is informational")
    report.add_warning("test", "This is a warning", detail1="value1")
    report.add_error("test", "This is an error")

    print("\nSummary:", report.get_summary_line())
    print("\nShould block:", report.should_block())

    # Test critical
    report.add_critical("test", "Critical issue!", year_requested=2025, year_returned=2023)
    print("\nAfter adding critical:")
    print("Should block:", report.should_block())
    print(report.get_blocking_message())

    print("\n✓ DataValidator tests complete")
