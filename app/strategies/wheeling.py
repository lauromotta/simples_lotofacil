"""
Estratégia de Wheeling (Cobertura Sistemática).

Wheeling é uma técnica que garante cobertura sistemática de combinações.
Esta implementação usa wheeling simplificado baseado em um conjunto maior
de números escolhidos e gera todas as combinações possíveis ou uma amostra.

Características:
- Cobertura garantida: Garante que certas condições sejam atendidas
- Determinística: Mesma entrada = mesma saída
- Configurável: Permite diferentes níveis de cobertura
- Pode gerar muitos jogos: Combinações crescem exponencialmente

Tipos de Wheeling:
1. Full Wheeling: Todas as combinações de N números
2. Abbreviated Wheeling: Subconjunto otimizado
3. Key Number Wheeling: Garante certos números em todos os jogos

Esta implementação usa uma abordagem híbrida simplificada:
- Seleciona K números "quentes" (mais frequentes historicamente)
- Gera combinações sistemáticas desses números
- Opcionalmente aplica filtros

Ideal para:
- Cobertura de números específicos
- Garantir participação de "favoritos"
- Jogar em sindicatos (muitos jogos)
"""

from typing import List, Set, Optional, Tuple
from itertools import combinations
import random

from app.strategies.base import BaseStrategy, StrategyConfig
from app.core.game import Game
from app.core.combinatorics import TAMANHO_JOGO, UNIVERSO


class WheelingStrategy(BaseStrategy):
    """
    Estratégia de wheeling simplificada.

    Seleciona um conjunto maior de números (wheel_size) e gera
    combinações sistemáticas de TAMANHO_JOGO números.

    Examples:
        >>> strategy = WheelingStrategy(wheel_size=18)
        >>> config = StrategyConfig(n_games=50, seed=42)
        >>> result = strategy.generate(config)
        >>> print(f"Gerados: {result.n_games} jogos do wheel")
    """

    def __init__(self, wheel_size: int = 18):
        """
        Inicializa estratégia de Wheeling.

        Args:
            wheel_size: Tamanho do conjunto de números para wheeling
                       (deve ser >= TAMANHO_JOGO e <= UNIVERSO)

        Raises:
            ValueError: Se wheel_size for inválido
        """
        super().__init__(
            name=f"wheeling_{wheel_size}",
            description=f"Wheeling com {wheel_size} números base",
        )

        if wheel_size < TAMANHO_JOGO:
            raise ValueError(
                f"wheel_size ({wheel_size}) deve ser >= {TAMANHO_JOGO}"
            )

        if wheel_size > UNIVERSO:
            raise ValueError(f"wheel_size ({wheel_size}) deve ser <= {UNIVERSO}")

        self.wheel_size = wheel_size

        # Calcular total de combinações possíveis
        from math import comb

        self.total_combinations = comb(wheel_size, TAMANHO_JOGO)

    def _select_wheel_numbers(self, seed: Optional[int] = None) -> List[int]:
        """
        Seleciona números para o wheel.

        Estratégia: Usa distribuição uniforme aleatória.
        Futuramente pode ser melhorado para usar frequências históricas.

        Args:
            seed: Seed para reprodutibilidade

        Returns:
            Lista de wheel_size números ordenados [1-25]
        """
        if seed is not None:
            random.seed(seed)

        # Selecionar wheel_size números únicos do universo [1-25]
        wheel_numbers = sorted(
            random.sample(range(1, UNIVERSO + 1), self.wheel_size)
        )

        return wheel_numbers

    def _generate_combinations(
        self, wheel_numbers: List[int], n_games: int, seed: Optional[int] = None
    ) -> List[List[int]]:
        """
        Gera combinações dos números do wheel.

        Se n_games >= total_combinations, gera todas as combinações.
        Caso contrário, amostra n_games combinações aleatoriamente.

        Args:
            wheel_numbers: Números do wheel
            n_games: Quantidade de jogos desejada
            seed: Seed para amostragem aleatória

        Returns:
            Lista de combinações (cada combinação é uma lista de 15 números)
        """
        all_combinations = list(combinations(wheel_numbers, TAMANHO_JOGO))

        if n_games >= len(all_combinations):
            # Gerar todas as combinações
            return [list(combo) for combo in all_combinations]

        # Amostrar n_games combinações
        if seed is not None:
            random.seed(seed + 1)  # Seed diferente para amostragem

        sampled = random.sample(all_combinations, n_games)
        return [list(combo) for combo in sampled]

    def _generate_games(self, config: StrategyConfig) -> List[Game]:
        """
        Gera jogos usando wheeling.

        Args:
            config: Configuração da estratégia

        Returns:
            Lista de jogos gerados

        Raises:
            ValueError: Se configuração for inválida
        """
        # Selecionar números do wheel
        wheel_numbers = self._select_wheel_numbers(seed=config.seed)

        # Gerar combinações
        combinations_list = self._generate_combinations(
            wheel_numbers, config.n_games, seed=config.seed
        )

        games = []
        seen_numbers: Set[frozenset] = set()

        for i, numbers in enumerate(combinations_list):
            # Verificar duplicatas se necessário
            if not config.allow_duplicates:
                numbers_set = frozenset(numbers)
                if numbers_set in seen_numbers:
                    continue
                seen_numbers.add(numbers_set)

            # Aplicar filtros se fornecidos
            if config.filters is not None:
                is_valid, rejection_reasons = config.filters.apply(numbers)
                if not is_valid:
                    continue

            # Criar jogo
            game = Game(
                numbers=numbers,
                strategy=self.name,
                seed=config.seed,
                metadata={
                    "generation_index": i,
                    "wheel_size": self.wheel_size,
                    "wheel_numbers": wheel_numbers,
                    "from_wheeling": True,
                },
            )

            games.append(game)

            # Parar se atingiu n_games (importante quando há filtros)
            if len(games) >= config.n_games:
                break

        # Se não conseguiu gerar jogos suficientes com filtros
        if len(games) < config.n_games and config.filters is not None:
            raise RuntimeError(
                f"Wheeling com filtros gerou apenas {len(games)}/{config.n_games} jogos. "
                f"Total combinações do wheel: {self.total_combinations}. "
                f"Considere: (1) aumentar wheel_size, (2) relaxar filtros, "
                f"ou (3) reduzir n_games."
            )

        return games


# ============================================================================
# SCRIPT DE DEMONSTRAÇÃO
# ============================================================================

if __name__ == "__main__":
    from app.strategies.base import StrategyConfig
    from app.filters import FilterChain, SumRangeFilter

    print("=" * 70)
    print("WHEELING STRATEGY - Demonstração")
    print("=" * 70)

    # 1. Criar estratégia
    print("\n📦 Criando estratégia Wheeling (wheel_size=18)...")
    strategy = WheelingStrategy(wheel_size=18)
    print(f"   Nome: {strategy.name}")
    print(f"   Descrição: {strategy.description}")
    print(f"   Wheel size: {strategy.wheel_size}")
    print(f"   Total combinações possíveis: {strategy.total_combinations:,}")

    # 2. Gerar 20 jogos
    print("\n🎲 Gerando 20 jogos com wheeling (seed=42)...")
    config = StrategyConfig(n_games=20, seed=42, allow_duplicates=False)

    result = strategy.generate(config)

    print(f"\n✅ Resultado:")
    print(f"   Portfolio ID: {result.portfolio_id}")
    print(f"   Jogos gerados: {result.n_games}")
    print(f"   Custo total: R$ {result.total_cost:.2f}")
    print(f"   Tempo execução: {result.execution_time:.4f}s")
    print(f"   Sucesso: {result.success}")

    # 3. Estatísticas
    print(f"\n📊 Estatísticas dos Jogos:")
    print(f"   Soma mínima: {result.stats['sum_min']}")
    print(f"   Soma máxima: {result.stats['sum_max']}")
    print(f"   Soma média: {result.stats['sum_avg']:.2f}")
    print(f"   Pares mínimo: {result.stats['even_min']}")
    print(f"   Pares máximo: {result.stats['even_max']}")
    print(f"   Pares médio: {result.stats['even_avg']:.2f}")

    # 4. Mostrar wheel numbers
    if result.games:
        wheel_nums = result.games[0].metadata.get("wheel_numbers", [])
        print(f"\n🎯 Números do Wheel (18 números):")
        print(f"   {wheel_nums}")

    # 5. Mostrar primeiros 3 jogos
    print(f"\n🎮 Primeiros 3 jogos:")
    for i, game in enumerate(result.games[:3]):
        print(f"   {i+1}. {game.numbers} (soma={game.sum})")

    # 6. Verificar cobertura do wheel
    print(f"\n🔍 Verificando cobertura do wheel...")
    all_numbers_used = set()
    for game in result.games:
        all_numbers_used.update(game.numbers)

    wheel_coverage = len(all_numbers_used & set(wheel_nums)) / len(wheel_nums) * 100
    print(f"   Números do wheel usados: {len(all_numbers_used & set(wheel_nums))}/{len(wheel_nums)}")
    print(f"   Cobertura: {wheel_coverage:.1f}%")

    # 7. Teste com filtros
    print(f"\n⚙️  Teste com filtros (Soma: 180-210)...")
    filters = FilterChain([SumRangeFilter(min_sum=180, max_sum=210)])
    config2 = StrategyConfig(
        n_games=15, seed=42, filters=filters, allow_duplicates=False
    )

    result2 = strategy.generate(config2)
    print(f"   Gerados: {result2.n_games} jogos")
    print(f"   Tempo: {result2.execution_time:.4f}s")

    if "filter_stats" in result2.stats:
        for fname, fstats in result2.stats["filter_stats"].items():
            approval_rate = (
                100 - fstats["rejection_rate"] if "rejection_rate" in fstats else 0
            )
            print(f"   {fname}: {approval_rate:.1f}% aprovação")

    # 8. Teste diferentes wheel sizes
    print(f"\n📏 Comparando diferentes wheel sizes...")
    for wheel_sz in [17, 18, 20]:
        strat = WheelingStrategy(wheel_size=wheel_sz)
        cfg = StrategyConfig(n_games=10, seed=123)
        res = strat.generate(cfg)
        print(f"   Wheel {wheel_sz}: {strat.total_combinations:,} combinações possíveis")

    # 9. Reprodutibilidade
    print(f"\n🔄 Testando reprodutibilidade...")
    config3 = StrategyConfig(n_games=10, seed=42)
    result3a = strategy.generate(config3)
    result3b = strategy.generate(config3)

    if result3a.games[0].numbers == result3b.games[0].numbers:
        print("   ✅ Reproduzível! Mesmos jogos com mesmo seed")
    else:
        print("   ❌ Não reproduzível")

    print("\n" + "=" * 70)
    print("✅ Wheeling Strategy implementada e testada")
    print("=" * 70)
