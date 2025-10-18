#!/usr/bin/env python3
"""
Exemplo: Tratamento de Validação Crítica

Demonstra como o sistema detecta e bloqueia dados problemáticos,
como quando há uma grande discrepância temporal.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from analyze_crops import current_condition_report, AnalysisError


def demo_critical_scenario():
    """Demonstra cenário que acionaria bloqueio crítico."""
    print("="*70)
    print(" DEMONSTRAÇÃO: BLOQUEIO POR VALIDAÇÃO CRÍTICA")
    print("="*70)
    print()

    print("Cenário: Tentando buscar dados muito antigos (2022)")
    print()

    try:
        # Tentar buscar dados de 2022 (3 anos atrás)
        report = current_condition_report('CORN', 2022)

        # Verificar validações
        validation = report['validation']

        print(f"Status de Validação: {validation['summary']}")
        print()

        if validation['should_block']:
            print("🚫 BLOQUEIO ATIVADO!")
            print()
            print(validation['blocking_message'])
            print()
            print("O sistema detectou que os dados são muito antigos e bloqueou")
            print("a exibição automática. Você pode optar por continuar se necessário.")
            print()

            # Simular resposta do usuário
            print("Deseja continuar mesmo assim? (simulado: não)")
            print()
            print("✅ Operação abortada com segurança.")

        else:
            print("✅ Dados aprovados (não deveria chegar aqui com dados de 2022)")

    except AnalysisError as e:
        print(f"❌ Erro ao buscar dados: {e}")

    print()
    print("="*70)


def demo_warning_scenario():
    """Demonstra cenário com avisos mas não bloqueio."""
    print()
    print("="*70)
    print(" DEMONSTRAÇÃO: AVISOS SEM BLOQUEIO")
    print("="*70)
    print()

    print("Cenário: Dados com avisos mas ainda utilizáveis")
    print()

    try:
        # Buscar dados atuais (podem ter avisos mas não bloqueio)
        report = current_condition_report('CORN', 2025)

        validation = report['validation']

        print(f"Status: {validation['summary']}")
        print()

        if not validation['should_block']:
            print("✅ Dados aprovados para uso")
            print()
            print("Avisos encontrados (se houver):")
            print(validation['formatted'])
            print()
            print("Os dados são utilizáveis, mas os avisos fornecem contexto importante.")
        else:
            print("🚫 Bloqueio ativado")

    except AnalysisError as e:
        print(f"❌ Erro: {e}")

    print()
    print("="*70)


def main():
    print()
    print("Este exemplo demonstra o sistema de validação em ação,")
    print("incluindo como ele protege contra uso de dados problemáticos.")
    print()

    # Demonstração 1: Bloqueio crítico
    demo_critical_scenario()

    # Demonstração 2: Avisos sem bloqueio
    demo_warning_scenario()

    print()
    print("="*70)
    print(" RESUMO")
    print("="*70)
    print()
    print("O sistema de validação fornece:")
    print("  ✅ Transparência sobre idade e fonte dos dados")
    print("  ⚠️  Alertas sobre possíveis problemas")
    print("  ❌ Detecção de erros graves")
    print("  🚫 Bloqueio de dados críticos (com opção de override)")
    print()


if __name__ == "__main__":
    main()
