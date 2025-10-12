"""
Key Number Wheeling System.

Este módulo implementa wheeling com "números-chave" que aparecem
em TODOS os jogos do portfolio.

Exemplo:
    Key numbers = [7, 13, 21]
    Wheel = [1,2,3,4,5,6,8,9,10,11,12,14,15,16,17,18,19,20]

    Todos os jogos gerados conterão 7, 13 e 21.
    Os outros 12 números variam entre os números do wheel.

Uso:
    - Números "favoritos" ou "quentes"
    - Datas especiais (aniversários)
    - Números com padrões históricos favoráveis

Vantagem:
    Se os key numbers forem sorteados, TODOS os jogos terão esses acertos.

Desvantagem:
    Se os key numbers NÃO forem sorteados, TODOS os jogos perdem esses acertos.
"""

from typing import List, Set
from itertools import combinations
import random

from app.core.game import Game
from app.core.combinatorics import TAMANHO_JOGO


class KeyNumberWheeling:
    """
    Gerador de wheeling com key numbers (números fixos).

    Gera jogos onde certos números aparecem em TODOS os jogos.

    Examples:
        >>> generator = KeyNumberWheeling()
        >>> key_nums = [7, 13, 21]
        >>> other_nums = [1,2,3,4,5,6,8,9,10,11,12,14,15,16,17,18]
        >>> games = generator.generate(key_nums, other_nums, n_games=10, seed=42)
        >>> # Todos os jogos terão [7, 13, 21] + 12 outros números
    """

    def __init__(self):
        """Inicializa o gerador de key number wheeling."""
        pass

    def generate(
        self,
        key_numbers: List[int],
        other_numbers: List[int],
        n_games: int,
        seed: int = None,
        ensure_all_others: bool = False,
    ) -> List[Game]:
        """
        Gera jogos com key numbers fixos.

        Args:
            key_numbers: Números que aparecem em TODOS os jogos
            other_numbers: Números que variam entre os jogos
            n_games: Quantidade de jogos a gerar
            seed: Seed para reprodutibilidade
            ensure_all_others: Se True, garante que todos os other_numbers
                              apareçam em pelo menos 1 jogo

        Returns:
            Lista de jogos com key numbers

        Raises:
            ValueError: Se configuração for inválida

        Examples:
            >>> gen = KeyNumberWheeling()
            >>> games = gen.generate([7,13], [1,2,3,4,5,6,8,9,10,11,12,14,15,16,17,18], 10)
        """
        # Validações
        if len(key_numbers) >= TAMANHO_JOGO:
            raise ValueError(
                f"Key numbers ({len(key_numbers)}) deve ser < {TAMANHO_JOGO}"
            )

        slots_remaining = TAMANHO_JOGO - len(key_numbers)

        if len(other_numbers) < slots_remaining:
            raise ValueError(
                f"Precisa de pelo menos {slots_remaining} outros números, "
                f"got {len(other_numbers)}"
            )

        # Verificar overlap
        key_set = set(key_numbers)
        other_set = set(other_numbers)
        if key_set & other_set:
            raise ValueError("Key numbers e other numbers não podem ter overlap")

        if seed is not None:
            random.seed(seed)

        games = []
        seen_combinations: Set[frozenset] = set()

        # Se ensure_all_others, começar com combinações que cobrem todos
        if ensure_all_others:
            games = self._generate_with_coverage(
                key_numbers, other_numbers, n_games, slots_remaining
            )
        else:
            # Gerar aleatoriamente
            for i in range(n_games):
                attempt = 0
                max_attempts = 1000

                while attempt < max_attempts:
                    # Selecionar slots_remaining números dos others
                    selected_others = random.sample(other_numbers, slots_remaining)

                    # Combinar com key numbers
                    full_game = sorted(key_numbers + selected_others)

                    # Verificar duplicatas
                    game_set = frozenset(full_game)
                    if game_set not in seen_combinations:
                        seen_combinations.add(game_set)

                        game = Game(
                            numbers=full_game,
                            strategy="key_number_wheeling",
                            seed=seed,
                            metadata={
                                "generation_index": i,
                                "key_numbers": key_numbers,
                                "other_numbers": selected_others,
                            },
                        )

                        games.append(game)
                        break

                    attempt += 1

                if attempt >= max_attempts:
                    # Não conseguiu gerar jogo único
                    break

        return games

    def _generate_with_coverage(
        self,
        key_numbers: List[int],
        other_numbers: List[int],
        n_games: int,
        slots_remaining: int,
    ) -> List[Game]:
        """
        Gera jogos garantindo que todos os other_numbers apareçam.

        Args:
            key_numbers: Key numbers fixos
            other_numbers: Pool de outros números
            n_games: Quantidade de jogos
            slots_remaining: Slots disponíveis por jogo

        Returns:
            Lista de jogos com cobertura completa
        """
        # Gerar todas as combinações possíveis
        all_combos = list(combinations(other_numbers, slots_remaining))

        # Se n_games >= total combos, pegar todas
        if n_games >= len(all_combos):
            selected_combos = all_combos
        else:
            # Estratégia: garantir cobertura de todos os números
            # 1. Identificar quantas vezes cada número precisa aparecer
            min_appearances = (n_games * slots_remaining) // len(other_numbers)

            # 2. Greedy: selecionar combinações que balanceiam cobertura
            number_count = {num: 0 for num in other_numbers}
            selected_combos = []

            # Shuffle para randomização
            shuffled_combos = all_combos.copy()
            random.shuffle(shuffled_combos)

            for combo in shuffled_combos:
                if len(selected_combos) >= n_games:
                    break

                # Calcular score (prioriza números com menos aparições)
                score = sum(1 / (number_count[num] + 1) for num in combo)

                # Aceitar se score bom ou se precisamos de mais jogos
                if score > 0:  # Sempre aceita
                    selected_combos.append(combo)

                    # Atualizar contadores
                    for num in combo:
                        number_count[num] += 1

        # Criar jogos
        games = []
        for i, combo in enumerate(selected_combos[:n_games]):
            full_game = sorted(key_numbers + list(combo))

            game = Game(
                numbers=full_game,
                strategy="key_number_coverage",
                seed=None,
                metadata={
                    "generation_index": i,
                    "key_numbers": key_numbers,
                    "other_numbers": list(combo),
                },
            )

            games.append(game)

        return games

    def analyze_coverage(
        self, key_numbers: List[int], other_numbers: List[int], games: List[Game]
    ) -> dict:
        """
        Analisa cobertura dos other_numbers nos jogos.

        Args:
            key_numbers: Key numbers
            other_numbers: Pool de outros números
            games: Jogos gerados

        Returns:
            Dicionário com estatísticas de cobertura
        """
        # Verificar cobertura de key numbers
        key_coverage = all(
            all(kn in game.numbers for kn in key_numbers) for game in games
        )

        # Verificar cobertura de other numbers
        covered_others = set()
        other_frequency = {num: 0 for num in other_numbers}

        for game in games:
            for num in game.numbers:
                if num in other_numbers:
                    covered_others.add(num)
                    other_frequency[num] += 1

        uncovered = set(other_numbers) - covered_others

        return {
            "total_games": len(games),
            "key_numbers": key_numbers,
            "key_coverage": key_coverage,
            "other_numbers_pool": len(other_numbers),
            "others_covered": len(covered_others),
            "others_uncovered": len(uncovered),
            "coverage_percentage": len(covered_others) / len(other_numbers) * 100
            if other_numbers
            else 0,
            "uncovered_numbers": sorted(uncovered),
            "frequency": other_frequency,
            "min_frequency": min(other_frequency.values()) if other_frequency else 0,
            "max_frequency": max(other_frequency.values()) if other_frequency else 0,
            "avg_frequency": sum(other_frequency.values()) / len(other_frequency)
            if other_frequency
            else 0,
        }


# ============================================================================
# SCRIPT DE DEMONSTRAÇÃO
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("KEY NUMBER WHEELING - Demonstração")
    print("=" * 70)

    # 1. Configurar key numbers e pool
    print("\n📦 Configurando Key Number Wheeling...")
    key_nums = [7, 13, 21]  # 3 números fixos
    other_nums = [1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18, 19, 20]  # 18 números variáveis

    print(f"   Key numbers (fixos): {key_nums}")
    print(f"   Other numbers (pool): {len(other_nums)} números")
    print(f"   Slots por jogo: 15 - 3 = 12 slots para other numbers")

    from math import comb

    total_combos = comb(len(other_nums), 12)
    print(f"   Combinações possíveis: {total_combos:,}")

    # 2. Gerar sem garantia de cobertura
    print("\n🎲 Gerando 10 jogos (sem garantia de cobertura)...")
    generator = KeyNumberWheeling()
    games_basic = generator.generate(key_nums, other_nums, n_games=10, seed=42)

    print(f"   Jogos gerados: {len(games_basic)}")

    # Analisar
    stats_basic = generator.analyze_coverage(key_nums, other_nums, games_basic)

    print(f"   Key numbers em todos os jogos: {stats_basic['key_coverage']}")
    print(f"   Other numbers cobertos: {stats_basic['others_covered']}/{stats_basic['other_numbers_pool']}")
    print(f"   Cobertura: {stats_basic['coverage_percentage']:.1f}%")

    if stats_basic["uncovered_numbers"]:
        print(f"   Não cobertos: {stats_basic['uncovered_numbers']}")

    # 3. Gerar COM garantia de cobertura
    print("\n✅ Gerando 15 jogos (COM garantia de cobertura)...")
    games_coverage = generator.generate(
        key_nums, other_nums, n_games=15, seed=42, ensure_all_others=True
    )

    print(f"   Jogos gerados: {len(games_coverage)}")

    stats_coverage = generator.analyze_coverage(key_nums, other_nums, games_coverage)

    print(f"   Key numbers em todos os jogos: {stats_coverage['key_coverage']}")
    print(f"   Other numbers cobertos: {stats_coverage['others_covered']}/{stats_coverage['other_numbers_pool']}")
    print(f"   Cobertura: {stats_coverage['coverage_percentage']:.1f}%")

    if stats_coverage["uncovered_numbers"]:
        print(f"   Não cobertos: {stats_coverage['uncovered_numbers']}")
    else:
        print(f"   ✅ Todos os {len(other_nums)} other numbers estão cobertos!")

    # 4. Frequência dos other numbers
    print(f"\n📊 Frequência dos Other Numbers (com cobertura):")
    print(f"   Mínimo: {stats_coverage['min_frequency']} aparições")
    print(f"   Máximo: {stats_coverage['max_frequency']} aparições")
    print(f"   Média: {stats_coverage['avg_frequency']:.2f} aparições")

    # Top 5 mais frequentes
    sorted_freq = sorted(
        stats_coverage["frequency"].items(), key=lambda x: x[1], reverse=True
    )
    print(f"\n   Top 5 mais frequentes:")
    for num, freq in sorted_freq[:5]:
        print(f"      {num}: {freq} vezes")

    # 5. Mostrar primeiros 3 jogos
    print(f"\n🎮 Primeiros 3 jogos (com cobertura):")
    for i, game in enumerate(games_coverage[:3]):
        key_in_game = [n for n in game.numbers if n in key_nums]
        others_in_game = [n for n in game.numbers if n in other_nums]

        print(f"   {i+1}. {game.numbers}")
        print(f"      Keys: {key_in_game} | Others: {others_in_game}")

    # 6. Validar que TODOS os jogos têm os key numbers
    print(f"\n🔍 Validando key numbers em todos os jogos...")
    all_have_keys = True
    for game in games_coverage:
        if not all(kn in game.numbers for kn in key_nums):
            all_have_keys = False
            print(f"   ❌ Jogo sem key numbers: {game.numbers}")

    if all_have_keys:
        print(f"   ✅ Todos os {len(games_coverage)} jogos contêm {key_nums}!")

    # 7. Exemplo com mais key numbers
    print(f"\n🔬 Teste com 5 key numbers...")
    key_5 = [7, 13, 17, 21, 25]
    other_13 = [1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 14, 15, 16, 18, 19, 20, 22, 23, 24]

    games_5keys = generator.generate(key_5, other_13, n_games=20, seed=123, ensure_all_others=True)
    stats_5keys = generator.analyze_coverage(key_5, other_13, games_5keys)

    print(f"   Key numbers: {key_5} ({len(key_5)} números)")
    print(f"   Slots para others: 15 - 5 = 10")
    print(f"   Jogos gerados: {len(games_5keys)}")
    print(f"   Cobertura others: {stats_5keys['coverage_percentage']:.1f}%")

    print("\n" + "=" * 70)
    print("✅ Key Number Wheeling implementado")
    print("=" * 70)
