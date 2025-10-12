"""
Estratégia de Geração Aleatória com Filtros.

Esta estratégia gera jogos aleatórios e aplica filtros para validação.
Jogos que não passam nos filtros são descartados e novos são gerados
até atingir a quantidade desejada.

Características:
- Moderadamente rápida: Depende da taxa de aprovação dos filtros
- Com filtros: Aplica FilterChain configurável
- Reproduzível: Usa seed se fornecido
- Garante qualidade: Todos os jogos passam nos filtros
- Tracking: Estatísticas de aprovação/rejeição

Ideal para:
- Geração com critérios de qualidade
- Seguir padrões históricos
- Balancear aleatoriedade e restrições

Performance:
- Se taxa de aprovação = 30%, espera-se ~3.3 tentativas por jogo
- Max_attempts protege contra loops infinitos
"""

from typing import List, Set, Optional
import numpy as np

from app.strategies.base import BaseStrategy, StrategyConfig
from app.core.game import Game
from app.core.combinatorics import gerar_jogo_aleatorio


class RandomFilteredStrategy(BaseStrategy):
    """
    Estratégia de geração aleatória com filtros aplicados.

    Gera jogos aleatórios e valida com FilterChain. Jogos rejeitados
    são descartados e novas tentativas são feitas até atingir n_games
    ou max_attempts.

    Examples:
        >>> from app.filters import FilterChain, SumRangeFilter
        >>> filters = FilterChain([SumRangeFilter(180, 210)])
        >>> strategy = RandomFilteredStrategy()
        >>> config = StrategyConfig(n_games=10, filters=filters, seed=42)
        >>> result = strategy.generate(config)
        >>> print(f"Taxa aprovação: {result.stats['approval_rate']:.1%}")
    """

    def __init__(self):
        """Inicializa estratégia RandomFiltered."""
        super().__init__(
            name="random_filtered",
            description="Geração aleatória com aplicação de filtros",
        )

    def validate_config(self, config: StrategyConfig) -> tuple[bool, Optional[str]]:
        """
        Valida configuração específica para RandomFiltered.

        Args:
            config: Configuração a validar

        Returns:
            Tupla (válido, mensagem_erro)
        """
        # Validação base
        is_valid, error_msg = super().validate_config(config)
        if not is_valid:
            return False, error_msg

        # RandomFiltered REQUER filtros
        if config.filters is None:
            return (
                False,
                "RandomFiltered requer FilterChain em config.filters. "
                "Use RandomPure se não quiser filtros.",
            )

        return True, None

    def _generate_games(self, config: StrategyConfig) -> List[Game]:
        """
        Gera jogos aleatórios aplicando filtros.

        Args:
            config: Configuração da estratégia

        Returns:
            Lista de jogos gerados (todos aprovados pelos filtros)

        Raises:
            ValueError: Se config.filters é None
            RuntimeError: Se não conseguir gerar jogos suficientes
        """
        # Validar configuração
        is_valid, error_msg = self.validate_config(config)
        if not is_valid:
            raise ValueError(error_msg)

        games = []
        seen_numbers: Set[frozenset] = set()

        # Configurar seed se fornecido
        if config.seed is not None:
            np.random.seed(config.seed)

        # Estatísticas de geração
        total_attempts = 0
        total_generated = 0
        total_rejected = 0

        for i in range(config.n_games):
            attempt = 0
            game_generated = False

            while attempt < config.max_attempts:
                total_attempts += 1

                # Gerar jogo aleatório
                numbers = gerar_jogo_aleatorio(seed=None)

                # Verificar duplicatas se necessário
                if not config.allow_duplicates:
                    numbers_set = frozenset(numbers)
                    if numbers_set in seen_numbers:
                        attempt += 1
                        continue

                # Aplicar filtros
                is_valid_game, rejection_reasons = config.filters.apply(numbers)

                if not is_valid_game:
                    # Jogo rejeitado pelos filtros
                    total_rejected += 1
                    attempt += 1
                    continue

                # Jogo aprovado!
                if not config.allow_duplicates:
                    seen_numbers.add(numbers_set)

                game = Game(
                    numbers=numbers,
                    strategy=self.name,
                    seed=config.seed,
                    metadata={
                        "generation_index": i,
                        "attempts": attempt + 1,
                        "passed_filters": True,
                    },
                )

                games.append(game)
                total_generated += 1
                game_generated = True
                break

            if not game_generated:
                # Não conseguiu gerar jogo após max_attempts
                raise RuntimeError(
                    f"Não foi possível gerar jogo {i+1}/{config.n_games} após "
                    f"{config.max_attempts} tentativas. "
                    f"Gerados: {len(games)} jogos. "
                    f"Total tentativas: {total_attempts}. "
                    f"Taxa aprovação atual: {total_generated/total_attempts:.1%}. "
                    f"Considere: (1) aumentar max_attempts, "
                    f"(2) relaxar filtros, ou (3) usar allow_duplicates=True."
                )

        return games


# ============================================================================
# SCRIPT DE DEMONSTRAÇÃO
# ============================================================================

if __name__ == "__main__":
    from app.strategies.base import StrategyConfig
    from app.filters import (
        FilterChain,
        SumRangeFilter,
        EvenOddFilter,
        ConsecutiveFilter,
    )

    print("=" * 70)
    print("RANDOM FILTERED STRATEGY - Demonstração")
    print("=" * 70)

    # 1. Criar estratégia
    print("\n📦 Criando estratégia RandomFiltered...")
    strategy = RandomFilteredStrategy()
    print(f"   Nome: {strategy.name}")
    print(f"   Descrição: {strategy.description}")

    # 2. Configurar filtros moderados
    print("\n⚙️  Configurando filtros moderados...")
    filters = FilterChain(
        [
            SumRangeFilter(min_sum=180, max_sum=210),
            EvenOddFilter(min_even=6, max_even=9),
            ConsecutiveFilter(max_consecutive=4),
        ]
    )
    print("   - Soma: 180-210")
    print("   - Pares: 6-9")
    print("   - Consecutivos: máx 4")

    # 3. Gerar 20 jogos com filtros
    print("\n🎲 Gerando 20 jogos com filtros (seed=42)...")
    config = StrategyConfig(
        n_games=20, seed=42, filters=filters, max_attempts=1000, allow_duplicates=False
    )

    result = strategy.generate(config)

    print(f"\n✅ Resultado:")
    print(f"   Portfolio ID: {result.portfolio_id}")
    print(f"   Jogos gerados: {result.n_games}")
    print(f"   Custo total: R$ {result.total_cost:.2f}")
    print(f"   Tempo execução: {result.execution_time:.4f}s")
    print(f"   Sucesso: {result.success}")

    # 4. Estatísticas
    print(f"\n📊 Estatísticas dos Jogos:")
    print(f"   Soma mínima: {result.stats['sum_min']}")
    print(f"   Soma máxima: {result.stats['sum_max']}")
    print(f"   Soma média: {result.stats['sum_avg']:.2f}")
    print(f"   Pares mínimo: {result.stats['even_min']}")
    print(f"   Pares máximo: {result.stats['even_max']}")
    print(f"   Pares médio: {result.stats['even_avg']:.2f}")

    # 5. Estatísticas dos filtros
    print(f"\n📈 Estatísticas dos Filtros:")
    if "filter_stats" in result.stats:
        for filter_name, fstats in result.stats["filter_stats"].items():
            print(f"\n   {filter_name}:")
            print(f"      Avaliados: {fstats['evaluated']}")
            print(f"      Rejeitados: {fstats['rejected']}")
            print(f"      Taxa rejeição: {fstats['rejection_rate']:.1f}%")

    # 6. Mostrar primeiros 3 jogos
    print(f"\n🎮 Primeiros 3 jogos:")
    for i, game in enumerate(result.games[:3]):
        pares = sum(1 for n in game.numbers if n % 2 == 0)
        print(f"   {i+1}. {game.numbers}")
        print(f"      Soma={game.sum}, Pares={pares}")

    # 7. Validar que todos passam nos filtros
    print(f"\n🔍 Validando que todos os jogos passam nos filtros...")
    all_valid = True
    for game in result.games:
        is_valid, reasons = filters.apply(game.numbers)
        if not is_valid:
            all_valid = False
            print(f"   ❌ Jogo inválido: {game.numbers}")
            print(f"      Razões: {reasons}")

    if all_valid:
        print(f"   ✅ Todos os {result.n_games} jogos passam nos filtros!")

    # 8. Teste de performance
    print(f"\n⚡ Teste de performance (50 jogos com filtros)...")
    config2 = StrategyConfig(n_games=50, seed=123, filters=filters, max_attempts=1000)
    result2 = strategy.generate(config2)
    jogos_por_segundo = result2.n_games / result2.execution_time
    print(f"   Gerados: {result2.n_games} jogos")
    print(f"   Tempo: {result2.execution_time:.4f}s")
    print(f"   Taxa: {jogos_por_segundo:.0f} jogos/segundo")

    # 9. Comparar com RandomPure
    print(f"\n📊 Comparação com RandomPure:")
    from app.strategies.random_pure import RandomPureStrategy

    pure_strategy = RandomPureStrategy()
    config_pure = StrategyConfig(n_games=50, seed=123)
    result_pure = pure_strategy.generate(config_pure)

    print(f"   RandomPure:")
    print(f"      Tempo: {result_pure.execution_time:.4f}s")
    print(f"      Taxa: {result_pure.n_games/result_pure.execution_time:.0f} jogos/s")
    print(f"   RandomFiltered:")
    print(f"      Tempo: {result2.execution_time:.4f}s")
    print(f"      Taxa: {result2.n_games/result2.execution_time:.0f} jogos/s")

    slowdown = result2.execution_time / result_pure.execution_time
    print(f"   Overhead dos filtros: {slowdown:.1f}x mais lento")

    print("\n" + "=" * 70)
    print("✅ RandomFiltered Strategy implementada e testada")
    print("=" * 70)
