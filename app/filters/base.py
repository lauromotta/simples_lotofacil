"""
Sistema base de filtros para validação de jogos.

Define a interface abstrata que todos os filtros devem implementar.
Permite sistema plugável e extensível de filtros.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FilterStats:
    """
    Estatísticas de execução de um filtro.

    Attributes:
        filter_name: Nome do filtro
        total_evaluated: Total de jogos avaliados
        total_rejected: Total de jogos rejeitados
        total_accepted: Total de jogos aceitos
        rejection_rate: Taxa de rejeição (%)
        execution_time_ms: Tempo total de execução (ms)
        reasons: Dicionário com razões de rejeição e contagens
    """
    filter_name: str
    total_evaluated: int = 0
    total_rejected: int = 0
    total_accepted: int = 0
    rejection_rate: float = 0.0
    execution_time_ms: float = 0.0
    reasons: Dict[str, int] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def update(self, accepted: bool, reason: Optional[str] = None) -> None:
        """Atualiza estatísticas com resultado de validação."""
        self.total_evaluated += 1

        if accepted:
            self.total_accepted += 1
        else:
            self.total_rejected += 1
            if reason:
                self.reasons[reason] = self.reasons.get(reason, 0) + 1

        # Atualizar taxa de rejeição
        if self.total_evaluated > 0:
            self.rejection_rate = (self.total_rejected / self.total_evaluated) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "filter_name": self.filter_name,
            "total_evaluated": self.total_evaluated,
            "total_rejected": self.total_rejected,
            "total_accepted": self.total_accepted,
            "rejection_rate": round(self.rejection_rate, 2),
            "execution_time_ms": round(self.execution_time_ms, 2),
            "reasons": self.reasons,
            "created_at": self.created_at.isoformat(),
        }

    def __str__(self) -> str:
        return (
            f"Filter: {self.filter_name}\n"
            f"  Evaluated: {self.total_evaluated}\n"
            f"  Accepted: {self.total_accepted}\n"
            f"  Rejected: {self.total_rejected} ({self.rejection_rate:.2f}%)\n"
            f"  Time: {self.execution_time_ms:.2f}ms"
        )


class Filter(ABC):
    """
    Classe base abstrata para todos os filtros.

    Todos os filtros devem herdar desta classe e implementar:
    - validate(game): Valida um jogo específico
    - get_config(): Retorna configuração do filtro

    Attributes:
        name: Nome do filtro
        enabled: Se o filtro está ativo
        stats: Estatísticas de execução
    """

    def __init__(self, name: str, enabled: bool = True):
        """
        Inicializa o filtro.

        Args:
            name: Nome identificador do filtro
            enabled: Se o filtro está ativo (padrão: True)
        """
        self.name = name
        self.enabled = enabled
        self.stats = FilterStats(filter_name=name)

    @abstractmethod
    def validate(self, game: List[int]) -> tuple[bool, Optional[str]]:
        """
        Valida um jogo contra as regras do filtro.

        Args:
            game: Lista de 15 números do jogo

        Returns:
            Tupla (válido, razão_rejeição)
            - válido: True se passou no filtro, False se foi rejeitado
            - razão_rejeição: String descrevendo o motivo (se rejeitado)

        Examples:
            >>> filter.validate([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])
            (False, "Soma fora do range: 120")
        """
        pass

    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """
        Retorna a configuração atual do filtro.

        Returns:
            Dicionário com parâmetros do filtro
        """
        pass

    def apply(self, game: List[int]) -> tuple[bool, Optional[str]]:
        """
        Aplica o filtro ao jogo (wrapper que atualiza estatísticas).

        Args:
            game: Lista de números do jogo

        Returns:
            Tupla (válido, razão)
        """
        import time

        if not self.enabled:
            return True, None

        start_time = time.perf_counter()
        valid, reason = self.validate(game)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        self.stats.execution_time_ms += elapsed_ms
        self.stats.update(accepted=valid, reason=reason)

        return valid, reason

    def reset_stats(self) -> None:
        """Reseta as estatísticas do filtro."""
        self.stats = FilterStats(filter_name=self.name)

    def get_stats(self) -> FilterStats:
        """Retorna estatísticas do filtro."""
        return self.stats

    def enable(self) -> None:
        """Ativa o filtro."""
        self.enabled = True

    def disable(self) -> None:
        """Desativa o filtro."""
        self.enabled = False

    def __str__(self) -> str:
        status = "✓ Enabled" if self.enabled else "✗ Disabled"
        return f"{self.name} [{status}]"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', enabled={self.enabled})"


class FilterChain:
    """
    Cadeia de filtros aplicados sequencialmente.

    Permite combinar múltiplos filtros e aplicá-los em ordem.
    Se algum filtro rejeitar, o jogo é rejeitado imediatamente (short-circuit).
    """

    def __init__(self, filters: Optional[List[Filter]] = None):
        """
        Inicializa a cadeia de filtros.

        Args:
            filters: Lista de filtros a aplicar (ordem importa)
        """
        self.filters: List[Filter] = filters or []

    def add_filter(self, filter_obj: Filter) -> None:
        """Adiciona um filtro à cadeia."""
        self.filters.append(filter_obj)

    def remove_filter(self, filter_name: str) -> bool:
        """
        Remove um filtro pelo nome.

        Returns:
            True se removeu, False se não encontrou
        """
        for i, f in enumerate(self.filters):
            if f.name == filter_name:
                self.filters.pop(i)
                return True
        return False

    def apply(self, game: List[int]) -> tuple[bool, List[str]]:
        """
        Aplica todos os filtros ao jogo sequencialmente.

        Args:
            game: Lista de números do jogo

        Returns:
            Tupla (válido, lista_de_razões)
            - válido: True se passou em TODOS os filtros
            - lista_de_razões: Lista de razões de rejeição (se houver)
        """
        reasons = []

        for filter_obj in self.filters:
            if not filter_obj.enabled:
                continue

            valid, reason = filter_obj.apply(game)

            if not valid:
                if reason:
                    reasons.append(f"{filter_obj.name}: {reason}")
                else:
                    reasons.append(f"{filter_obj.name}: Rejeitado")

                # Short-circuit: parar na primeira rejeição
                return False, reasons

        return True, reasons

    def validate_all(self, games: List[List[int]]) -> List[tuple[List[int], bool, List[str]]]:
        """
        Valida múltiplos jogos.

        Args:
            games: Lista de jogos

        Returns:
            Lista de tuplas (jogo, válido, razões)
        """
        results = []
        for game in games:
            valid, reasons = self.apply(game)
            results.append((game, valid, reasons))
        return results

    def get_all_stats(self) -> Dict[str, FilterStats]:
        """Retorna estatísticas de todos os filtros."""
        return {f.name: f.get_stats() for f in self.filters}

    def reset_all_stats(self) -> None:
        """Reseta estatísticas de todos os filtros."""
        for f in self.filters:
            f.reset_stats()

    def get_summary(self) -> Dict[str, Any]:
        """Retorna resumo da cadeia de filtros."""
        total_evaluated = sum(f.stats.total_evaluated for f in self.filters)
        total_rejected = sum(f.stats.total_rejected for f in self.filters)
        total_time = sum(f.stats.execution_time_ms for f in self.filters)

        return {
            "total_filters": len(self.filters),
            "enabled_filters": sum(1 for f in self.filters if f.enabled),
            "total_evaluated": total_evaluated,
            "total_rejected": total_rejected,
            "total_time_ms": round(total_time, 2),
            "filters": [
                {
                    "name": f.name,
                    "enabled": f.enabled,
                    "stats": f.stats.to_dict()
                }
                for f in self.filters
            ]
        }

    def __len__(self) -> int:
        return len(self.filters)

    def __str__(self) -> str:
        lines = ["FilterChain:"]
        for i, f in enumerate(self.filters, 1):
            lines.append(f"  {i}. {f}")
        return "\n".join(lines)


if __name__ == "__main__":
    # Exemplo de uso (com filtro dummy)

    class DummyFilter(Filter):
        """Filtro exemplo para demonstração."""

        def __init__(self):
            super().__init__("dummy_filter")

        def validate(self, game: List[int]) -> tuple[bool, Optional[str]]:
            # Rejeita jogos com soma < 100
            soma = sum(game)
            if soma < 100:
                return False, f"Soma muito baixa: {soma}"
            return True, None

        def get_config(self) -> Dict[str, Any]:
            return {"min_sum": 100}

    print("=" * 70)
    print("Sistema de Filtros - Base")
    print("=" * 70)

    # Criar filtro
    filtro = DummyFilter()
    print(f"\n✓ Filtro criado: {filtro}")

    # Testar jogos
    jogo_valido = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
    jogo_invalido = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

    print(f"\n📊 Testando jogo válido (soma={sum(jogo_valido)}):")
    valid, reason = filtro.apply(jogo_valido)
    print(f"  Resultado: {'✓ ACEITO' if valid else '✗ REJEITADO'}")
    if reason:
        print(f"  Razão: {reason}")

    print(f"\n📊 Testando jogo inválido (soma={sum(jogo_invalido)}):")
    valid, reason = filtro.apply(jogo_invalido)
    print(f"  Resultado: {'✓ ACEITO' if valid else '✗ REJEITADO'}")
    if reason:
        print(f"  Razão: {reason}")

    # Estatísticas
    print(f"\n📈 Estatísticas do filtro:")
    print(filtro.stats)

    # FilterChain
    print(f"\n🔗 Testando FilterChain:")
    chain = FilterChain([filtro])
    print(chain)

    valid, reasons = chain.apply(jogo_invalido)
    print(f"\n  Resultado: {'✓ ACEITO' if valid else '✗ REJEITADO'}")
    if reasons:
        print(f"  Razões: {reasons}")

    print("\n" + "=" * 70)
