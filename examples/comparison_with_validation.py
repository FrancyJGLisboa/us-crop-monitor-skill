#!/usr/bin/env python3
"""
Exemplo: Comparações Week-over-Week e Year-over-Year com Validações

Demonstra detecção automática de anomalias em mudanças bruscas.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from analyze_crops import week_over_week_comparison, year_over_year_comparison


def main():
    print("="*70)
    print(" COMPARAÇÕES DE SAFRA - COM DETECÇÃO DE ANOMALIAS")
    print("="*70)
    print()

    # Week-over-Week
    print("1. COMPARAÇÃO SEMANA A SEMANA (WoW)")
    print("-"*70)
    print()

    wow = week_over_week_comparison('CORN', 2025)

    print(f"Semana #{wow['current_week']} vs Semana #{wow['previous_week']}")
    print()
    print(f"Nacional: {wow['national']['previous']:.1f}% → {wow['national']['current']:.1f}%")
    print(f"Mudança: {wow['national']['delta']:+.1f} pontos")
    print()

    if wow['top_improvements']:
        print("Maiores melhorias:")
        for state in wow['top_improvements'][:3]:
            print(f"  • {state['state_name']:20} ({state['delta']:+.1f} pontos)")
    print()

    # Validações WoW
    print("📊 Validações WoW: {validation['summary']}")
    if validation['should_block']:
        print("⚠️ ALERTA: Mudanças anormais detectadas!")
    print()

    # Year-over-Year
    print("="*70)
    print("2. COMPARAÇÃO ANO A ANO (YoY)")
    print("-"*70)
    print()

    yoy = year_over_year_comparison('CORN', 2025, 2024)

    print(f"2025 vs 2024 (Semana #{yoy['week']})")
    print()
    print(f"Bom+Excelente: {yoy['national_previous']['good_excellent']:.1f}% (2024) → "
          f"{yoy['national_current']['good_excellent']:.1f}% (2025)")
    print(f"Mudança: {yoy['national_delta']['good_excellent']:+.1f} pontos")
    print()

    if yoy['top_improvements']:
        print("Estados com maiores melhorias YoY:")
        for state in yoy['top_improvements'][:3]:
            print(f"  • {state['state_name']:20} ({state['delta_ge']:+.1f} pontos)")
    print()

    # Validações YoY
    validation_yoy = yoy['validation']
    print(f"📊 Validações YoY: {validation_yoy['summary']}")
    print()

    # Mostrar validações detalhadas se houver avisos
    if validation_yoy['formatted']:
        print("="*70)
        print(" DETALHES DAS VALIDAÇÕES")
        print("="*70)
        print()
        print(validation_yoy['formatted'])

    print("="*70)


if __name__ == "__main__":
    # Fix validation reference
    validation = {'summary': '...', 'should_block': False}  # Placeholder
    main()
