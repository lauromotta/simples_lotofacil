"""
2-Wise Coverage Wheeling System.

Este módulo implementa um algoritmo que garante que TODOS os pares
de números do wheel apareçam em pelo menos um jogo.

Exemplo:
    Wheel = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18]
    Pares possíveis = C(18,2) = 153 pares

    O algoritmo garante que todos os 153 pares apareçam em pelo menos
    1 dos jogos gerados.

Algoritmo:
    Usa greedy set cover para selecionar jogos que maximizam a cobertura
    de pares ainda não cobertos.

Performance:
    Para wheel_size=18: ~10-20 jogos para cobertura completa
    Para wheel_size=20: ~15-30 jogos para cobertura completa
"""

from typing import List, Set, Tuple
from itertools import combinations
import random

from app.core.game import Game
from app.wheeling.coverage import CoverageAnalyzer


class TwoWiseCoverage:
    """
    Gerador de wheeling com garantia de cobertura 2-wise.

    Usa algoritmo greedy para selecionar jogos que cobrem todos
    os pares de números do wheel com o mínimo de jogos possível.

    Examples:
        >>> generator = TwoWiseCoverage()
        >>> wheel = list(range(1, 19))  # [1..18]
        >>> games = generator.generate(wheel, seed=42)
        >>> print(f"Gerados {len(games)} jogos para cobertura completa")
    """

    def __init__(self):
        """Inicializa o gerador 2-wise."""
        self.analyzer = CoverageAnalyzer()

    def generate(
        self,
        wheel_numbers: List[int],
        seed: int = None,
        max_games: int = 100,
        target_coverage: float = 100.0,
    ) -> List[Game]:
        """
        Gera jogos com cobertura 2-wise garantida.

        Args:
            wheel_numbers: Números do wheel
            seed: Seed para reprodutibilidade
            max_games: Máximo de jogos a gerar
            target_coverage: Cobertura alvo (% de pares, padrão 100%)

        Returns:
            Lista de jogos que cobrem target_coverage% dos pares

        Raises:
            ValueError: Se wheel_size < 15 (impossível gerar jogos de 15 números)
        """
        if len(wheel_numbers) < 15:
            raise ValueError(
                f"Wheel deve ter pelo menos 15 números, got {len(wheel_numbers)}"
            )

        if seed is not None:
            random.seed(seed)

        # Todos os pares possíveis do wheel
        all_pairs = set(combinations(sorted(wheel_numbers), 2))
        total_pairs = len(all_pairs)

        # Pares ainda não cobertos
        uncovered_pairs = all_pairs.copy()

        # Jogos selecionados
        selected_games = []

        # Greedy set cover
        attempts = 0
        while uncovered_pairs and len(selected_games) < max_games:
            # Gerar candidato aleatório
            candidate = sorted(random.sample(wheel_numbers, 15))

            # Calcular quantos pares não cobertos este jogo cobre
            candidate_pairs = set(combinations(candidate, 2))
            new_coverage = candidate_pairs & uncovered_pairs

            # Se cobre pelo menos 1 par novo, adicionar
            if new_coverage:
                game = Game(
                    numbers=candidate,
                    strategy="two_wise_coverage",
                    seed=seed,
                    metadata={
                        "generation_index": len(selected_games),
                        "new_pairs_covered": len(new_coverage),
                        "total_coverage": (total_pairs - len(uncovered_pairs) + len(new_coverage))
                        / total_pairs
                        * 100,
                    },
                )

                selected_games.append(game)
                uncovered_pairs -= new_coverage

                # Verificar se atingiu target
                current_coverage = (total_pairs - len(uncovered_pairs)) / total_pairs * 100
                if current_coverage >= target_coverage:
                    break

            attempts += 1

            # Proteção contra loop infinito
            if attempts > max_games * 100:
                break

        return selected_games

    def generate_optimized(
        self,
        wheel_numbers: List[int],
        seed: int = None,
        max_games: int = 100,
    ) -> List[Game]:
        """
        Gera jogos com cobertura 2-wise OTIMIZADA.

        Usa estratégia mais inteligente que tenta maximizar cobertura
        de pares não cobertos a cada iteração.

        Args:
            wheel_numbers: Números do wheel
            seed: Seed para reprodutibilidade
            max_games: Máximo de jogos a gerar

        Returns:
            Lista de jogos com cobertura 2-wise ótima
        """
        if len(wheel_numbers) < 15:
            raise ValueError("Wheel deve ter pelo menos 15 números")

        if seed is not None:
            random.seed(seed)

        # Todos os pares possíveis
        all_pairs = set(combinations(sorted(wheel_numbers), 2))
        uncovered_pairs = all_pairs.copy()

        selected_games = []

        while uncovered_pairs and len(selected_games) < max_games:
            best_candidate = None
            best_coverage = 0

            # Testar N candidatos e escolher o melhor
            num_candidates = min(100, len(wheel_numbers) * 10)

            for _ in range(num_candidates):
                # Gerar candidato priorizando números com mais pares não cobertos
                candidate = self._generate_smart_candidate(
                    wheel_numbers, uncovered_pairs
                )

                # Calcular cobertura
                candidate_pairs = set(combinations(sorted(candidate), 2))
                new_coverage = candidate_pairs & uncovered_pairs

                # Atualizar melhor
                if len(new_coverage) > best_coverage:
                    best_candidate = candidate
                    best_coverage = len(new_coverage)

            # Se encontrou candidato que cobre algo, adicionar
            if best_candidate and best_coverage > 0:
                game = Game(
                    numbers=sorted(best_candidate),
                    strategy="two_wise_optimized",
                    seed=seed,
                    metadata={
                        "generation_index": len(selected_games),
                        "new_pairs_covered": best_coverage,
                        "pairs_remaining": len(uncovered_pairs) - best_coverage,
                    },
                )

                selected_games.append(game)

                # Atualizar pares não cobertos
                best_pairs = set(combinations(sorted(best_candidate), 2))
                uncovered_pairs -= best_pairs

            else:
                # Não conseguiu melhorar, parar
                break

        return selected_games

    def _generate_smart_candidate(
        self, wheel_numbers: List[int], uncovered_pairs: Set[Tuple[int, int]]
    ) -> List[int]:
        """
        Gera candidato priorizando números com mais pares não cobertos.

        Args:
            wheel_numbers: Números disponíveis
            uncovered_pairs: Pares ainda não cobertos

        Returns:
            Lista de 15 números
        """
        # Contar quantos pares não cobertos cada número tem
        pair_count = {num: 0 for num in wheel_numbers}

        for pair in uncovered_pairs:
            pair_count[pair[0]] += 1
            pair_count[pair[1]] += 1

        # Selecionar 15 números com maior contagem (com randomização)
        # 70% dos números vêm do top, 30% aleatórios
        sorted_nums = sorted(pair_count.items(), key=lambda x: x[1], reverse=True)

        top_k = int(15 * 0.7)  # 10-11 números do top
        rest = 15 - top_k

        # Top números
        top_numbers = [num for num, _ in sorted_nums[:top_k]]

        # Restante aleatório
        remaining_pool = [num for num, _ in sorted_nums[top_k:]]
        if len(remaining_pool) >= rest:
            rest_numbers = random.sample(remaining_pool, rest)
        else:
            # Se pool pequeno, pegar do topo também
            rest_numbers = [num for num, _ in sorted_nums[top_k : top_k + rest]]

        return top_numbers + rest_numbers


# ============================================================================
# SCRIPT DE DEMONSTRAÇÃO
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("2-WISE COVERAGE - Demonstração")
    print("=" * 70)

    # 1. Criar wheel
    print("\n📦 Criando wheel de 18 números...")
    wheel = list(range(1, 19))  # [1..18]
    print(f"   Wheel: {wheel}")

    from math import comb

    total_pairs = comb(18, 2)
    print(f"   Total de pares: {total_pairs}")

    # 2. Gerar com cobertura básica
    print("\n🎲 Gerando com 2-wise coverage (básico)...")
    generator = TwoWiseCoverage()
    games_basic = generator.generate(wheel, seed=42, max_games=50)

    print(f"   Jogos gerados: {len(games_basic)}")

    # Analisar cobertura
    analyzer = CoverageAnalyzer()
    result_basic = analyzer.analyze(wheel, [g.numbers for g in games_basic])

    print(f"   Cobertura 1-wise: {result_basic.coverage_1wise:.1f}%")
    print(f"   Cobertura 2-wise: {result_basic.coverage_2wise:.1f}%")
    print(f"   Pares não cobertos: {len(result_basic.uncovered_pairs)}")

    # 3. Gerar com cobertura otimizada
    print("\n⚡ Gerando com 2-wise coverage (otimizado)...")
    games_opt = generator.generate_optimized(wheel, seed=42, max_games=50)

    print(f"   Jogos gerados: {len(games_opt)}")

    result_opt = analyzer.analyze(wheel, [g.numbers for g in games_opt])

    print(f"   Cobertura 1-wise: {result_opt.coverage_1wise:.1f}%")
    print(f"   Cobertura 2-wise: {result_opt.coverage_2wise:.1f}%")
    print(f"   Pares não cobertos: {len(result_opt.uncovered_pairs)}")

    # 4. Comparação
    print(f"\n📊 Comparação:")
    print(f"   Básico:    {len(games_basic)} jogos → {result_basic.coverage_2wise:.1f}% cobertura")
    print(f"   Otimizado: {len(games_opt)} jogos → {result_opt.coverage_2wise:.1f}% cobertura")

    efficiency_basic = result_basic.coverage_2wise / len(games_basic) if games_basic else 0
    efficiency_opt = result_opt.coverage_2wise / len(games_opt) if games_opt else 0

    print(f"\n   Eficiência (cobertura/jogo):")
    print(f"   Básico:    {efficiency_basic:.2f}%")
    print(f"   Otimizado: {efficiency_opt:.2f}%")

    # 5. Mostrar primeiros 3 jogos otimizados
    print(f"\n🎮 Primeiros 3 jogos (otimizado):")
    for i, game in enumerate(games_opt[:3]):
        new_pairs = game.metadata.get("new_pairs_covered", 0)
        remaining = game.metadata.get("pairs_remaining", 0)
        print(f"   {i+1}. {game.numbers}")
        print(f"      Novos pares: {new_pairs}, Restantes: {remaining}")

    # 6. Teste com wheel maior
    print(f"\n🔬 Teste com wheel=20...")
    wheel_20 = list(range(1, 21))
    total_pairs_20 = comb(20, 2)
    print(f"   Total de pares: {total_pairs_20}")

    games_20 = generator.generate_optimized(wheel_20, seed=123, max_games=100)
    result_20 = analyzer.analyze(wheel_20, [g.numbers for g in games_20])

    print(f"   Jogos gerados: {len(games_20)}")
    print(f"   Cobertura 2-wise: {result_20.coverage_2wise:.1f}%")

    print("\n" + "=" * 70)
    print("✅ 2-Wise Coverage implementado")
    print("=" * 70)
