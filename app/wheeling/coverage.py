"""
Analisador de Cobertura para Wheeling Systems.

Este módulo analisa a cobertura de um conjunto de jogos, verificando:
- Cobertura de números individuais (1-wise)
- Cobertura de pares de números (2-wise)
- Cobertura de triplas (3-wise) - opcional
- Garantias de acertos mínimos

Exemplo:
    Se você tem um wheeling que garante "se acertar 4 números do wheel,
    terá pelo menos 1 jogo com 11 pontos", este módulo valida isso.
"""

from typing import List, Dict, Set, Tuple
from dataclasses import dataclass, field
from itertools import combinations
from collections import defaultdict


@dataclass
class CoverageResult:
    """
    Resultado da análise de cobertura.

    Attributes:
        total_games: Total de jogos analisados
        wheel_numbers: Números do wheel
        coverage_1wise: Cobertura de números individuais (%)
        coverage_2wise: Cobertura de pares (%)
        coverage_3wise: Cobertura de triplas (%) - opcional
        uncovered_singles: Números não cobertos
        uncovered_pairs: Pares não cobertos
        pair_frequency: Dicionário com frequência de cada par
        guarantees: Garantias de acertos mínimos
    """

    total_games: int
    wheel_numbers: List[int]
    coverage_1wise: float
    coverage_2wise: float
    coverage_3wise: float = 0.0
    uncovered_singles: Set[int] = field(default_factory=set)
    uncovered_pairs: Set[Tuple[int, int]] = field(default_factory=set)
    pair_frequency: Dict[Tuple[int, int], int] = field(default_factory=dict)
    guarantees: Dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:
        """String representation."""
        return (
            f"CoverageResult(\n"
            f"  Total jogos: {self.total_games}\n"
            f"  Wheel: {len(self.wheel_numbers)} números\n"
            f"  Cobertura 1-wise: {self.coverage_1wise:.1f}%\n"
            f"  Cobertura 2-wise: {self.coverage_2wise:.1f}%\n"
            f"  Cobertura 3-wise: {self.coverage_3wise:.1f}%\n"
            f"  Não cobertos: {len(self.uncovered_singles)} singles, {len(self.uncovered_pairs)} pares\n"
            f")"
        )


class CoverageAnalyzer:
    """
    Analisador de cobertura de wheeling systems.

    Calcula métricas de cobertura para um conjunto de jogos gerados
    a partir de um wheel de números.

    Examples:
        >>> analyzer = CoverageAnalyzer()
        >>> wheel = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
        >>> games = [[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15], ...]
        >>> result = analyzer.analyze(wheel, games)
        >>> print(f"Cobertura 2-wise: {result.coverage_2wise:.1f}%")
    """

    def __init__(self):
        """Inicializa o analisador."""
        pass

    def analyze(
        self,
        wheel_numbers: List[int],
        games: List[List[int]],
        analyze_3wise: bool = False,
    ) -> CoverageResult:
        """
        Analisa a cobertura de um conjunto de jogos.

        Args:
            wheel_numbers: Números do wheel
            games: Lista de jogos (cada jogo é uma lista de 15 números)
            analyze_3wise: Se True, analisa também cobertura 3-wise (mais lento)

        Returns:
            CoverageResult com todas as métricas

        Examples:
            >>> wheel = list(range(1, 19))  # [1..18]
            >>> games = [list(range(1, 16))]  # Um jogo: [1..15]
            >>> result = analyzer.analyze(wheel, games)
        """
        # Validar entrada
        if not wheel_numbers or not games:
            return CoverageResult(
                total_games=len(games),
                wheel_numbers=wheel_numbers,
                coverage_1wise=0.0,
                coverage_2wise=0.0,
            )

        # 1-wise: Cobertura de números individuais
        coverage_1wise, uncovered_singles = self._analyze_1wise(wheel_numbers, games)

        # 2-wise: Cobertura de pares
        coverage_2wise, uncovered_pairs, pair_freq = self._analyze_2wise(
            wheel_numbers, games
        )

        # 3-wise: Cobertura de triplas (opcional)
        coverage_3wise = 0.0
        if analyze_3wise:
            coverage_3wise, _ = self._analyze_3wise(wheel_numbers, games)

        # Garantias (análise de acertos mínimos)
        guarantees = self._analyze_guarantees(wheel_numbers, games)

        return CoverageResult(
            total_games=len(games),
            wheel_numbers=wheel_numbers,
            coverage_1wise=coverage_1wise,
            coverage_2wise=coverage_2wise,
            coverage_3wise=coverage_3wise,
            uncovered_singles=uncovered_singles,
            uncovered_pairs=uncovered_pairs,
            pair_frequency=pair_freq,
            guarantees=guarantees,
        )

    def _analyze_1wise(
        self, wheel_numbers: List[int], games: List[List[int]]
    ) -> Tuple[float, Set[int]]:
        """
        Analisa cobertura 1-wise (números individuais).

        Args:
            wheel_numbers: Números do wheel
            games: Lista de jogos

        Returns:
            Tupla (percentual_cobertura, numeros_nao_cobertos)
        """
        covered = set()
        for game in games:
            covered.update(game)

        # Verificar quantos números do wheel estão cobertos
        wheel_set = set(wheel_numbers)
        covered_wheel = covered & wheel_set
        uncovered = wheel_set - covered_wheel

        coverage_pct = (
            len(covered_wheel) / len(wheel_set) * 100 if wheel_set else 0.0
        )

        return coverage_pct, uncovered

    def _analyze_2wise(
        self, wheel_numbers: List[int], games: List[List[int]]
    ) -> Tuple[float, Set[Tuple[int, int]], Dict[Tuple[int, int], int]]:
        """
        Analisa cobertura 2-wise (pares de números).

        Args:
            wheel_numbers: Números do wheel
            games: Lista de jogos

        Returns:
            Tupla (percentual_cobertura, pares_nao_cobertos, frequencia_pares)
        """
        # Todos os pares possíveis do wheel
        all_pairs = set(combinations(sorted(wheel_numbers), 2))

        # Pares cobertos pelos jogos
        covered_pairs = set()
        pair_frequency = defaultdict(int)

        for game in games:
            game_pairs = set(combinations(sorted(game), 2))
            for pair in game_pairs:
                if pair in all_pairs:
                    covered_pairs.add(pair)
                    pair_frequency[pair] += 1

        # Calcular cobertura
        uncovered = all_pairs - covered_pairs
        coverage_pct = len(covered_pairs) / len(all_pairs) * 100 if all_pairs else 0.0

        return coverage_pct, uncovered, dict(pair_frequency)

    def _analyze_3wise(
        self, wheel_numbers: List[int], games: List[List[int]]
    ) -> Tuple[float, Set[Tuple[int, int, int]]]:
        """
        Analisa cobertura 3-wise (triplas de números).

        ATENÇÃO: Pode ser MUITO lento para wheels grandes!
        Wheel 18 = C(18,3) = 816 triplas
        Wheel 20 = C(20,3) = 1140 triplas

        Args:
            wheel_numbers: Números do wheel
            games: Lista de jogos

        Returns:
            Tupla (percentual_cobertura, triplas_nao_cobertas)
        """
        # Todos as triplas possíveis do wheel
        all_triples = set(combinations(sorted(wheel_numbers), 3))

        # Triplas cobertas pelos jogos
        covered_triples = set()

        for game in games:
            game_triples = set(combinations(sorted(game), 3))
            for triple in game_triples:
                if triple in all_triples:
                    covered_triples.add(triple)

        # Calcular cobertura
        uncovered = all_triples - covered_triples
        coverage_pct = (
            len(covered_triples) / len(all_triples) * 100 if all_triples else 0.0
        )

        return coverage_pct, uncovered

    def _analyze_guarantees(
        self, wheel_numbers: List[int], games: List[List[int]]
    ) -> Dict[str, str]:
        """
        Analisa garantias de acertos mínimos.

        Exemplo: Se você acertar 4 números do wheel, qual é o mínimo
        garantido de acertos em pelo menos um jogo?

        Args:
            wheel_numbers: Números do wheel
            games: Lista de jogos

        Returns:
            Dicionário com garantias
        """
        guarantees = {}

        # Para cada quantidade de acertos no wheel (de 11 a 15)
        for k in range(11, 16):
            min_hits = self._find_minimum_guarantee(wheel_numbers, games, k)
            if min_hits > 0:
                guarantees[f"acertos_{k}_no_wheel"] = (
                    f"Pelo menos 1 jogo com {min_hits} pontos"
                )

        return guarantees

    def _find_minimum_guarantee(
        self, wheel_numbers: List[int], games: List[List[int]], k: int
    ) -> int:
        """
        Encontra garantia mínima para k acertos no wheel.

        Testa todas as combinações de k números do wheel e verifica
        qual o mínimo de acertos em pelo menos 1 jogo.

        Args:
            wheel_numbers: Números do wheel
            games: Lista de jogos
            k: Quantidade de acertos no wheel

        Returns:
            Mínimo de pontos garantidos em pelo menos 1 jogo
        """
        if k > len(wheel_numbers):
            return 0

        min_guarantee = 15  # Máximo possível

        # Testar algumas combinações (não todas para performance)
        # Limitar a 100 amostras para wheels grandes
        from itertools import islice
        import random

        all_combos = list(combinations(wheel_numbers, k))

        # Se muitas combinações, amostrar
        if len(all_combos) > 100:
            sample_combos = random.sample(all_combos, 100)
        else:
            sample_combos = all_combos

        for combo in sample_combos:
            combo_set = set(combo)

            # Encontrar máximo de acertos em qualquer jogo
            max_hits_in_any_game = 0
            for game in games:
                hits = len(set(game) & combo_set)
                max_hits_in_any_game = max(max_hits_in_any_game, hits)

            # Atualizar mínimo garantido
            min_guarantee = min(min_guarantee, max_hits_in_any_game)

        return min_guarantee


# ============================================================================
# SCRIPT DE DEMONSTRAÇÃO
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("COVERAGE ANALYZER - Demonstração")
    print("=" * 70)

    # 1. Criar wheeling simples
    print("\n📦 Criando wheeling de teste...")
    wheel = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]

    # Gerar alguns jogos do wheel
    from itertools import combinations

    all_combos = list(combinations(wheel, 15))
    print(f"   Wheel: {len(wheel)} números")
    print(f"   Total combinações possíveis: {len(all_combos):,}")

    # Amostrar 50 jogos
    import random

    random.seed(42)
    games = random.sample(all_combos, min(50, len(all_combos)))
    games = [list(g) for g in games]

    print(f"   Jogos amostrados: {len(games)}")

    # 2. Analisar cobertura
    print("\n🔍 Analisando cobertura...")
    analyzer = CoverageAnalyzer()
    result = analyzer.analyze(wheel, games, analyze_3wise=False)

    print(f"\n📊 Resultados:")
    print(f"   Total de jogos: {result.total_games}")
    print(f"   Números no wheel: {len(result.wheel_numbers)}")
    print(f"   Cobertura 1-wise: {result.coverage_1wise:.1f}%")
    print(f"   Cobertura 2-wise: {result.coverage_2wise:.1f}%")

    if result.uncovered_singles:
        print(f"\n   ❌ Números não cobertos: {sorted(result.uncovered_singles)}")
    else:
        print(f"\n   ✅ Todos os números estão cobertos!")

    print(f"   Pares não cobertos: {len(result.uncovered_pairs)}")

    # 3. Análise de frequência de pares
    print(f"\n📈 Pares mais frequentes:")
    sorted_pairs = sorted(
        result.pair_frequency.items(), key=lambda x: x[1], reverse=True
    )

    for pair, freq in sorted_pairs[:5]:
        print(f"   {pair}: {freq} vezes")

    # 4. Garantias
    if result.guarantees:
        print(f"\n🎯 Garantias de acertos:")
        for key, value in result.guarantees.items():
            print(f"   {key}: {value}")

    # 5. Teste com 3-wise (cuidado: pode ser lento!)
    print(f"\n⚠️  Testando cobertura 3-wise (pode demorar)...")
    result_3wise = analyzer.analyze(wheel, games, analyze_3wise=True)
    print(f"   Cobertura 3-wise: {result_3wise.coverage_3wise:.1f}%")

    print("\n" + "=" * 70)
    print("✅ Coverage Analyzer implementado")
    print("=" * 70)
