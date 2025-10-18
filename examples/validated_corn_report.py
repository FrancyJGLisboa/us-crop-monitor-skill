#!/usr/bin/env python3
"""
Exemplo: Relatório de Milho com Validações

Demonstra como usar current_condition_report() com o sistema de validação integrado.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from analyze_crops import current_condition_report


def main():
    print("="*70)
    print(" RELATÓRIO DE CONDIÇÕES DO MILHO - COM VALIDAÇÕES")
    print("="*70)
    print()

    # Buscar dados atuais de milho
    print("Buscando dados de milho para 2025...")
    report = current_condition_report('CORN', 2025)

    # Mostrar dados principais
    print()
    print(f"📊 MILHO - Semana #{report['week']}, {report['year']}")
    print()

    conditions = report['conditions']
    print("CONDIÇÕES NACIONAIS:")
    print(f"  Excelente: {conditions.get('EXCELLENT', 0):.1f}%")
    print(f"  Bom:       {conditions.get('GOOD', 0):.1f}%")
    print(f"  Regular:   {conditions.get('FAIR', 0):.1f}%")
    print(f"  Ruim:      {conditions.get('POOR', 0):.1f}%")
    print(f"  Muito Ruim: {conditions.get('VERY POOR', 0):.1f}%")
    print()
    print(f"→ BOM + EXCELENTE: {conditions.get('good_excellent', 0):.1f}%")
    print()

    # Mostrar top estados
    if report.get('top_states'):
        print("TOP 5 ESTADOS:")
        for i, state in enumerate(report['top_states'][:5], 1):
            print(f"  {i}. {state['state_name']:20} {state['good_excellent']:.1f}%")
        print()

    # Mostrar seção de validações
    print("="*70)
    print(" VALIDAÇÕES")
    print("="*70)
    print()

    validation = report['validation']

    # Summary badge
    print(f"Status: {validation['summary']}")
    print()

    # Formatted validation section
    print(validation['formatted'])

    # Check if should block
    if validation['should_block']:
        print()
        print("🚫 AVISO: Problemas críticos detectados!")
        print(validation['blocking_message'])
    else:
        print("✅ Dados validados e aprovados para uso")

    print()
    print("="*70)


if __name__ == "__main__":
    main()
