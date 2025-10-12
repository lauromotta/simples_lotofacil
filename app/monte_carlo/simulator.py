"""
Simulação Monte Carlo para Lotofácil.

Monte Carlo é uma técnica de simulação estatística que executa
milhares de experimentos aleatórios para estimar distribuições
de probabilidade e resultados esperados.

Para loteria:
1. Simula N sorteios aleatórios (ex: 10.000)
2. Testa portfolio contra cada sorteio simulado
3. Calcula distribuição de prêmios e lucros
4. Estima probabilidades de diferentes cenários

Útil para:
- Entender variância e risco
- Estimar cenários best/worst/average case
- Calcular Value at Risk (VaR)
- Validar Expected Value teórico
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import numpy as np
from collections import defaultdict, Counter

from app.core.game import Game
from app.core.combinatorics import gerar_jogo_aleatorio, calcular_acertos, TAMANHO_JOGO


# Tabela de prêmios (valores médios)
PREMIO_MEDIO = {
    15: 1_500_000.0,
    14: 1_500.0,
    13: 25.0,
    12: 10.0,
    11: 5.0,
}

CUSTO_JOGO = 3.0


@dataclass
class SimulationResult:
    """
    Resultado de uma simulação Monte Carlo.

    Attributes:
        n_simulations: Quantidade de simulações executadas
        n_games: Quantidade de jogos no portfolio
        total_cost: Custo total do portfolio
        lucros: Lista de lucros em cada simulação
        premios: Lista de prêmios em cada simulação
        acertos_distribution: Distribuição de acertos {11: [100, 95, ...], ...}
        percentiles: Percentis de lucro (5%, 25%, 50%, 75%, 95%)
        expected_profit: Lucro esperado (média)
        expected_roi: ROI esperado (%)
        probability_profit: Probabilidade de lucro > 0
        probability_breakeven: Probabilidade de empate
        var_95: Value at Risk 95% (máxima perda em 95% dos casos)
        best_case: Melhor caso (máximo lucro)
        worst_case: Pior caso (máximo prejuízo)
    """

    n_simulations: int
    n_games: int
    total_cost: float
    lucros: List[float] = field(default_factory=list)
    premios: List[float] = field(default_factory=list)
    acertos_distribution: Dict[int, List[int]] = field(default_factory=dict)
    percentiles: Dict[str, float] = field(default_factory=dict)
    expected_profit: float = 0.0
    expected_roi: float = 0.0
    probability_profit: float = 0.0
    probability_breakeven: float = 0.0
    var_95: float = 0.0
    best_case: float = 0.0
    worst_case: float = 0.0

    def __str__(self) -> str:
        return (
            f"SimulationResult(\n"
            f"  Simulações: {self.n_simulations:,}\n"
            f"  Jogos: {self.n_games}\n"
            f"  Custo: R$ {self.total_cost:.2f}\n"
            f"  Lucro esperado: R$ {self.expected_profit:.2f}\n"
            f"  ROI esperado: {self.expected_roi:.2f}%\n"
            f"  P(Lucro > 0): {self.probability_profit:.2f}%\n"
            f"  VaR 95%: R$ {self.var_95:.2f}\n"
            f"  Melhor caso: R$ {self.best_case:.2f}\n"
            f"  Pior caso: R$ {self.worst_case:.2f}\n"
            f")"
        )


class MonteCarloSimulator:
    """
    Simulador Monte Carlo para loteria.

    Executa milhares de simulações para estimar distribuição
    de resultados de um portfolio de jogos.

    Examples:
        >>> from app.strategies import RandomPureStrategy, StrategyConfig
        >>> strategy = RandomPureStrategy()
        >>> result = strategy.generate(StrategyConfig(n_games=10, seed=42))
        >>>
        >>> simulator = MonteCarloSimulator()
        >>> sim_result = simulator.run(result.games, n_simulations=10000, seed=123)
        >>> print(f"ROI esperado: {sim_result.expected_roi:.2f}%")
        >>> print(f"P(Lucro): {sim_result.probability_profit:.2f}%")
    """

    def __init__(self, premio_table: Optional[Dict[int, float]] = None):
        """
        Inicializa o simulador.

        Args:
            premio_table: Tabela customizada de prêmios (opcional)
        """
        self.premio_table = premio_table or PREMIO_MEDIO

    def run(
        self,
        games: List[Game],
        n_simulations: int = 10000,
        seed: Optional[int] = None,
        progress_callback: Optional[callable] = None,
    ) -> SimulationResult:
        """
        Executa simulação Monte Carlo.

        Args:
            games: Portfolio de jogos a simular
            n_simulations: Quantidade de simulações (padrão: 10.000)
            seed: Seed para reprodutibilidade
            progress_callback: Função chamada a cada N simulações
                              Signature: callback(current, total)

        Returns:
            SimulationResult com estatísticas completas

        Examples:
            >>> simulator = MonteCarloSimulator()
            >>> result = simulator.run(games, n_simulations=10000, seed=42)
        """
        if not games:
            raise ValueError("Lista de jogos não pode estar vazia")

        if n_simulations <= 0:
            raise ValueError("n_simulations deve ser > 0")

        if seed is not None:
            np.random.seed(seed)

        # Calcular custo total
        total_cost = len(games) * CUSTO_JOGO

        # Armazenar resultados
        lucros = []
        premios = []
        acertos_dist = defaultdict(list)

        # Executar simulações
        for sim in range(n_simulations):
            # Simular um sorteio aleatório
            sorteio = gerar_jogo_aleatorio(seed=None)

            # Testar todos os jogos contra este sorteio
            premio_total = 0.0
            acertos_sim = []

            for game in games:
                # Calcular acertos
                acertos = calcular_acertos(game.numbers, sorteio)
                acertos_sim.append(acertos)

                # Calcular prêmio
                premio = self.premio_table.get(acertos, 0.0)
                premio_total += premio

            # Calcular lucro
            lucro = premio_total - total_cost

            # Armazenar
            lucros.append(lucro)
            premios.append(premio_total)

            # Contar acertos
            acertos_count = Counter(acertos_sim)
            for pts, count in acertos_count.items():
                acertos_dist[pts].append(count)

            # Callback de progresso
            if progress_callback and (sim + 1) % 1000 == 0:
                progress_callback(sim + 1, n_simulations)

        # Calcular estatísticas
        lucros_array = np.array(lucros)
        premios_array = np.array(premios)

        # Expected values
        expected_profit = float(np.mean(lucros_array))
        expected_roi = (expected_profit / total_cost * 100) if total_cost > 0 else 0.0

        # Percentis
        percentiles = {
            "p5": float(np.percentile(lucros_array, 5)),
            "p25": float(np.percentile(lucros_array, 25)),
            "p50": float(np.percentile(lucros_array, 50)),  # Mediana
            "p75": float(np.percentile(lucros_array, 75)),
            "p95": float(np.percentile(lucros_array, 95)),
        }

        # Probabilidades
        prob_profit = float(np.sum(lucros_array > 0) / len(lucros_array) * 100)
        prob_breakeven = float(np.sum(lucros_array == 0) / len(lucros_array) * 100)

        # Value at Risk (95%)
        var_95 = float(np.percentile(lucros_array, 5))  # Pior 5% dos casos

        # Best/Worst case
        best_case = float(np.max(lucros_array))
        worst_case = float(np.min(lucros_array))

        return SimulationResult(
            n_simulations=n_simulations,
            n_games=len(games),
            total_cost=total_cost,
            lucros=lucros,
            premios=premios,
            acertos_distribution=dict(acertos_dist),
            percentiles=percentiles,
            expected_profit=expected_profit,
            expected_roi=expected_roi,
            probability_profit=prob_profit,
            probability_breakeven=prob_breakeven,
            var_95=var_95,
            best_case=best_case,
            worst_case=worst_case,
        )

    def compare_portfolios(
        self,
        portfolios: Dict[str, List[Game]],
        n_simulations: int = 10000,
        seed: Optional[int] = None,
    ) -> Dict[str, SimulationResult]:
        """
        Compara múltiplos portfolios via Monte Carlo.

        Args:
            portfolios: Dicionário {nome: lista_de_jogos}
            n_simulations: Quantidade de simulações
            seed: Seed para reprodutibilidade

        Returns:
            Dicionário {nome: SimulationResult}

        Examples:
            >>> portfolios = {
            ...     "small": games_10,
            ...     "large": games_100,
            ... }
            >>> comparison = simulator.compare_portfolios(portfolios, n_simulations=5000)
        """
        results = {}

        for i, (name, games) in enumerate(portfolios.items()):
            # Usar seed diferente para cada portfolio
            portfolio_seed = (seed + i * 1000) if seed is not None else None

            result = self.run(
                games,
                n_simulations=n_simulations,
                seed=portfolio_seed,
            )

            results[name] = result

        return results


# ============================================================================
# SCRIPT DE DEMONSTRAÇÃO
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("MONTE CARLO SIMULATOR - Demonstração")
    print("=" * 70)

    # 1. Gerar portfolio de teste
    print("\n📦 Gerando portfolio de teste...")
    from app.strategies import RandomPureStrategy, StrategyConfig

    strategy = RandomPureStrategy()
    result = strategy.generate(StrategyConfig(n_games=10, seed=42))

    print(f"   Jogos: {result.n_games}")
    print(f"   Custo: R$ {result.total_cost:.2f}")

    # 2. Executar simulação
    print("\n🎲 Executando simulação Monte Carlo (10.000 simulações)...")

    def progress(current, total):
        if current % 2000 == 0:
            pct = current / total * 100
            print(f"   Progresso: {current:,}/{total:,} ({pct:.0f}%)")

    simulator = MonteCarloSimulator()
    sim_result = simulator.run(
        result.games,
        n_simulations=10000,
        seed=123,
        progress_callback=progress,
    )

    print("\n✅ Simulação completa!")

    # 3. Resultados
    print("\n📊 Resultados:")
    print(f"   Simulações: {sim_result.n_simulations:,}")
    print(f"   Jogos: {sim_result.n_games}")
    print(f"   Custo total: R$ {sim_result.total_cost:.2f}")
    print(f"\n   Lucro esperado: R$ {sim_result.expected_profit:.2f}")
    print(f"   ROI esperado: {sim_result.expected_roi:.2f}%")
    print(f"\n   P(Lucro > 0): {sim_result.probability_profit:.2f}%")
    print(f"   P(Empate): {sim_result.probability_breakeven:.2f}%")
    print(f"   P(Prejuízo): {100 - sim_result.probability_profit - sim_result.probability_breakeven:.2f}%")

    # 4. Percentis
    print(f"\n📈 Distribuição de Lucro:")
    print(f"   P5  (pior 5%):  R$ {sim_result.percentiles['p5']:.2f}")
    print(f"   P25 (Q1):       R$ {sim_result.percentiles['p25']:.2f}")
    print(f"   P50 (mediana):  R$ {sim_result.percentiles['p50']:.2f}")
    print(f"   P75 (Q3):       R$ {sim_result.percentiles['p75']:.2f}")
    print(f"   P95 (top 5%):   R$ {sim_result.percentiles['p95']:.2f}")

    # 5. Cenários
    print(f"\n🎯 Cenários:")
    print(f"   Melhor caso:  R$ {sim_result.best_case:.2f}")
    print(f"   Pior caso:    R$ {sim_result.worst_case:.2f}")
    print(f"   VaR 95%:      R$ {sim_result.var_95:.2f}")

    # 6. Distribuição de acertos
    print(f"\n🎰 Média de Acertos (por simulação):")
    for pts in sorted(sim_result.acertos_distribution.keys()):
        counts = sim_result.acertos_distribution[pts]
        avg_count = np.mean(counts) if counts else 0
        print(f"   {pts} pontos: {avg_count:.2f} jogos em média")

    # 7. Comparar portfolios
    print(f"\n⚖️  Comparando portfolios de diferentes tamanhos...")

    # Portfolio pequeno (5 jogos)
    result_small = strategy.generate(StrategyConfig(n_games=5, seed=42))

    # Portfolio grande (20 jogos)
    result_large = strategy.generate(StrategyConfig(n_games=20, seed=42))

    portfolios = {
        "small_5": result_small.games,
        "medium_10": result.games,
        "large_20": result_large.games,
    }

    comparison = simulator.compare_portfolios(portfolios, n_simulations=5000, seed=456)

    print(f"\n📊 Comparação:")
    print(f"   Portfolio    | Custo    | ROI Esp. | P(Lucro) | VaR 95%")
    print(f"   -------------+----------+----------+----------+----------")
    for name, res in comparison.items():
        print(
            f"   {name:12} | R$ {res.total_cost:6.2f} | {res.expected_roi:7.2f}% | "
            f"{res.probability_profit:7.2f}% | R$ {res.var_95:7.2f}"
        )

    print("\n" + "=" * 70)
    print("✅ Monte Carlo Simulator implementado")
    print("=" * 70)
