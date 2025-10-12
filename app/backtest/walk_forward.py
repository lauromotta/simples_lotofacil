"""
Walk-Forward Validation para Backtesting.

Walk-Forward é uma técnica de validação que simula trading/apostas
no mundo real, onde você:
1. Treina em dados passados (in-sample)
2. Testa em dados futuros (out-of-sample)
3. Avança a janela no tempo

Exemplo:
    Window 1: Treina em concursos 1-100, testa em 101-120
    Window 2: Treina em concursos 21-120, testa em 121-140
    Window 3: Treina em concursos 41-140, testa em 141-160
    ...

Isso evita overfitting e simula melhor a realidade onde você
só tem dados passados para tomar decisões.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
from datetime import datetime

from app.backtest.base import Backtester, PortfolioBacktest
from app.core.game import Game


@dataclass
class WalkForwardWindow:
    """
    Uma janela de walk-forward.

    Attributes:
        window_id: ID da janela
        train_start: Concurso inicial do treino
        train_end: Concurso final do treino
        test_start: Concurso inicial do teste
        test_end: Concurso final do teste
        train_size: Quantidade de concursos de treino
        test_size: Quantidade de concursos de teste
    """

    window_id: int
    train_start: int
    train_end: int
    test_start: int
    test_end: int

    @property
    def train_size(self) -> int:
        return self.train_end - self.train_start + 1

    @property
    def test_size(self) -> int:
        return self.test_end - self.test_start + 1

    def __str__(self) -> str:
        return (
            f"Window {self.window_id}: "
            f"Train[{self.train_start}-{self.train_end}] ({self.train_size}), "
            f"Test[{self.test_start}-{self.test_end}] ({self.test_size})"
        )


@dataclass
class WalkForwardResult:
    """
    Resultado completo de walk-forward validation.

    Attributes:
        strategy_name: Nome da estratégia testada
        windows: Lista de janelas testadas
        window_results: Resultados por janela
        overall_roi: ROI médio em todas as janelas
        overall_win_rate: Win rate médio
        total_custo: Custo total (todas as janelas)
        total_premio: Premio total
        total_lucro: Lucro total
        best_window: Melhor janela (maior ROI)
        worst_window: Pior janela (menor ROI)
        consistency: Desvio padrão do ROI entre janelas
    """

    strategy_name: str
    windows: List[WalkForwardWindow]
    window_results: Dict[int, PortfolioBacktest] = field(default_factory=dict)
    overall_roi: float = 0.0
    overall_win_rate: float = 0.0
    total_custo: float = 0.0
    total_premio: float = 0.0
    total_lucro: float = 0.0
    best_window: Optional[WalkForwardWindow] = None
    worst_window: Optional[WalkForwardWindow] = None
    consistency: float = 0.0

    def __str__(self) -> str:
        return (
            f"WalkForwardResult(\n"
            f"  Estratégia: {self.strategy_name}\n"
            f"  Janelas: {len(self.windows)}\n"
            f"  ROI médio: {self.overall_roi:.2f}%\n"
            f"  Win rate médio: {self.overall_win_rate:.2f}%\n"
            f"  Custo total: R$ {self.total_custo:.2f}\n"
            f"  Premio total: R$ {self.total_premio:.2f}\n"
            f"  Lucro total: R$ {self.total_lucro:.2f}\n"
            f"  Consistência (std ROI): {self.consistency:.2f}%\n"
            f")"
        )


class WalkForwardValidator:
    """
    Validador Walk-Forward para backtesting.

    Divide dados históricos em janelas treino/teste que avançam no tempo,
    simulando a evolução temporal real de apostas.

    Examples:
        >>> from app.io.database import get_database, Draw
        >>> db = get_database("sqlite:///lotofacil.db")
        >>> session = db.get_session()
        >>> draws = session.query(Draw).order_by(Draw.concurso).all()
        >>>
        >>> def strategy_generator(train_draws):
        ...     # Gera jogos baseados em dados de treino
        ...     from app.strategies import RandomPureStrategy, StrategyConfig
        ...     strategy = RandomPureStrategy()
        ...     return strategy.generate(StrategyConfig(n_games=10, seed=42)).games
        >>>
        >>> validator = WalkForwardValidator()
        >>> result = validator.run(
        ...     draws=draws,
        ...     strategy_generator=strategy_generator,
        ...     train_size=100,
        ...     test_size=20,
        ...     step_size=20
        ... )
        >>> print(f"ROI médio: {result.overall_roi:.2f}%")
    """

    def __init__(self):
        """Inicializa o validador walk-forward."""
        self.backtester = Backtester()

    def create_windows(
        self,
        total_draws: int,
        train_size: int,
        test_size: int,
        step_size: int,
        min_concurso: int = 1,
    ) -> List[WalkForwardWindow]:
        """
        Cria janelas de walk-forward.

        Args:
            total_draws: Total de sorteios disponíveis
            train_size: Tamanho da janela de treino
            test_size: Tamanho da janela de teste
            step_size: Quanto avançar entre janelas
            min_concurso: Número do primeiro concurso

        Returns:
            Lista de janelas WalkForwardWindow

        Examples:
            >>> validator = WalkForwardValidator()
            >>> windows = validator.create_windows(
            ...     total_draws=200,
            ...     train_size=100,
            ...     test_size=20,
            ...     step_size=20
            ... )
            >>> len(windows)
            5
        """
        windows = []
        window_id = 1
        current_pos = 0

        while current_pos + train_size + test_size <= total_draws:
            train_start = min_concurso + current_pos
            train_end = train_start + train_size - 1
            test_start = train_end + 1
            test_end = test_start + test_size - 1

            window = WalkForwardWindow(
                window_id=window_id,
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
            )

            windows.append(window)
            window_id += 1
            current_pos += step_size

        return windows

    def run(
        self,
        draws: List,  # List[Draw]
        strategy_generator: Callable[[List], List[Game]],
        train_size: int = 100,
        test_size: int = 20,
        step_size: int = 20,
        strategy_name: str = "walk_forward_strategy",
    ) -> WalkForwardResult:
        """
        Executa walk-forward validation.

        Args:
            draws: Lista completa de sorteios (ordenados por concurso)
            strategy_generator: Função que recebe draws de treino e retorna games
                               Signature: def generator(train_draws) -> List[Game]
            train_size: Tamanho da janela de treino
            test_size: Tamanho da janela de teste
            step_size: Quanto avançar entre janelas
            strategy_name: Nome da estratégia

        Returns:
            WalkForwardResult com resultados de todas as janelas

        Raises:
            ValueError: Se parâmetros inválidos
        """
        if train_size <= 0 or test_size <= 0 or step_size <= 0:
            raise ValueError("Tamanhos devem ser positivos")

        if len(draws) < train_size + test_size:
            raise ValueError(
                f"Draws insuficientes: {len(draws)} < {train_size + test_size}"
            )

        # Ordenar draws por concurso
        draws_sorted = sorted(
            draws, key=lambda d: d.concurso if hasattr(d, 'concurso') else d['concurso']
        )

        # Criar janelas
        min_concurso = (
            draws_sorted[0].concurso if hasattr(draws_sorted[0], 'concurso')
            else draws_sorted[0]['concurso']
        )

        windows = self.create_windows(
            total_draws=len(draws_sorted),
            train_size=train_size,
            test_size=test_size,
            step_size=step_size,
            min_concurso=min_concurso,
        )

        # Executar backtest em cada janela
        window_results = {}
        all_rois = []
        all_win_rates = []
        total_custo = 0.0
        total_premio = 0.0

        for window in windows:
            # Separar dados de treino e teste
            train_draws = [
                d for d in draws_sorted
                if (
                    window.train_start
                    <= (d.concurso if hasattr(d, 'concurso') else d['concurso'])
                    <= window.train_end
                )
            ]

            test_draws = [
                d for d in draws_sorted
                if (
                    window.test_start
                    <= (d.concurso if hasattr(d, 'concurso') else d['concurso'])
                    <= window.test_end
                )
            ]

            # Gerar jogos baseados nos dados de treino
            games = strategy_generator(train_draws)

            # Testar nos dados de teste
            bt_result = self.backtester.run(
                games,
                test_draws,
                portfolio_id=f"{strategy_name}_window_{window.window_id}",
                strategy=strategy_name,
            )

            window_results[window.window_id] = bt_result
            all_rois.append(bt_result.roi)
            all_win_rates.append(bt_result.win_rate)
            total_custo += bt_result.total_custo
            total_premio += bt_result.total_premio

        # Calcular métricas agregadas
        overall_roi = sum(all_rois) / len(all_rois) if all_rois else 0.0
        overall_win_rate = sum(all_win_rates) / len(all_win_rates) if all_win_rates else 0.0
        total_lucro = total_premio - total_custo

        # Melhor e pior janela
        best_window = max(windows, key=lambda w: window_results[w.window_id].roi)
        worst_window = min(windows, key=lambda w: window_results[w.window_id].roi)

        # Consistência (desvio padrão do ROI)
        if len(all_rois) > 1:
            mean_roi = sum(all_rois) / len(all_rois)
            variance = sum((roi - mean_roi) ** 2 for roi in all_rois) / len(all_rois)
            consistency = variance ** 0.5
        else:
            consistency = 0.0

        return WalkForwardResult(
            strategy_name=strategy_name,
            windows=windows,
            window_results=window_results,
            overall_roi=overall_roi,
            overall_win_rate=overall_win_rate,
            total_custo=total_custo,
            total_premio=total_premio,
            total_lucro=total_lucro,
            best_window=best_window,
            worst_window=worst_window,
            consistency=consistency,
        )


# ============================================================================
# SCRIPT DE DEMONSTRAÇÃO
# ============================================================================

if __name__ == "__main__":
    from dataclasses import dataclass as dc
    from typing import List as TList

    print("=" * 70)
    print("WALK-FORWARD VALIDATION - Demonstração")
    print("=" * 70)

    # 1. Criar sorteios fictícios
    print("\n📦 Criando sorteios fictícios (200 concursos)...")

    @dc
    class FakeDraw:
        concurso: int
        nums_15: TList[int]

    import random
    random.seed(42)

    draws = []
    for i in range(1, 201):
        nums = sorted(random.sample(range(1, 26), 15))
        draws.append(FakeDraw(concurso=i, nums_15=nums))

    print(f"   Sorteios criados: {len(draws)}")

    # 2. Definir gerador de estratégia
    print("\n🎯 Definindo gerador de estratégia...")

    def simple_strategy_generator(train_draws):
        """Estratégia simples: gera 5 jogos aleatórios"""
        from app.strategies import RandomPureStrategy, StrategyConfig

        # Análise fictícia dos dados de treino
        # (em uma implementação real, você analisaria padrões históricos)

        strategy = RandomPureStrategy()
        seed = train_draws[0].concurso if train_draws else 42
        config = StrategyConfig(n_games=5, seed=seed)
        result = strategy.generate(config)

        return result.games

    print("   Gerador definido: 5 jogos aleatórios por janela")

    # 3. Criar janelas
    print("\n📐 Criando janelas walk-forward...")
    validator = WalkForwardValidator()

    windows = validator.create_windows(
        total_draws=200,
        train_size=100,
        test_size=20,
        step_size=20,
        min_concurso=1,
    )

    print(f"   Janelas criadas: {len(windows)}")
    for w in windows[:3]:
        print(f"      {w}")
    if len(windows) > 3:
        print(f"      ...")

    # 4. Executar walk-forward
    print("\n🔬 Executando walk-forward validation...")
    wf_result = validator.run(
        draws=draws,
        strategy_generator=simple_strategy_generator,
        train_size=100,
        test_size=20,
        step_size=20,
        strategy_name="simple_random",
    )

    print(f"\n✅ Resultados Gerais:")
    print(f"   Estratégia: {wf_result.strategy_name}")
    print(f"   Janelas testadas: {len(wf_result.windows)}")
    print(f"   ROI médio: {wf_result.overall_roi:.2f}%")
    print(f"   Win rate médio: {wf_result.overall_win_rate:.2f}%")
    print(f"   Custo total: R$ {wf_result.total_custo:.2f}")
    print(f"   Premio total: R$ {wf_result.total_premio:.2f}")
    print(f"   Lucro total: R$ {wf_result.total_lucro:.2f}")
    print(f"   Consistência (std): {wf_result.consistency:.2f}%")

    # 5. Melhor e pior janela
    print(f"\n🏆 Melhor Janela:")
    if wf_result.best_window:
        best_result = wf_result.window_results[wf_result.best_window.window_id]
        print(f"   {wf_result.best_window}")
        print(f"   ROI: {best_result.roi:.2f}%")
        print(f"   Win rate: {best_result.win_rate:.2f}%")

    print(f"\n📉 Pior Janela:")
    if wf_result.worst_window:
        worst_result = wf_result.window_results[wf_result.worst_window.window_id]
        print(f"   {wf_result.worst_window}")
        print(f"   ROI: {worst_result.roi:.2f}%")
        print(f"   Win rate: {worst_result.win_rate:.2f}%")

    # 6. ROI por janela
    print(f"\n📊 ROI por Janela:")
    for window in wf_result.windows:
        result = wf_result.window_results[window.window_id]
        bar = "█" * int(max(0, result.roi / 10))
        print(f"   Window {window.window_id}: {result.roi:7.2f}% {bar}")

    print("\n" + "=" * 70)
    print("✅ Walk-Forward Validation implementado")
    print("=" * 70)
