"""
Filtro de distribuição por quadrantes.

Valida se a distribuição dos números por quadrantes está balanceada.
Quadrantes: Q1(1-6), Q2(7-12), Q3(13-18), Q4(19-25)
"""

from typing import List, Dict, Any, Optional
from app.filters.base import Filter


class QuadrantsFilter(Filter):
    """
    Filtro que valida distribuição de números por quadrantes.

    Quadrantes:
    - Q1: 1-6   (6 números)
    - Q2: 7-12  (6 números)
    - Q3: 13-18 (6 números)
    - Q4: 19-25 (7 números)

    Distribuição equilibrada: ~3-4 números por quadrante.

    Attributes:
        q1_range: Tupla (min, max) para Q1
        q2_range: Tupla (min, max) para Q2
        q3_range: Tupla (min, max) para Q3
        q4_range: Tupla (min, max) para Q4
    """

    def __init__(
        self,
        q1_range: tuple[int, int] = (2, 5),
        q2_range: tuple[int, int] = (2, 5),
        q3_range: tuple[int, int] = (2, 5),
        q4_range: tuple[int, int] = (2, 5),
        enabled: bool = True
    ):
        """
        Inicializa o filtro de quadrantes.

        Args:
            q1_range: Range (min, max) para Q1 [1-6]
            q2_range: Range (min, max) para Q2 [7-12]
            q3_range: Range (min, max) para Q3 [13-18]
            q4_range: Range (min, max) para Q4 [19-25]
            enabled: Se o filtro está ativo

        Examples:
            >>> filter = QuadrantsFilter(
            ...     q1_range=(2,4), q2_range=(3,5),
            ...     q3_range=(3,5), q4_range=(3,5)
            ... )
        """
        super().__init__("quadrants", enabled)
        self.q1_range = q1_range
        self.q2_range = q2_range
        self.q3_range = q3_range
        self.q4_range = q4_range

        # Validação
        self._validate_ranges()

    def _validate_ranges(self) -> None:
        """Valida se os ranges são consistentes."""
        for i, qrange in enumerate([self.q1_range, self.q2_range, self.q3_range, self.q4_range], 1):
            min_val, max_val = qrange

            if min_val < 0:
                raise ValueError(f"Q{i} min não pode ser negativo")
            if max_val > 15:
                raise ValueError(f"Q{i} max não pode ser maior que 15")
            if min_val > max_val:
                raise ValueError(f"Q{i} min não pode ser maior que max")

        # Verificar se a soma mínima não excede 15
        min_total = sum(qr[0] for qr in [self.q1_range, self.q2_range, self.q3_range, self.q4_range])
        if min_total > 15:
            raise ValueError(f"Soma dos mínimos ({min_total}) excede 15")

    def _count_quadrants(self, game: List[int]) -> Dict[str, int]:
        """
        Conta quantos números há em cada quadrante.

        Args:
            game: Lista de números

        Returns:
            Dicionário {q1: count, q2: count, q3: count, q4: count}
        """
        counts = {"q1": 0, "q2": 0, "q3": 0, "q4": 0}

        for num in game:
            if 1 <= num <= 6:
                counts["q1"] += 1
            elif 7 <= num <= 12:
                counts["q2"] += 1
            elif 13 <= num <= 18:
                counts["q3"] += 1
            elif 19 <= num <= 25:
                counts["q4"] += 1

        return counts

    def validate(self, game: List[int]) -> tuple[bool, Optional[str]]:
        """
        Valida distribuição por quadrantes.

        Args:
            game: Lista de 15 números

        Returns:
            Tupla (válido, razão)
        """
        counts = self._count_quadrants(game)

        # Validar cada quadrante
        validations = [
            ("q1", self.q1_range, counts["q1"], "1-6"),
            ("q2", self.q2_range, counts["q2"], "7-12"),
            ("q3", self.q3_range, counts["q3"], "13-18"),
            ("q4", self.q4_range, counts["q4"], "19-25"),
        ]

        for quad, (min_val, max_val), count, range_str in validations:
            if count < min_val:
                return False, f"Q{quad[1]} ({range_str}): {count} números (mín: {min_val})"
            if count > max_val:
                return False, f"Q{quad[1]} ({range_str}): {count} números (máx: {max_val})"

        return True, None

    def get_config(self) -> Dict[str, Any]:
        """Retorna configuração do filtro."""
        return {
            "filter_type": "quadrants",
            "q1_range": {"min": self.q1_range[0], "max": self.q1_range[1], "numbers": "1-6"},
            "q2_range": {"min": self.q2_range[0], "max": self.q2_range[1], "numbers": "7-12"},
            "q3_range": {"min": self.q3_range[0], "max": self.q3_range[1], "numbers": "13-18"},
            "q4_range": {"min": self.q4_range[0], "max": self.q4_range[1], "numbers": "19-25"},
            "enabled": self.enabled,
        }

    def __str__(self) -> str:
        status = "✓" if self.enabled else "✗"
        return (
            f"{status} Quadrants["
            f"Q1:{self.q1_range[0]}-{self.q1_range[1]}, "
            f"Q2:{self.q2_range[0]}-{self.q2_range[1]}, "
            f"Q3:{self.q3_range[0]}-{self.q3_range[1]}, "
            f"Q4:{self.q4_range[0]}-{self.q4_range[1]}]"
        )


if __name__ == "__main__":
    print("=" * 70)
    print("Filtro: Quadrants")
    print("=" * 70)

    # Criar filtro balanceado
    filtro = QuadrantsFilter(
        q1_range=(2, 4),
        q2_range=(3, 5),
        q3_range=(3, 5),
        q4_range=(3, 5)
    )
    print(f"\n✓ {filtro}")

    # Casos de teste
    test_cases = [
        # (jogo, descrição, deve_passar)
        ([1, 2, 3, 4, 5, 6, 7, 15, 16, 17, 18, 19, 20, 21, 22], "Q1=6, outros poucos", False),
        ([1, 2, 7, 8, 9, 10, 13, 14, 15, 16, 19, 20, 21, 22, 23], "Distribuído OK", True),
        ([1, 2, 3, 7, 8, 9, 10, 13, 14, 15, 16, 19, 20, 21, 22], "Q1=3, Q2=4, Q3=4, Q4=4", True),
        ([19, 20, 21, 22, 23, 24, 25, 1, 2, 7, 8, 13, 14, 15, 16], "Q4=7 (muitos)", False),
        ([5, 6, 7, 8, 11, 12, 13, 14, 17, 18, 19, 20, 23, 24, 25], "Balanceado", True),
    ]

    print("\n📊 Testando jogos:")
    print("-" * 70)
    for jogo, descricao, deve_passar in test_cases:
        valido, razao = filtro.apply(jogo)
        counts = filtro._count_quadrants(jogo)

        status = "✓ ACEITO" if valido else "✗ REJEITADO"
        resultado = "✓" if valido == deve_passar else "✗ ERRO"

        print(f"\n{resultado} {descricao}:")
        print(f"   Jogo: {sorted(jogo)}")
        print(f"   Distribuição: Q1={counts['q1']}, Q2={counts['q2']}, Q3={counts['q3']}, Q4={counts['q4']}")
        print(f"   Resultado: {status}")
        if razao:
            print(f"   Razão: {razao}")

    # Estatísticas
    print(f"\n📈 Estatísticas:")
    print("-" * 70)
    print(filtro.stats)

    # Testar filtro liberal
    print(f"\n🔧 Filtro Liberal:")
    print("-" * 70)
    filtro_liberal = QuadrantsFilter(
        q1_range=(0, 6),
        q2_range=(1, 7),
        q3_range=(1, 7),
        q4_range=(1, 7)
    )
    print(f"{filtro_liberal}")

    jogo_extremo = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]  # Q1=6, Q2=6, Q3=3
    counts = filtro_liberal._count_quadrants(jogo_extremo)
    valido, razao = filtro_liberal.apply(jogo_extremo)

    print(f"\n  Jogo extremo: {jogo_extremo}")
    print(f"  Distribuição: Q1={counts['q1']}, Q2={counts['q2']}, Q3={counts['q3']}, Q4={counts['q4']}")
    print(f"  Resultado: {'✓ ACEITO' if valido else '✗ REJEITADO'}")
    if razao:
        print(f"  Razão: {razao}")

    print("\n" + "=" * 70)
