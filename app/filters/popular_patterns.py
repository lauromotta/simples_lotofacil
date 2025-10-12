"""
Filtro de padrões populares.

Evita padrões óbvios que muitas pessoas jogam:
- Sequências simples (1,2,3,4,...)
- Linhas/colunas do volante
- Múltiplos de um número
- Padrões geométricos
"""

from typing import List, Dict, Any, Optional
from app.filters.base import Filter


class PopularPatternsFilter(Filter):
    """
    Filtro que rejeita padrões populares/óbvios.

    Evita jogos com padrões que muitas pessoas jogam,
    o que reduz o prêmio em caso de vitória (mais ganhadores).

    Padrões detectados:
    - Sequências longas (>6 consecutivos)
    - Múltiplos de um número (ex: 5, 10, 15, 20, 25)
    - Primeiros/últimos números (1-15 ou 11-25)
    - Padrões aritméticos simples
    """

    def __init__(self, enabled: bool = True):
        """
        Inicializa o filtro de padrões populares.

        Args:
            enabled: Se o filtro está ativo
        """
        super().__init__("popular_patterns", enabled)

    def _is_long_sequence(self, game: List[int]) -> tuple[bool, str]:
        """Detecta sequências muito longas (>6)."""
        sorted_game = sorted(game)
        max_seq = 1
        current_seq = 1

        for i in range(1, len(sorted_game)):
            if sorted_game[i] == sorted_game[i - 1] + 1:
                current_seq += 1
                max_seq = max(max_seq, current_seq)
            else:
                current_seq = 1

        if max_seq > 6:
            return True, f"Sequência de {max_seq} números (óbvia)"

        return False, ""

    def _is_simple_sequence(self, game: List[int]) -> tuple[bool, str]:
        """Detecta sequência simples tipo 1-15."""
        sorted_game = sorted(game)

        # Checa se é 1,2,3,...,15
        if sorted_game == list(range(1, 16)):
            return True, "Sequência 1-15 (muito popular)"

        # Checa se é 11,12,13,...,25
        if sorted_game == list(range(11, 26)):
            return True, "Sequência 11-25 (muito popular)"

        return False, ""

    def _is_multiples_pattern(self, game: List[int]) -> tuple[bool, str]:
        """Detecta múltiplos de um número."""
        # Checa múltiplos de 5: 5, 10, 15, 20, 25
        multiplos_5 = [5, 10, 15, 20, 25]
        if all(n in game for n in multiplos_5):
            return True, "Todos os múltiplos de 5 (popular)"

        # Checa se maioria são múltiplos de um número
        for divisor in [2, 3, 4, 5]:
            multiplos = [n for n in game if n % divisor == 0]
            if len(multiplos) >= 10:  # 10+ múltiplos do mesmo número
                return True, f"{len(multiplos)} múltiplos de {divisor} (padrão)"

        return False, ""

    def _is_arithmetic_progression(self, game: List[int]) -> tuple[bool, str]:
        """Detecta progressões aritméticas simples."""
        sorted_game = sorted(game)

        # Verificar se é PA com razão constante
        differences = [sorted_game[i+1] - sorted_game[i] for i in range(len(sorted_game)-1)]

        # Se todas as diferenças são iguais = PA perfeita
        if len(set(differences)) == 1:
            razao = differences[0]
            if razao > 1:  # Permitir sequência (razão=1)
                return True, f"PA com razão {razao} (ex: 2,4,6,8...)"

        # Verificar PA parcial (maioria das diferenças iguais)
        from collections import Counter
        freq = Counter(differences)
        most_common_diff, count = freq.most_common(1)[0]

        if count >= 10 and most_common_diff > 1:  # 10+ com mesma diferença
            return True, f"PA parcial com razão {most_common_diff}"

        return False, ""

    def _is_only_odd_or_even(self, game: List[int]) -> tuple[bool, str]:
        """Detecta se são todos pares ou todos ímpares."""
        pares = sum(1 for n in game if n % 2 == 0)

        if pares == 0:
            return True, "Todos ímpares (padrão extremo)"

        if pares == 15:
            return True, "Todos pares (padrão extremo)"

        return False, ""

    def _is_fibonacci_like(self, game: List[int]) -> tuple[bool, str]:
        """Detecta sequências tipo Fibonacci."""
        # Fibonacci: 1, 1, 2, 3, 5, 8, 13, 21
        fib_numbers = {1, 2, 3, 5, 8, 13, 21}
        fib_in_game = [n for n in game if n in fib_numbers]

        if len(fib_in_game) >= 6:  # 6+ números de Fibonacci
            return True, f"{len(fib_in_game)} números Fibonacci (popular)"

        return False, ""

    def _is_prime_pattern(self, game: List[int]) -> tuple[bool, str]:
        """Detecta se maioria são primos."""
        primes_25 = {2, 3, 5, 7, 11, 13, 17, 19, 23}
        primos_in_game = [n for n in game if n in primes_25]

        # Se todos os 9 primos estão no jogo (muito raro naturalmente)
        if len(primos_in_game) == 9:
            return True, "Todos os primos até 25 (padrão)"

        return False, ""

    def validate(self, game: List[int]) -> tuple[bool, Optional[str]]:
        """
        Valida se o jogo contém padrões populares.

        Args:
            game: Lista de 15 números

        Returns:
            Tupla (válido, razão) - False se encontrar padrão popular
        """
        # Lista de checagens
        checks = [
            self._is_simple_sequence,
            self._is_long_sequence,
            self._is_multiples_pattern,
            self._is_arithmetic_progression,
            self._is_only_odd_or_even,
            self._is_fibonacci_like,
            self._is_prime_pattern,
        ]

        for check_func in checks:
            is_pattern, reason = check_func(game)
            if is_pattern:
                return False, f"Padrão popular: {reason}"

        return True, None

    def get_config(self) -> Dict[str, Any]:
        """Retorna configuração do filtro."""
        return {
            "filter_type": "popular_patterns",
            "enabled": self.enabled,
            "patterns_checked": [
                "simple_sequences",
                "long_sequences",
                "multiples",
                "arithmetic_progressions",
                "only_odd_even",
                "fibonacci",
                "primes"
            ]
        }

    def __str__(self) -> str:
        status = "✓" if self.enabled else "✗"
        return f"{status} PopularPatterns[7 checks]"


if __name__ == "__main__":
    print("=" * 70)
    print("Filtro: PopularPatterns")
    print("=" * 70)

    # Criar filtro
    filtro = PopularPatternsFilter()
    print(f"\n✓ {filtro}")

    # Casos de teste
    test_cases = [
        # (jogo, descrição, deve_passar)
        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], "Sequência 1-15", False),
        ([11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25], "Sequência 11-25", False),
        ([2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 5, 7, 9], "PA razão 2", False),
        ([1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 2, 4], "Todos ímpares -2", False),
        ([2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 1, 3, 5], "Todos pares -3", False),
        ([1, 2, 3, 5, 8, 13, 21, 4, 6, 7, 9, 10, 11, 12, 14], "6 Fibonacci", False),
        ([2, 3, 5, 7, 11, 13, 17, 19, 23, 1, 4, 6, 8, 9, 10], "Todos primos", False),
        ([5, 10, 15, 20, 25, 1, 2, 3, 4, 6, 7, 8, 9, 11, 12], "Múltiplos de 5", False),
        ([1, 3, 7, 9, 11, 14, 16, 18, 19, 20, 21, 23, 24, 25, 5], "Aleatório OK", True),
        ([2, 5, 8, 11, 13, 15, 17, 19, 21, 22, 23, 24, 25, 1, 4], "Aleatório OK", True),
    ]

    print("\n📊 Testando jogos:")
    print("-" * 70)
    for jogo, descricao, deve_passar in test_cases:
        valido, razao = filtro.apply(jogo)

        status = "✓ ACEITO" if valido else "✗ REJEITADO"
        resultado = "✓" if valido == deve_passar else "✗ ERRO"

        print(f"\n{resultado} {descricao}:")
        print(f"   Jogo: {sorted(jogo)}")
        print(f"   Resultado: {status}")
        if razao:
            print(f"   Razão: {razao}")

    # Estatísticas
    print(f"\n📈 Estatísticas:")
    print("-" * 70)
    print(filtro.stats)

    # Detalhes de checagens
    print(f"\n🔍 Tipos de Padrões Detectados:")
    print("-" * 70)
    config = filtro.get_config()
    for i, pattern in enumerate(config["patterns_checked"], 1):
        print(f"  {i}. {pattern}")

    print("\n" + "=" * 70)
