"""
Filtro de quantidade de números pares e ímpares.

Valida se a distribuição de pares/ímpares está dentro do esperado.
"""

from typing import List, Dict, Any, Optional
from app.filters.base import Filter


class EvenOddFilter(Filter):
    """
    Filtro que valida distribuição de números pares e ímpares.

    A distribuição média histórica é ~7-8 pares e ~7-8 ímpares.
    Extremos (0 pares ou 15 pares) são raros.

    Attributes:
        min_even: Mínimo de números pares
        max_even: Máximo de números pares
    """

    def __init__(
        self,
        min_even: int = 6,
        max_even: int = 10,
        enabled: bool = True
    ):
        """
        Inicializa o filtro de pares/ímpares.

        Args:
            min_even: Mínimo de pares permitido (padrão: 6)
            max_even: Máximo de pares permitido (padrão: 10)
            enabled: Se o filtro está ativo

        Examples:
            >>> filter = EvenOddFilter(min_even=7, max_even=8)
            >>> filter.validate([2,4,6,8,10,12,14,16,18,20,22,24,1,3,5])
            (False, "11 pares fora do range [7, 8]")
        """
        super().__init__("even_odd", enabled)
        self.min_even = min_even
        self.max_even = max_even

        # Validação dos parâmetros
        if min_even < 0:
            raise ValueError("min_even não pode ser negativo")
        if max_even > 15:
            raise ValueError("max_even não pode ser maior que 15")
        if min_even > max_even:
            raise ValueError("min_even não pode ser maior que max_even")

    def validate(self, game: List[int]) -> tuple[bool, Optional[str]]:
        """
        Valida distribuição de pares/ímpares.

        Args:
            game: Lista de 15 números

        Returns:
            Tupla (válido, razão)
        """
        pares = sum(1 for n in game if n % 2 == 0)
        impares = 15 - pares

        if pares < self.min_even:
            return False, f"{pares} pares (mín: {self.min_even})"

        if pares > self.max_even:
            return False, f"{pares} pares (máx: {self.max_even})"

        return True, None

    def get_config(self) -> Dict[str, Any]:
        """Retorna configuração do filtro."""
        min_odd = 15 - self.max_even
        max_odd = 15 - self.min_even

        return {
            "filter_type": "even_odd",
            "min_even": self.min_even,
            "max_even": self.max_even,
            "min_odd": min_odd,
            "max_odd": max_odd,
            "enabled": self.enabled,
        }

    def __str__(self) -> str:
        status = "✓" if self.enabled else "✗"
        min_odd = 15 - self.max_even
        max_odd = 15 - self.min_even
        return f"{status} EvenOdd[pares:{self.min_even}-{self.max_even}, ímpares:{min_odd}-{max_odd}]"


if __name__ == "__main__":
    print("=" * 70)
    print("Filtro: EvenOdd")
    print("=" * 70)

    # Criar filtro balanceado
    filtro = EvenOddFilter(min_even=7, max_even=8)
    print(f"\n✓ {filtro}")

    # Casos de teste
    test_cases = [
        # (jogo, qtd_pares, deve_passar)
        ([2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 1, 3, 5], 12, False),  # Muitos pares
        ([1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 2, 4], 2, False),   # Poucos pares
        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], 7, True),      # 7 pares - OK
        ([2, 4, 6, 8, 10, 12, 14, 16, 1, 3, 5, 7, 9, 11, 13], 8, True),      # 8 pares - OK
    ]

    print("\n📊 Testando jogos:")
    print("-" * 70)
    for jogo, pares_esperado, deve_passar in test_cases:
        valido, razao = filtro.apply(jogo)
        pares_real = sum(1 for n in jogo if n % 2 == 0)
        impares_real = 15 - pares_real

        status = "✓ ACEITO" if valido else "✗ REJEITADO"
        resultado = "✓" if valido == deve_passar else "✗ ERRO"

        print(f"\n{resultado} Jogo (pares={pares_real}, ímpares={impares_real}):")
        print(f"   Resultado: {status}")
        if razao:
            print(f"   Razão: {razao}")

    # Estatísticas
    print(f"\n📈 Estatísticas:")
    print("-" * 70)
    print(filtro.stats)

    # Testar com filtro liberal
    print(f"\n🔧 Filtro Liberal:")
    print("-" * 70)
    filtro_liberal = EvenOddFilter(min_even=5, max_even=11)
    print(f"{filtro_liberal}")

    # Caso extremo que só passa no liberal
    jogo_extremo = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 1, 3, 5, 7]  # 11 pares
    pares = sum(1 for n in jogo_extremo if n % 2 == 0)

    valido, razao = filtro_liberal.apply(jogo_extremo)
    print(f"\n  Jogo extremo ({pares} pares): {'✓ ACEITO' if valido else '✗ REJEITADO'}")

    print("\n" + "=" * 70)
