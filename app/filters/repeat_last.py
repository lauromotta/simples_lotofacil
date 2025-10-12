"""
Filtro de repetição de números do último sorteio.

Valida quantos números do jogo repetem do último concurso.
Média histórica: ~3 números repetem.
"""

from typing import List, Dict, Any, Optional
from app.filters.base import Filter


class RepeatLastFilter(Filter):
    """
    Filtro que valida repetição de números do último sorteio.

    Estatisticamente, cerca de 2-4 números costumam se repetir
    entre um sorteio e outro.

    Attributes:
        min_repeat: Mínimo de repetições permitido
        max_repeat: Máximo de repetições permitido
        last_draw: Lista de números do último sorteio
    """

    def __init__(
        self,
        last_draw: Optional[List[int]] = None,
        min_repeat: int = 0,
        max_repeat: int = 6,
        enabled: bool = True
    ):
        """
        Inicializa o filtro de repetição.

        Args:
            last_draw: Números do último sorteio (15 números)
            min_repeat: Mínimo de repetições permitido (padrão: 0)
            max_repeat: Máximo de repetições permitido (padrão: 6)
            enabled: Se o filtro está ativo

        Examples:
            >>> last = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
            >>> filter = RepeatLastFilter(last, min_repeat=2, max_repeat=4)
            >>> filter.validate([1,2,3,16,17,18,19,20,21,22,23,24,25,4,5])
            (False, "5 repetições do último sorteio (máx: 4)")
        """
        super().__init__("repeat_last", enabled)
        self.last_draw = set(last_draw) if last_draw else set()
        self.min_repeat = min_repeat
        self.max_repeat = max_repeat

        # Validação
        if min_repeat < 0:
            raise ValueError("min_repeat não pode ser negativo")
        if max_repeat > 15:
            raise ValueError("max_repeat não pode ser maior que 15")
        if min_repeat > max_repeat:
            raise ValueError("min_repeat não pode ser maior que max_repeat")

        if last_draw and len(last_draw) != 15:
            raise ValueError("last_draw deve ter exatamente 15 números")

    def set_last_draw(self, last_draw: List[int]) -> None:
        """
        Atualiza o último sorteio.

        Args:
            last_draw: Lista de 15 números do último sorteio
        """
        if len(last_draw) != 15:
            raise ValueError("last_draw deve ter exatamente 15 números")
        self.last_draw = set(last_draw)

    def validate(self, game: List[int]) -> tuple[bool, Optional[str]]:
        """
        Valida repetições do último sorteio.

        Args:
            game: Lista de 15 números

        Returns:
            Tupla (válido, razão)
        """
        # Se não tem último sorteio definido, aceitar qualquer jogo
        if not self.last_draw:
            return True, None

        # Contar repetições
        game_set = set(game)
        repeticoes = len(game_set & self.last_draw)

        if repeticoes < self.min_repeat:
            return False, f"{repeticoes} repetições do último (mín: {self.min_repeat})"

        if repeticoes > self.max_repeat:
            return False, f"{repeticoes} repetições do último (máx: {self.max_repeat})"

        return True, None

    def get_repeated_numbers(self, game: List[int]) -> List[int]:
        """
        Retorna os números que repetem do último sorteio.

        Args:
            game: Lista de números

        Returns:
            Lista de números repetidos
        """
        if not self.last_draw:
            return []

        game_set = set(game)
        return sorted(list(game_set & self.last_draw))

    def get_config(self) -> Dict[str, Any]:
        """Retorna configuração do filtro."""
        return {
            "filter_type": "repeat_last",
            "min_repeat": self.min_repeat,
            "max_repeat": self.max_repeat,
            "last_draw": sorted(list(self.last_draw)) if self.last_draw else None,
            "has_last_draw": len(self.last_draw) > 0,
            "enabled": self.enabled,
        }

    def __str__(self) -> str:
        status = "✓" if self.enabled else "✗"
        has_draw = "com ref" if self.last_draw else "sem ref"
        return f"{status} RepeatLast[{self.min_repeat}-{self.max_repeat}, {has_draw}]"


if __name__ == "__main__":
    print("=" * 70)
    print("Filtro: RepeatLast")
    print("=" * 70)

    # Último sorteio simulado
    ultimo_sorteio = [1, 3, 4, 7, 9, 10, 12, 14, 15, 16, 19, 21, 22, 24, 25]
    print(f"\n🎲 Último sorteio: {ultimo_sorteio}")

    # Criar filtro
    filtro = RepeatLastFilter(
        last_draw=ultimo_sorteio,
        min_repeat=2,
        max_repeat=4
    )
    print(f"\n✓ {filtro}")

    # Casos de teste
    test_cases = [
        # (jogo, descrição, deve_passar)
        ([1, 3, 4, 7, 9, 5, 6, 8, 11, 13, 17, 18, 20, 23, 2], "5 repetições", False),  # Muitas
        ([5, 6, 8, 11, 13, 17, 18, 20, 23, 2, 26, 1, 3, 4, 7], "ERR: 26 inválido", False),
        ([5, 6, 8, 11, 13, 17, 18, 20, 23, 2, 1, 3, 4, 7, 9], "5 rep (ajustar)", False),
        ([1, 3, 5, 6, 8, 11, 13, 17, 18, 20, 23, 2, 26, 27, 28], "ERR: múltiplos inválidos", False),
        ([5, 6, 8, 11, 13, 17, 18, 20, 23, 2, 26, 1, 3, 4, 7], "ERR: 26 inválido (caso real)", False),
    ]

    # Casos válidos (corrigidos)
    casos_validos = [
        ([2, 5, 6, 8, 11, 13, 17, 18, 20, 23, 1, 3, 4, 7, 9], "5 repetições (muitas)", False),
        ([2, 5, 6, 8, 11, 13, 17, 18, 20, 23, 1, 3, 4, 7, 10], "4 repetições (OK)", True),
        ([2, 5, 6, 8, 11, 13, 17, 18, 20, 23, 1, 3, 4, 7, 11], "ERR: 11 duplicado", False),
        ([2, 5, 6, 8, 11, 13, 17, 18, 20, 23, 1, 3, 10, 7, 12], "4 repetições (OK)", True),
        ([2, 5, 6, 8, 11, 13, 17, 18, 20, 23, 1, 10, 12, 7, 14], "3 repetições (OK)", True),
        ([2, 5, 6, 8, 11, 13, 17, 18, 20, 23, 26, 10, 12, 1, 14], "ERR: 26 > 25", False),
    ]

    print("\n📊 Testando jogos:")
    print("-" * 70)

    # Casos válidos dentro do universo 1-25
    casos_finais = [
        ([2, 5, 6, 8, 11, 13, 17, 18, 20, 23, 1, 3, 4, 7, 9], "5 repetições", False),
        ([2, 5, 6, 8, 11, 13, 17, 18, 20, 23, 1, 3, 4, 7, 10], "4 repetições", True),
        ([2, 5, 6, 8, 11, 13, 17, 18, 20, 23, 1, 3, 10, 12, 7], "4 repetições", True),
        ([2, 5, 6, 8, 11, 13, 17, 18, 20, 23, 1, 10, 12, 14, 7], "3 repetições", True),
        ([2, 5, 6, 8, 11, 13, 17, 18, 20, 23, 10, 12, 14, 1, 7], "2 repetições", True),
        ([2, 5, 6, 8, 11, 13, 17, 18, 20, 23, 10, 12, 14, 1, 26], "ERR", False),  # 26 não existe
    ]

    for jogo, descricao, deve_passar in casos_finais:
        # Validar se jogo é válido (1-25, 15 únicos)
        if len(set(jogo)) != 15 or any(n < 1 or n > 25 for n in jogo):
            print(f"\n✗ SKIP: {descricao} - Jogo inválido")
            continue

        valido, razao = filtro.apply(jogo)
        repetidos = filtro.get_repeated_numbers(jogo)
        qtd_rep = len(repetidos)

        status = "✓ ACEITO" if valido else "✗ REJEITADO"
        resultado = "✓" if valido == deve_passar else "✗ ERRO"

        print(f"\n{resultado} {descricao} ({qtd_rep} repetições):")
        print(f"   Jogo: {sorted(jogo)}")
        print(f"   Repetidos: {repetidos}")
        print(f"   Resultado: {status}")
        if razao:
            print(f"   Razão: {razao}")

    # Estatísticas
    print(f"\n📈 Estatísticas:")
    print("-" * 70)
    print(filtro.stats)

    # Testar sem último sorteio
    print(f"\n🔧 Filtro Sem Último Sorteio:")
    print("-" * 70)
    filtro_sem_ref = RepeatLastFilter(min_repeat=2, max_repeat=4)
    print(f"{filtro_sem_ref}")

    jogo_teste = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    valido, razao = filtro_sem_ref.apply(jogo_teste)

    print(f"\n  Jogo: {jogo_teste}")
    print(f"  Resultado: {'✓ ACEITO' if valido else '✗ REJEITADO'} (sem referência = aceita tudo)")

    print("\n" + "=" * 70)
