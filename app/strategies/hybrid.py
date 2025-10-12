"""
Estratégia Híbrida (Combinação de Estratégias).

Esta estratégia combina múltiplas estratégias para criar um portfolio
diversificado. Permite alocar diferentes percentuais do portfolio para
diferentes estratégias.

Características:
- Diversificação: Combina pontos fortes de várias estratégias
- Configurável: Define proporções de cada estratégia
- Flexível: Suporta qualquer combinação de estratégias
- Reproduzível: Usa seeds diferentes para cada sub-estratégia

Exemplo de uso:
- 50% RandomFiltered (seguir padrões históricos)
- 30% Wheeling (cobertura sistemática)
- 20% RandomPure (aleatoriedade pura)

Ideal para:
- Balancear risco e cobertura
- Testar múltiplas abordagens
- Portfolios grandes e diversificados
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from app.strategies.base import BaseStrategy, StrategyConfig
from app.core.game import Game


@dataclass
class StrategyAllocation:
    """
    Alocação de uma estratégia no portfolio híbrido.

    Attributes:
        strategy: Instância da estratégia
        percentage: Percentual do portfolio (0.0 - 1.0)
        config_override: Overrides específicos para esta estratégia (opcional)
    """

    strategy: BaseStrategy
    percentage: float
    config_override: Optional[Dict] = None

    def __post_init__(self):
        """Validação."""
        if not 0.0 < self.percentage <= 1.0:
            raise ValueError(f"Percentage deve estar entre 0 e 1, got {self.percentage}")


class HybridStrategy(BaseStrategy):
    """
    Estratégia híbrida que combina múltiplas estratégias.

    Distribui n_games entre as estratégias conforme percentuais definidos.
    Cada estratégia pode ter configurações específicas.

    Examples:
        >>> from app.strategies import RandomPureStrategy, RandomFilteredStrategy
        >>> from app.filters import FilterChain, SumRangeFilter
        >>>
        >>> filters = FilterChain([SumRangeFilter(180, 210)])
        >>> allocations = [
        ...     StrategyAllocation(RandomPureStrategy(), 0.5),
        ...     StrategyAllocation(RandomFilteredStrategy(), 0.5,
        ...                       config_override={'filters': filters})
        ... ]
        >>> strategy = HybridStrategy(allocations)
        >>> config = StrategyConfig(n_games=100, seed=42)
        >>> result = strategy.generate(config)
        >>> print(f"{result.n_games} jogos: 50% pure, 50% filtered")
    """

    def __init__(self, allocations: List[StrategyAllocation]):
        """
        Inicializa estratégia híbrida.

        Args:
            allocations: Lista de alocações de estratégias

        Raises:
            ValueError: Se alocações forem inválidas
        """
        super().__init__(
            name="hybrid",
            description=f"Híbrido de {len(allocations)} estratégias",
        )

        if not allocations:
            raise ValueError("Pelo menos uma alocação deve ser fornecida")

        # Validar que percentuais somam ~1.0
        total_percentage = sum(a.percentage for a in allocations)
        if not 0.99 <= total_percentage <= 1.01:
            raise ValueError(
                f"Percentuais devem somar 1.0, got {total_percentage:.2f}"
            )

        self.allocations = allocations

    def _calculate_games_per_strategy(
        self, total_games: int
    ) -> List[Tuple[BaseStrategy, int, Optional[Dict]]]:
        """
        Calcula quantos jogos cada estratégia deve gerar.

        Args:
            total_games: Total de jogos do portfolio

        Returns:
            Lista de tuplas (estratégia, n_jogos, config_override)
        """
        distributions = []
        allocated_games = 0

        for i, allocation in enumerate(self.allocations):
            # Calcular jogos para esta estratégia
            if i == len(self.allocations) - 1:
                # Última estratégia: pega o restante para evitar erros de arredondamento
                n_games = total_games - allocated_games
            else:
                n_games = int(total_games * allocation.percentage)

            allocated_games += n_games

            distributions.append(
                (allocation.strategy, n_games, allocation.config_override)
            )

        return distributions

    def _merge_configs(
        self, base_config: StrategyConfig, override: Optional[Dict]
    ) -> StrategyConfig:
        """
        Mescla configuração base com overrides.

        Args:
            base_config: Configuração base
            override: Dicionário com overrides (ou None)

        Returns:
            Nova StrategyConfig mesclada
        """
        if override is None:
            return base_config

        # Criar novo config com valores base
        merged = StrategyConfig(
            n_games=base_config.n_games,
            seed=base_config.seed,
            filters=base_config.filters,
            max_attempts=base_config.max_attempts,
            allow_duplicates=base_config.allow_duplicates,
            metadata=base_config.metadata.copy(),
        )

        # Aplicar overrides
        for key, value in override.items():
            if hasattr(merged, key):
                setattr(merged, key, value)

        return merged

    def _generate_games(self, config: StrategyConfig) -> List[Game]:
        """
        Gera jogos distribuindo entre as estratégias.

        Args:
            config: Configuração global

        Returns:
            Lista combinada de jogos de todas as estratégias
        """
        all_games = []

        # Calcular distribuição
        distributions = self._calculate_games_per_strategy(config.n_games)

        # Gerar jogos para cada estratégia
        for i, (strategy, n_games, config_override) in enumerate(distributions):
            if n_games == 0:
                continue

            # Criar config para esta estratégia
            strategy_config = self._merge_configs(config, config_override)
            strategy_config.n_games = n_games

            # Usar seed diferente para cada estratégia (se seed fornecido)
            if config.seed is not None:
                strategy_config.seed = config.seed + i * 1000

            # Gerar jogos com esta estratégia
            result = strategy.generate(strategy_config)

            if not result.success:
                raise RuntimeError(
                    f"Estratégia {strategy.name} falhou: {result.error_message}"
                )

            # Adicionar metadata sobre origem
            for game in result.games:
                game.metadata["hybrid_source"] = strategy.name
                game.metadata["hybrid_allocation"] = self.allocations[i].percentage

            all_games.extend(result.games)

        return all_games


# ============================================================================
# SCRIPT DE DEMONSTRAÇÃO
# ============================================================================

if __name__ == "__main__":
    from app.strategies.base import StrategyConfig
    from app.strategies.random_pure import RandomPureStrategy
    from app.strategies.random_filtered import RandomFilteredStrategy
    from app.strategies.wheeling import WheelingStrategy
    from app.filters import FilterChain, SumRangeFilter, EvenOddFilter

    print("=" * 70)
    print("HYBRID STRATEGY - Demonstração")
    print("=" * 70)

    # 1. Configurar estratégias
    print("\n📦 Configurando estratégias componentes...")

    pure = RandomPureStrategy()
    filtered = RandomFilteredStrategy()
    wheeling = WheelingStrategy(wheel_size=18)

    # Configurar filtros para RandomFiltered
    filters = FilterChain(
        [
            SumRangeFilter(min_sum=180, max_sum=210),
            EvenOddFilter(min_even=6, max_even=9),
        ]
    )

    print(f"   - {pure.name}: Geração aleatória pura")
    print(f"   - {filtered.name}: Com filtros (soma 180-210, pares 6-9)")
    print(f"   - {wheeling.name}: Wheeling sistemático")

    # 2. Criar alocações
    print("\n⚖️  Definindo alocações...")
    allocations = [
        StrategyAllocation(pure, 0.30),  # 30% pure
        StrategyAllocation(
            filtered, 0.50, config_override={"filters": filters}
        ),  # 50% filtered
        StrategyAllocation(wheeling, 0.20),  # 20% wheeling
    ]

    print("   30% RandomPure")
    print("   50% RandomFiltered")
    print("   20% Wheeling")

    # 3. Criar estratégia híbrida
    print("\n🔀 Criando estratégia Híbrida...")
    strategy = HybridStrategy(allocations)
    print(f"   Nome: {strategy.name}")
    print(f"   Descrição: {strategy.description}")

    # 4. Gerar 100 jogos
    print("\n🎲 Gerando 100 jogos com estratégia híbrida (seed=42)...")
    config = StrategyConfig(n_games=100, seed=42, allow_duplicates=False)

    result = strategy.generate(config)

    print(f"\n✅ Resultado:")
    print(f"   Portfolio ID: {result.portfolio_id}")
    print(f"   Jogos gerados: {result.n_games}")
    print(f"   Custo total: R$ {result.total_cost:.2f}")
    print(f"   Tempo execução: {result.execution_time:.4f}s")
    print(f"   Sucesso: {result.success}")

    # 5. Estatísticas gerais
    print(f"\n📊 Estatísticas Gerais:")
    print(f"   Soma mínima: {result.stats['sum_min']}")
    print(f"   Soma máxima: {result.stats['sum_max']}")
    print(f"   Soma média: {result.stats['sum_avg']:.2f}")
    print(f"   Pares mínimo: {result.stats['even_min']}")
    print(f"   Pares máximo: {result.stats['even_max']}")
    print(f"   Pares médio: {result.stats['even_avg']:.2f}")

    # 6. Distribuição por estratégia
    print(f"\n📈 Distribuição por Estratégia:")
    strategy_counts = {}
    for game in result.games:
        source = game.metadata.get("hybrid_source", "unknown")
        strategy_counts[source] = strategy_counts.get(source, 0) + 1

    for source, count in sorted(strategy_counts.items()):
        percentage = count / result.n_games * 100
        print(f"   {source}: {count} jogos ({percentage:.1f}%)")

    # 7. Validar jogos filtrados
    print(f"\n🔍 Validando jogos RandomFiltered...")
    filtered_games = [
        g for g in result.games if g.metadata.get("hybrid_source") == "random_filtered"
    ]

    if filtered_games:
        all_valid = True
        for game in filtered_games:
            is_valid, reasons = filters.apply(game.numbers)
            if not is_valid:
                all_valid = False
                print(f"   ❌ Jogo inválido: {game.numbers}")

        if all_valid:
            print(f"   ✅ Todos os {len(filtered_games)} jogos filtered passam nos filtros!")

    # 8. Amostra de jogos
    print(f"\n🎮 Amostra de jogos (5 primeiros):")
    for i, game in enumerate(result.games[:5]):
        source = game.metadata.get("hybrid_source", "unknown")
        print(f"   {i+1}. [{source}] {game.numbers[:5]}... (soma={game.sum})")

    # 9. Teste de reprodutibilidade
    print(f"\n🔄 Testando reprodutibilidade...")
    config2 = StrategyConfig(n_games=100, seed=42, allow_duplicates=False)
    result2 = strategy.generate(config2)

    if result.games[0].numbers == result2.games[0].numbers:
        print("   ✅ Reproduzível! Mesmos jogos com mesmo seed")
    else:
        print("   ❌ Não reproduzível")

    # 10. Comparação de performance
    print(f"\n⚡ Comparação de Performance:")
    print(f"   Hybrid (100 jogos): {result.execution_time:.4f}s")
    print(f"   Taxa: {result.n_games/result.execution_time:.0f} jogos/s")

    print("\n" + "=" * 70)
    print("✅ Hybrid Strategy implementada e testada")
    print("=" * 70)
