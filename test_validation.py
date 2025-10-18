#!/usr/bin/env python3
"""
Test Validation System

Quick test of the new validation system with real data.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path('scripts')))
sys.path.insert(0, str(Path('scripts/utils')))

from fetch_nass import NassApiClient
from parse_conditions import parse_api_response, pivot_conditions_table, calculate_good_excellent
from data_validator import DataValidator
from temporal_validator import validate_temporal_consistency, validate_year_consistency
from completeness_validator import validate_completeness, validate_percentage_sum
from anomaly_detector import detect_anomalies
from validation_formatter import format_validation_section, format_detailed_report

def test_validation_system():
    """Test the complete validation system."""
    print("="*70)
    print(" TESTING VALIDATION SYSTEM")
    print("="*70)
    print()

    # Initialize
    client = NassApiClient()
    validator = DataValidator()

    # Fetch data for 2025 WITH metadata
    print("1. Fetching data for 2025...")
    try:
        result = client.get_crop_conditions_with_metadata(
            commodity='CORN',
            year=2025,
            agg_level='STATE'
        )

        data_list = result['data']
        metadata = result['metadata']

        print(f"   ✓ Fetched {len(data_list)} records")
        print(f"   ✓ Metadata: {metadata}")
        print()

        # Parse data
        print("2. Parsing data...")
        df = parse_api_response(data_list)
        df_pivot = pivot_conditions_table(df)
        df_final = calculate_good_excellent(df_pivot)
        print(f"   ✓ Parsed into {len(df_final)} rows")
        print()

        # Create validation report
        print("3. Running validations...")
        from data_validator import ValidationReport

        report = ValidationReport()
        report.data_metadata = metadata

        # Get config
        config = validator.config

        # Run validators
        validate_temporal_consistency(df_final, report, config)
        validate_year_consistency(2025, df_final, report, config)
        validate_completeness(df_final, report, config)
        validate_percentage_sum(df_final, report, tolerance=2.0)
        detect_anomalies(df_final, report, config)

        print(f"   ✓ Completed {len(report.results)} validations")
        print()

        # Show results
        print("="*70)
        print(" VALIDATION RESULTS")
        print("="*70)
        print()
        print(format_validation_section(report, config))

        # Check if should block
        if report.should_block():
            print("\n🚫 CRITICAL ISSUES DETECTED - Would block in production")
        else:
            print("\n✅ All validations passed or non-critical")

        # Show detailed report
        print("\n")
        print(format_detailed_report(report, "RELATÓRIO DETALHADO DE VALIDAÇÃO"))

    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_validation_system()
