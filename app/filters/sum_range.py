"""
Filtro de range de soma.

Valida se a soma dos números está dentro de um intervalo [min, max].
"""

from typing import List, Dict, Any, Optional
from app.filters.base import Filter


class SumRangeFilter(Filter):
    """
    Filtro que valida se a soma está dentro do range permitido.

    A soma média histórica da Lotofácil é aproximadamente 187.
    Range típico: 160-210 (conservador) ou 155-215 (liberal)

    Attributes:
        min_sum: Soma mínima permitida
        max_sum: Soma máxima permitida
    """

    def __init__(
        self,
        min_sum: int = 160,
        max_sum: int = 210,
        enabled: bool = True
    ):
        """
        Inicializa o filtro de soma.

        Args:
            min_sum: Soma mínima permitida (padrão: 160)
            max_sum: Soma máxima permitida (padrão: 210)
            enabled: Se o filtro está ativo

        Examples:
            >>> filter = SumRangeFilter(min_sum=170, max_sum=200)
            >>> filter.validate([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])
            (False, "Soma 120 fora do range [170, 200]")
        """
        super().__init__("sum_range", enabled)
        self.min_sum = min_sum
        self.max_sum = max_sum

        # Validação dos parâmetros
        if min_sum < 120:  # Soma mínima possível: 1+2+...+15 = 120
            raise ValueError("min_sum não pode ser menor que 120")
        if max_sum > 255:  # Soma máxima possível: 11+12+...+25 = 255
            raise ValueError("max_sum não pode ser maior que 255")
        if min_sum > max_sum:
            raise ValueError("min_sum não pode ser maior que max_sum")

    def validate(self, game: List[int]) -> tuple[bool, Optional[str]]:
        """
        Valida se a soma do jogo está dentro do range.

        Args:
            game: Lista de 15 números

        Returns:
            Tupla (válido, razão)
        """
        soma = sum(game)

        if soma < self.min_sum:
            return False, f"Soma {soma} abaixo do mínimo {self.min_sum}"

        if soma > self.max_sum:
            return False, f"Soma {soma} acima do máximo {self.max_sum}"

        return True, None

    def get_config(self) -> Dict[str, Any]:
        """Retorna configuração do filtro."""
        return {
            "filter_type": "sum_range",
            "min_sum": self.min_sum,
            "max_sum": self.max_sum,
            "enabled": self.enabled,
        }

    def __str__(self) -> str:
        status = "✓" if self.enabled else "✗"
        return f"{status} SumRange[{self.min_sum}, {self.max_sum}]"


if __name__ == "__main__":
    print("=" * 70)
    print("Filtro: SumRange")
    print("=" * 70)

    # Criar filtro com range moderado
    filtro = SumRangeFilter(min_sum=170, max_sum=200)
    print(f"\n✓ {filtro}")

    # Casos de teste
    test_cases = [
        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], 120, False),  # Muito baixo
        ([5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19], 185, True),  # OK
        ([11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25], 255, False),  # Muito alto
        ([1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 20, 21, 22, 23, 24], 190, True),  # OK
    ]

    print("\n📊 Testando jogos:")
    print("-" * 70)
    for jogo, soma_esperada, deve_passar in test_cases:
        valido, razao = filtro.apply(jogo)
        soma_real = sum(jogo)

        status = "✓ ACEITO" if valido else "✗ REJEITADO"
        resultado = "✓" if valido == deve_passar else "✗ ERRO"

        print(f"\n{resultado} Jogo (soma={soma_real}):")
        print(f"   Resultado: {status}")
        if razao:
            print(f"   Razão: {razao}")

    # Estatísticas
    print(f"\n📈 Estatísticas:")
    print("-" * 70)
    print(filtro.stats)

    print("\n" + "=" * 70)
