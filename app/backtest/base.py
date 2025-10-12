"""
Sistema Base de Backtesting.

Este módulo implementa a infraestrutura base para backtesting de estratégias
de loteria usando dados históricos reais.

O backtesting permite:
- Avaliar performance de estratégias em dados passados
- Comparar diferentes abordagens
- Calcular métricas de retorno e risco
- Validar se uma estratégia teria sido lucrativa historicamente

IMPORTANTE: Performance passada NÃO garante resultados futuros!
O Expected Value da Lotofácil é NEGATIVO (~-53% ROI).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from collections import defaultdict

from app.core.game import Game
from app.core.combinatorics import calcular_acertos


# ============================================================================
# TABELA DE PRÊMIOS (valores médios históricos)
# ============================================================================

PREMIO_MEDIO = {
    15: 1_500_000.0,  # 15 acertos (prêmio principal)
    14: 1_500.0,      # 14 acertos
    13: 25.0,         # 13 acertos
    12: 10.0,         # 12 acertos
    11: 5.0,          # 11 acertos
}

CUSTO_JOGO = 3.0


@dataclass
class BacktestResult:
    """
    Resultado de um jogo individual no backtest.

    Attributes:
        game_id: ID do jogo
        concurso: Número do concurso testado
        numbers_game: Números do jogo
        numbers_draw: Números sorteados
        acertos: Quantidade de acertos
        premio: Valor do prêmio ganho
        lucro: Premio - custo
        roi: Return on Investment (%)
    """

    game_id: str
    concurso: int
    numbers_game: List[int]
    numbers_draw: List[int]
    acertos: int
    premio: float
    lucro: float
    roi: float


@dataclass
class PortfolioBacktest:
    """
    Resultado agregado de um portfolio testado contra vários sorteios.

    Attributes:
        portfolio_id: ID do portfolio
        strategy: Nome da estratégia
        n_games: Quantidade de jogos
        concursos_testados: Lista de concursos testados
        total_custo: Custo total do portfolio
        total_premio: Soma de todos os prêmios
        total_lucro: Premio - custo
        roi: ROI percentual
        acertos_distribution: Distribuição de acertos {11: 5, 12: 3, ...}
        best_result: Melhor resultado individual
        worst_result: Pior resultado individual
        win_rate: Taxa de vitória (jogos com premio > 0)
        results: Lista completa de resultados
    """

    portfolio_id: str
    strategy: str
    n_games: int
    concursos_testados: List[int]
    total_custo: float
    total_premio: float
    total_lucro: float
    roi: float
    acertos_distribution: Dict[int, int] = field(default_factory=dict)
    best_result: Optional[BacktestResult] = None
    worst_result: Optional[BacktestResult] = None
    win_rate: float = 0.0
    results: List[BacktestResult] = field(default_factory=list)

    def __str__(self) -> str:
        """String representation."""
        return (
            f"PortfolioBacktest(\n"
            f"  Portfolio: {self.portfolio_id}\n"
            f"  Estratégia: {self.strategy}\n"
            f"  Jogos: {self.n_games}\n"
            f"  Concursos testados: {len(self.concursos_testados)}\n"
            f"  Custo: R$ {self.total_custo:.2f}\n"
            f"  Premio: R$ {self.total_premio:.2f}\n"
            f"  Lucro: R$ {self.total_lucro:.2f}\n"
            f"  ROI: {self.roi:.2f}%\n"
            f"  Win rate: {self.win_rate:.2f}%\n"
            f")"
        )


class Backtester:
    """
    Motor de backtesting para avaliar estratégias com dados históricos.

    O Backtester:
    1. Recebe um portfolio de jogos
    2. Testa contra sorteios históricos
    3. Calcula acertos e prêmios
    4. Gera métricas de performance

    Examples:
        >>> from app.io.database import get_database, Draw
        >>> db = get_database("sqlite:///lotofacil.db")
        >>> session = db.get_session()
        >>>
        >>> # Buscar últimos 100 sorteios
        >>> draws = session.query(Draw).order_by(Draw.concurso.desc()).limit(100).all()
        >>>
        >>> # Gerar jogos (usando alguma estratégia)
        >>> from app.strategies import RandomPureStrategy, StrategyConfig
        >>> strategy = RandomPureStrategy()
        >>> result = strategy.generate(StrategyConfig(n_games=10, seed=42))
        >>>
        >>> # Backtest
        >>> backtester = Backtester()
        >>> bt_result = backtester.run(result.games, draws)
        >>> print(f"ROI: {bt_result.roi:.2f}%")
    """

    def __init__(self, premio_table: Optional[Dict[int, float]] = None):
        """
        Inicializa o backtester.

        Args:
            premio_table: Tabela customizada de prêmios (opcional)
                         Se None, usa PREMIO_MEDIO padrão
        """
        self.premio_table = premio_table or PREMIO_MEDIO

    def run(
        self,
        games: List[Game],
        draws: List,  # List[Draw] from database
        portfolio_id: Optional[str] = None,
        strategy: Optional[str] = None,
    ) -> PortfolioBacktest:
        """
        Executa backtest de um portfolio contra sorteios históricos.

        Args:
            games: Lista de jogos a testar
            draws: Lista de sorteios históricos (objetos Draw do DB)
            portfolio_id: ID do portfolio (opcional)
            strategy: Nome da estratégia (opcional)

        Returns:
            PortfolioBacktest com resultados completos
        """
        if not games:
            raise ValueError("Lista de jogos não pode estar vazia")

        if not draws:
            raise ValueError("Lista de sorteios não pode estar vazia")

        # Metadata
        portfolio_id = portfolio_id or f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        strategy = strategy or (games[0].strategy if hasattr(games[0], 'strategy') else "unknown")

        # Calcular custo total
        total_custo = len(games) * CUSTO_JOGO

        # Testar cada jogo contra cada sorteio
        all_results = []
        acertos_dist = defaultdict(int)
        total_premio = 0.0

        for draw in draws:
            # Extrair números sorteados
            if hasattr(draw, 'nums_15'):
                sorteio_nums = draw.nums_15
            else:
                # Fallback para dict
                sorteio_nums = draw.get('nums_15', [])

            concurso = draw.concurso if hasattr(draw, 'concurso') else draw.get('concurso', 0)

            for game in games:
                # Calcular acertos
                acertos = calcular_acertos(game.numbers, sorteio_nums)

                # Calcular prêmio
                premio = self.premio_table.get(acertos, 0.0)
                lucro = premio - CUSTO_JOGO
                roi = (lucro / CUSTO_JOGO * 100) if CUSTO_JOGO > 0 else 0.0

                # Criar resultado
                result = BacktestResult(
                    game_id=game.id or f"game_{id(game)}",
                    concurso=concurso,
                    numbers_game=game.numbers,
                    numbers_draw=sorteio_nums,
                    acertos=acertos,
                    premio=premio,
                    lucro=lucro,
                    roi=roi,
                )

                all_results.append(result)
                acertos_dist[acertos] += 1
                total_premio += premio

        # Calcular métricas agregadas
        total_lucro = total_premio - total_custo
        roi_total = (total_lucro / total_custo * 100) if total_custo > 0 else 0.0

        # Melhor e pior resultado
        best = max(all_results, key=lambda r: r.premio) if all_results else None
        worst = min(all_results, key=lambda r: r.premio) if all_results else None

        # Win rate (jogos com prêmio > 0)
        winners = sum(1 for r in all_results if r.premio > 0)
        win_rate = (winners / len(all_results) * 100) if all_results else 0.0

        # Concursos testados
        concursos = [draw.concurso if hasattr(draw, 'concurso') else draw.get('concurso', 0)
                     for draw in draws]

        return PortfolioBacktest(
            portfolio_id=portfolio_id,
            strategy=strategy,
            n_games=len(games),
            concursos_testados=concursos,
            total_custo=total_custo,
            total_premio=total_premio,
            total_lucro=total_lucro,
            roi=roi_total,
            acertos_distribution=dict(acertos_dist),
            best_result=best,
            worst_result=worst,
            win_rate=win_rate,
            results=all_results,
        )

    def compare_strategies(
        self,
        portfolios: Dict[str, List[Game]],
        draws: List,
    ) -> Dict[str, PortfolioBacktest]:
        """
        Compara múltiplas estratégias lado a lado.

        Args:
            portfolios: Dicionário {nome_estrategia: lista_de_jogos}
            draws: Lista de sorteios históricos

        Returns:
            Dicionário {nome_estrategia: PortfolioBacktest}

        Examples:
            >>> portfolios = {
            ...     "random_pure": games_pure,
            ...     "random_filtered": games_filtered,
            ... }
            >>> comparison = backtester.compare_strategies(portfolios, draws)
            >>> for name, result in comparison.items():
            ...     print(f"{name}: ROI = {result.roi:.2f}%")
        """
        results = {}

        for strategy_name, games in portfolios.items():
            result = self.run(
                games,
                draws,
                portfolio_id=f"{strategy_name}_backtest",
                strategy=strategy_name,
            )
            results[strategy_name] = result

        return results


# ============================================================================
# SCRIPT DE DEMONSTRAÇÃO
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("BACKTESTER - Demonstração")
    print("=" * 70)

    # 1. Criar jogos de teste
    print("\n📦 Criando jogos de teste...")
    from app.strategies import RandomPureStrategy, StrategyConfig

    strategy = RandomPureStrategy()
    config = StrategyConfig(n_games=5, seed=42)
    result = strategy.generate(config)

    print(f"   Gerados: {result.n_games} jogos")
    print(f"   Custo: R$ {result.total_cost:.2f}")

    # 2. Criar sorteios fictícios (simulando Draw do DB)
    print("\n🎲 Criando sorteios fictícios...")

    @dataclass
    class FakeDraw:
        concurso: int
        nums_15: List[int]

    # Sorteios de teste (alguns com overlap intencional)
    draws = [
        FakeDraw(3500, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]),
        FakeDraw(3501, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 16, 17]),
        FakeDraw(3502, [11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]),
    ]

    print(f"   Sorteios criados: {len(draws)}")

    # 3. Executar backtest
    print("\n🔬 Executando backtest...")
    backtester = Backtester()
    bt_result = backtester.run(result.games, draws)

    print(f"\n📊 Resultados:")
    print(f"   Portfolio: {bt_result.portfolio_id}")
    print(f"   Estratégia: {bt_result.strategy}")
    print(f"   Jogos: {bt_result.n_games}")
    print(f"   Concursos testados: {len(bt_result.concursos_testados)}")
    print(f"   Custo total: R$ {bt_result.total_custo:.2f}")
    print(f"   Premio total: R$ {bt_result.total_premio:.2f}")
    print(f"   Lucro: R$ {bt_result.total_lucro:.2f}")
    print(f"   ROI: {bt_result.roi:.2f}%")
    print(f"   Win rate: {bt_result.win_rate:.2f}%")

    # 4. Distribuição de acertos
    print(f"\n📈 Distribuição de Acertos:")
    for acertos, count in sorted(bt_result.acertos_distribution.items()):
        percentage = count / len(bt_result.results) * 100
        print(f"   {acertos} acertos: {count} vezes ({percentage:.1f}%)")

    # 5. Melhor e pior resultado
    if bt_result.best_result:
        print(f"\n🏆 Melhor Resultado:")
        print(f"   Concurso: {bt_result.best_result.concurso}")
        print(f"   Acertos: {bt_result.best_result.acertos}")
        print(f"   Premio: R$ {bt_result.best_result.premio:.2f}")

    if bt_result.worst_result:
        print(f"\n📉 Pior Resultado:")
        print(f"   Concurso: {bt_result.worst_result.concurso}")
        print(f"   Acertos: {bt_result.worst_result.acertos}")
        print(f"   Premio: R$ {bt_result.worst_result.premio:.2f}")

    # 6. Comparar estratégias
    print(f"\n⚖️  Comparando estratégias...")
    from app.strategies import RandomFilteredStrategy
    from app.filters import FilterChain, SumRangeFilter

    # Gerar segunda estratégia
    filters = FilterChain([SumRangeFilter(180, 210)])
    strategy2 = RandomFilteredStrategy()
    config2 = StrategyConfig(n_games=5, seed=42, filters=filters)
    result2 = strategy2.generate(config2)

    portfolios = {
        "random_pure": result.games,
        "random_filtered": result2.games,
    }

    comparison = backtester.compare_strategies(portfolios, draws)

    print(f"\n📊 Comparação:")
    print(f"   Estratégia           | ROI       | Win Rate")
    print(f"   ---------------------+-----------+----------")
    for name, bt in comparison.items():
        print(f"   {name:20} | {bt.roi:8.2f}% | {bt.win_rate:7.2f}%")

    print("\n" + "=" * 70)
    print("✅ Backtester base implementado")
    print("=" * 70)
