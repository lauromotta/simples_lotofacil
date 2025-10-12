"""
Filtro de sequências consecutivas.

Valida o tamanho máximo de sequências de números consecutivos.
Exemplo: 1,2,3,4,5 é uma sequência de tamanho 5.
"""

from typing import List, Dict, Any, Optional
from app.filters.base import Filter


class ConsecutiveFilter(Filter):
    """
    Filtro que limita o tamanho de sequências consecutivas.

    Sequências muito longas (ex: 1,2,3,4,5,6,7) são estatisticamente raras.
    Limite típico: 3-4 consecutivos.

    Attributes:
        max_consecutive: Tamanho máximo de sequência permitido
    """

    def __init__(
        self,
        max_consecutive: int = 4,
        enabled: bool = True
    ):
        """
        Inicializa o filtro de consecutivos.

        Args:
            max_consecutive: Tamanho máximo de sequência permitido (padrão: 4)
            enabled: Se o filtro está ativo

        Examples:
            >>> filter = ConsecutiveFilter(max_consecutive=3)
            >>> filter.validate([1,2,3,4,10,11,15,16,18,20,21,22,23,24,25])
            (False, "Sequência de 6 consecutivos encontrada (máx: 3)")
        """
        super().__init__("consecutive", enabled)
        self.max_consecutive = max_consecutive

        # Validação dos parâmetros
        if max_consecutive < 1:
            raise ValueError("max_consecutive deve ser pelo menos 1")
        if max_consecutive > 15:
            raise ValueError("max_consecutive não pode ser maior que 15")

    def validate(self, game: List[int]) -> tuple[bool, Optional[str]]:
        """
        Valida sequências consecutivas.

        Args:
            game: Lista de 15 números

        Returns:
            Tupla (válido, razão)
        """
        # Ordenar jogo
        sorted_game = sorted(game)

        max_seq_found = 1
        current_seq = 1

        for i in range(1, len(sorted_game)):
            if sorted_game[i] == sorted_game[i - 1] + 1:
                current_seq += 1
                max_seq_found = max(max_seq_found, current_seq)
            else:
                current_seq = 1

        if max_seq_found > self.max_consecutive:
            return False, f"Sequência de {max_seq_found} consecutivos (máx: {self.max_consecutive})"

        return True, None

    def get_sequences(self, game: List[int]) -> List[List[int]]:
        """
        Retorna todas as sequências consecutivas encontradas.

        Args:
            game: Lista de números

        Returns:
            Lista de sequências (cada sequência é uma lista)

        Examples:
            >>> filter.get_sequences([1,2,3,5,7,8,10])
            [[1,2,3], [7,8]]
        """
        sorted_game = sorted(game)
        sequences = []
        current_seq = [sorted_game[0]]

        for i in range(1, len(sorted_game)):
            if sorted_game[i] == sorted_game[i - 1] + 1:
                current_seq.append(sorted_game[i])
            else:
                if len(current_seq) >= 2:  # Só considerar sequências de 2+
                    sequences.append(current_seq)
                current_seq = [sorted_game[i]]

        # Verificar última sequência
        if len(current_seq) >= 2:
            sequences.append(current_seq)

        return sequences

    def get_config(self) -> Dict[str, Any]:
        """Retorna configuração do filtro."""
        return {
            "filter_type": "consecutive",
            "max_consecutive": self.max_consecutive,
            "enabled": self.enabled,
        }

    def __str__(self) -> str:
        status = "✓" if self.enabled else "✗"
        return f"{status} Consecutive[máx: {self.max_consecutive}]"


if __name__ == "__main__":
    print("=" * 70)
    print("Filtro: Consecutive")
    print("=" * 70)

    # Criar filtro moderado
    filtro = ConsecutiveFilter(max_consecutive=4)
    print(f"\n✓ {filtro}")

    # Casos de teste
    test_cases = [
        # (jogo, descrição, deve_passar)
        ([1, 2, 3, 4, 5, 6, 7, 8, 15, 16, 17, 18, 19, 20, 21], "Sequência de 8", False),
        ([1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 2, 4], "Sem consecutivos", True),
        ([1, 2, 3, 4, 10, 11, 12, 15, 18, 20, 21, 22, 23, 24, 25], "Várias seq (máx 6)", False),
        ([5, 6, 7, 8, 10, 12, 14, 16, 18, 19, 21, 23, 24, 25, 1], "Seq de 4 (OK)", True),
        ([1, 2, 5, 6, 7, 10, 11, 13, 15, 17, 19, 21, 23, 24, 25], "Seq de 3 (OK)", True),
    ]

    print("\n📊 Testando jogos:")
    print("-" * 70)
    for jogo, descricao, deve_passar in test_cases:
        valido, razao = filtro.apply(jogo)
        seqs = filtro.get_sequences(jogo)
        max_seq = max((len(s) for s in seqs), default=1)

        status = "✓ ACEITO" if valido else "✗ REJEITADO"
        resultado = "✓" if valido == deve_passar else "✗ ERRO"

        print(f"\n{resultado} {descricao} (máx seq: {max_seq}):")
        print(f"   Jogo: {sorted(jogo)}")
        if seqs:
            print(f"   Sequências: {seqs}")
        print(f"   Resultado: {status}")
        if razao:
            print(f"   Razão: {razao}")

    # Estatísticas
    print(f"\n📈 Estatísticas:")
    print("-" * 70)
    print(filtro.stats)

    # Testar filtro rigoroso
    print(f"\n🔧 Filtro Rigoroso (máx: 2):")
    print("-" * 70)
    filtro_rigoroso = ConsecutiveFilter(max_consecutive=2)
    print(f"{filtro_rigoroso}")

    jogo_teste = [1, 2, 5, 8, 10, 12, 14, 16, 18, 20, 21, 23, 24, 25, 3]
    valido, razao = filtro_rigoroso.apply(jogo_teste)
    seqs = filtro_rigoroso.get_sequences(jogo_teste)

    print(f"\n  Jogo: {sorted(jogo_teste)}")
    print(f"  Sequências: {seqs}")
    print(f"  Resultado: {'✓ ACEITO' if valido else '✗ REJEITADO'}")
    if razao:
        print(f"  Razão: {razao}")

    print("\n" + "=" * 70)
