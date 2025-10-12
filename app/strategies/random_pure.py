"""
Estratégia de Geração Aleatória Pura (sem filtros).

Esta é a estratégia mais simples: gera jogos completamente aleatórios
sem aplicar nenhum filtro ou restrição além das regras básicas do jogo.

Características:
- Rápida: O(n) - gera n jogos diretamente
- Sem filtros: Aceita qualquer combinação válida
- Reproduzível: Usa seed se fornecido
- Permite duplicatas: Se allow_duplicates=False, garante unicidade

Ideal para:
- Baseline de comparação
- Geração rápida de grandes volumes
- Análise de distribuição natural aleatória
"""

from typing import List, Set
import numpy as np

from app.strategies.base import BaseStrategy, StrategyConfig
from app.core.game import Game
from app.core.combinatorics import gerar_jogo_aleatorio, TAMANHO_JOGO


class RandomPureStrategy(BaseStrategy):
    """
    Estratégia de geração aleatória pura sem filtros.

    Gera jogos completamente aleatórios usando numpy.random.choice().
    É a estratégia mais rápida e serve como baseline.

    Examples:
        >>> strategy = RandomPureStrategy()
        >>> config = StrategyConfig(n_games=10, seed=42)
        >>> result = strategy.generate(config)
        >>> print(f"Gerados: {result.n_games} jogos")
        Gerados: 10 jogos
    """

    def __init__(self):
        """Inicializa estratégia RandomPure."""
        super().__init__(
            name="random_pure",
            description="Geração aleatória pura sem filtros ou restrições",
        )

    def _generate_games(self, config: StrategyConfig) -> List[Game]:
        """
        Gera jogos aleatórios puros.

        Args:
            config: Configuração da estratégia

        Returns:
            Lista de jogos gerados

        Raises:
            ValueError: Se não conseguir gerar jogos únicos
        """
        games = []
        seen_numbers: Set[frozenset] = set()

        # Configurar seed se fornecido
        if config.seed is not None:
            np.random.seed(config.seed)

        for i in range(config.n_games):
            attempt = 0
            while attempt < config.max_attempts:
                # Gerar jogo aleatório
                numbers = gerar_jogo_aleatorio(
                    seed=None  # Seed já configurado globalmente
                )

                # Verificar duplicatas se necessário
                if not config.allow_duplicates:
                    numbers_set = frozenset(numbers)
                    if numbers_set in seen_numbers:
                        attempt += 1
                        continue
                    seen_numbers.add(numbers_set)

                # Criar jogo
                game = Game(
                    numbers=numbers,
                    strategy=self.name,
                    seed=config.seed,
                    metadata={
                        "generation_index": i,
                        "attempts": attempt + 1,
                    },
                )

                games.append(game)
                break

            else:
                # Não conseguiu gerar jogo único após max_attempts
                if not config.allow_duplicates:
                    raise ValueError(
                        f"Não foi possível gerar jogo único após "
                        f"{config.max_attempts} tentativas. "
                        f"Gerados {len(games)}/{config.n_games} jogos. "
                        f"Considere allow_duplicates=True ou reduzir n_games."
                    )

        return games


# ============================================================================
# SCRIPT DE DEMONSTRAÇÃO
# ============================================================================

if __name__ == "__main__":
    from app.strategies.base import StrategyConfig

    print("=" * 70)
    print("RANDOM PURE STRATEGY - Demonstração")
    print("=" * 70)

    # 1. Criar estratégia
    print("\n📦 Criando estratégia RandomPure...")
    strategy = RandomPureStrategy()
    print(f"   Nome: {strategy.name}")
    print(f"   Descrição: {strategy.description}")

    # 2. Gerar 10 jogos com seed
    print("\n🎲 Gerando 10 jogos com seed=42...")
    config = StrategyConfig(n_games=10, seed=42, allow_duplicates=False)

    result = strategy.generate(config)

    print(f"\n✅ Resultado:")
    print(f"   Portfolio ID: {result.portfolio_id}")
    print(f"   Jogos gerados: {result.n_games}")
    print(f"   Custo total: R$ {result.total_cost:.2f}")
    print(f"   Tempo execução: {result.execution_time:.4f}s")
    print(f"   Sucesso: {result.success}")

    # 3. Estatísticas
    print(f"\n📊 Estatísticas:")
    print(f"   Soma mínima: {result.stats['sum_min']}")
    print(f"   Soma máxima: {result.stats['sum_max']}")
    print(f"   Soma média: {result.stats['sum_avg']:.2f}")
    print(f"   Pares mínimo: {result.stats['even_min']}")
    print(f"   Pares máximo: {result.stats['even_max']}")
    print(f"   Pares médio: {result.stats['even_avg']:.2f}")

    # 4. Mostrar primeiros 3 jogos
    print(f"\n🎮 Primeiros 3 jogos:")
    for i, game in enumerate(result.games[:3]):
        print(f"   {i+1}. {game.numbers} (soma={game.sum})")

    # 5. Teste de reprodutibilidade
    print(f"\n🔄 Testando reprodutibilidade...")
    config2 = StrategyConfig(n_games=10, seed=42, allow_duplicates=False)
    result2 = strategy.generate(config2)

    if result.games[0].numbers == result2.games[0].numbers:
        print("   ✅ Reproduzível! Mesmos jogos com mesmo seed")
    else:
        print("   ❌ Não reproduzível")

    # 6. Teste sem duplicatas
    print(f"\n🔍 Verificando jogos únicos...")
    unique_games = set(tuple(game.numbers) for game in result.games)
    if len(unique_games) == result.n_games:
        print(f"   ✅ Todos os {result.n_games} jogos são únicos")
    else:
        print(f"   ❌ Encontradas duplicatas")

    # 7. Teste de performance
    print(f"\n⚡ Teste de performance (100 jogos)...")
    config3 = StrategyConfig(n_games=100, seed=123)
    result3 = strategy.generate(config3)
    jogos_por_segundo = result3.n_games / result3.execution_time
    print(f"   Gerados: {result3.n_games} jogos")
    print(f"   Tempo: {result3.execution_time:.4f}s")
    print(f"   Taxa: {jogos_por_segundo:.0f} jogos/segundo")

    print("\n" + "=" * 70)
    print("✅ RandomPure Strategy implementada e testada")
    print("=" * 70)
