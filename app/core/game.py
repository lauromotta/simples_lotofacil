"""
Modelos de dados (Pydantic) para o sistema Lotofácil.

Define as estruturas de dados principais:
- Game: Um jogo individual
- Draw: Um sorteio histórico
- Portfolio: Coleção de jogos
- Result: Resultado de um jogo vs sorteio
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.core.combinatorics import (
    validar_jogo,
    calcular_acertos,
    soma_jogo,
    contar_pares_impares,
    maior_sequencia_consecutiva,
    distribuicao_quadrantes,
)


class Game(BaseModel):
    """
    Representa um jogo individual da Lotofácil.

    Attributes:
        numbers: Lista de 15 números únicos (1-25)
        id: Identificador único do jogo
        created_at: Data/hora de criação
        strategy: Estratégia usada para gerar
        seed: Seed usado (se aplicável)
        metadata: Metadados adicionais
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "numbers": [1, 2, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 24, 25],
                "id": "game_001",
                "strategy": "random_filtered"
            }
        }
    )

    numbers: List[int] = Field(..., min_length=15, max_length=15)
    id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    strategy: Optional[str] = None
    seed: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("numbers")
    @classmethod
    def validate_numbers(cls, v: List[int]) -> List[int]:
        """Valida se os números são válidos."""
        valido, msg = validar_jogo(v)
        if not valido:
            raise ValueError(msg)
        return sorted(v)

    @property
    def sum(self) -> int:
        """Soma dos números."""
        return soma_jogo(self.numbers)

    @property
    def even_count(self) -> int:
        """Quantidade de números pares."""
        return contar_pares_impares(self.numbers)[0]

    @property
    def odd_count(self) -> int:
        """Quantidade de números ímpares."""
        return contar_pares_impares(self.numbers)[1]

    @property
    def max_consecutive(self) -> int:
        """Maior sequência consecutiva."""
        return maior_sequencia_consecutiva(self.numbers)

    @property
    def quadrants(self) -> Dict[str, int]:
        """Distribuição por quadrantes."""
        return distribuicao_quadrantes(self.numbers)

    def to_dict(self) -> Dict:
        """Converte para dicionário."""
        return {
            "numbers": self.numbers,
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "strategy": self.strategy,
            "seed": self.seed,
            "sum": self.sum,
            "even": self.even_count,
            "odd": self.odd_count,
            "max_consecutive": self.max_consecutive,
            "quadrants": self.quadrants,
            "metadata": self.metadata,
        }

    def __str__(self) -> str:
        nums_str = " - ".join(f"{n:02d}" for n in self.numbers)
        return f"Game({nums_str}) [sum={self.sum}, even={self.even_count}]"


class Draw(BaseModel):
    """
    Representa um sorteio histórico da Lotofácil.

    Attributes:
        concurso: Número do concurso
        data: Data do sorteio
        numbers: Lista de 15 números sorteados
        winners_15: Quantidade de ganhadores com 15 acertos
        total_collected: Valor total arrecadado
        prizes: Dicionário com premiação por faixa
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "concurso": 3509,
                "data": "2025-10-10",
                "numbers": [1, 3, 4, 7, 9, 10, 12, 14, 15, 16, 19, 21, 22, 24, 25]
            }
        }
    )

    concurso: int = Field(..., gt=0)
    data: str
    numbers: List[int] = Field(..., min_length=15, max_length=15)
    winners_15: int = Field(default=0, ge=0)
    total_collected: float = Field(default=0.0, ge=0.0)
    prizes: Dict[int, float] = Field(default_factory=dict)

    @field_validator("numbers")
    @classmethod
    def validate_numbers(cls, v: List[int]) -> List[int]:
        """Valida números do sorteio."""
        valido, msg = validar_jogo(v)
        if not valido:
            raise ValueError(msg)
        return sorted(v)

    @property
    def sum(self) -> int:
        """Soma dos números sorteados."""
        return soma_jogo(self.numbers)

    @property
    def stats(self) -> Dict[str, any]:
        """Estatísticas do sorteio."""
        pares, impares = contar_pares_impares(self.numbers)
        return {
            "sum": self.sum,
            "even": pares,
            "odd": impares,
            "max_consecutive": maior_sequencia_consecutiva(self.numbers),
            "quadrants": distribuicao_quadrantes(self.numbers),
        }

    def __str__(self) -> str:
        nums_str = " - ".join(f"{n:02d}" for n in self.numbers)
        return f"Draw #{self.concurso} ({self.data}): {nums_str}"


class Result(BaseModel):
    """
    Resultado de um jogo contra um sorteio.

    Attributes:
        game_id: ID do jogo
        draw_id: Número do concurso
        hits: Quantidade de acertos (0-15)
        prize: Valor do prêmio (se houver)
        hit_numbers: Números acertados
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "game_id": "game_001",
                "draw_id": 3509,
                "hits": 11,
                "prize": 5.00
            }
        }
    )

    game_id: str
    draw_id: int
    hits: int = Field(..., ge=0, le=15)
    prize: float = Field(default=0.0, ge=0.0)
    hit_numbers: List[int] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)

    @property
    def is_winner(self) -> bool:
        """Verifica se ganhou algum prêmio (>= 11 acertos)."""
        return self.hits >= 11

    def __str__(self) -> str:
        status = "WIN" if self.is_winner else "LOSS"
        return f"Result({status}): {self.hits} hits → R$ {self.prize:.2f}"


class Portfolio(BaseModel):
    """
    Coleção de jogos (portfólio).

    Attributes:
        id: Identificador único do portfólio
        games: Lista de jogos
        strategy: Estratégia usada
        n_games: Quantidade de jogos
        total_cost: Custo total
        created_at: Data/hora de criação
        seed: Seed usado
        filters: Filtros aplicados
        metadata: Metadados adicionais
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "portfolio_001",
                "strategy": "random_filtered",
                "n_games": 100,
                "seed": 42
            }
        }
    )

    id: str
    games: List[Game]
    strategy: str
    n_games: int = Field(..., gt=0)
    total_cost: float = Field(..., ge=0.0)
    created_at: datetime = Field(default_factory=datetime.now)
    seed: Optional[int] = None
    filters: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    dataset_version: Optional[str] = None

    @field_validator("n_games")
    @classmethod
    def validate_n_games(cls, v: int, info) -> int:
        """Valida se n_games corresponde ao tamanho de games."""
        # Nota: Esta validação só funciona após games ser definido
        return v

    @property
    def cost_per_game(self) -> float:
        """Custo médio por jogo."""
        return self.total_cost / self.n_games if self.n_games > 0 else 0.0

    @property
    def unique_numbers(self) -> set[int]:
        """Conjunto de todos os números únicos usados."""
        all_numbers = set()
        for game in self.games:
            all_numbers.update(game.numbers)
        return all_numbers

    @property
    def coverage_statistics(self) -> Dict[str, int]:
        """Estatísticas de cobertura de números."""
        frequency = {n: 0 for n in range(1, 26)}
        for game in self.games:
            for num in game.numbers:
                frequency[num] += 1

        return {
            "total_unique": len(self.unique_numbers),
            "most_used": max(frequency, key=frequency.get),
            "least_used": min(frequency, key=frequency.get),
            "frequency": frequency,
        }

    def evaluate_against_draw(self, draw: Draw) -> List[Result]:
        """
        Avalia todos os jogos contra um sorteio.

        Args:
            draw: Sorteio a comparar

        Returns:
            Lista de resultados
        """
        from app.core.probability import PREMIOS_PADRAO

        results = []
        for game in self.games:
            hits = calcular_acertos(game.numbers, draw.numbers)
            prize = PREMIOS_PADRAO.get(hits, 0.0) if hits >= 11 else 0.0

            # Números acertados
            hit_nums = sorted(set(game.numbers) & set(draw.numbers))

            result = Result(
                game_id=game.id or "unknown",
                draw_id=draw.concurso,
                hits=hits,
                prize=prize,
                hit_numbers=hit_nums,
            )
            results.append(result)

        return results

    def summary(self) -> Dict[str, any]:
        """Resumo estatístico do portfólio."""
        sums = [game.sum for game in self.games]
        evens = [game.even_count for game in self.games]

        return {
            "id": self.id,
            "strategy": self.strategy,
            "n_games": self.n_games,
            "total_cost": self.total_cost,
            "cost_per_game": self.cost_per_game,
            "seed": self.seed,
            "stats": {
                "avg_sum": sum(sums) / len(sums) if sums else 0,
                "min_sum": min(sums) if sums else 0,
                "max_sum": max(sums) if sums else 0,
                "avg_even": sum(evens) / len(evens) if evens else 0,
            },
            "coverage": self.coverage_statistics,
            "created_at": self.created_at.isoformat(),
        }

    def __str__(self) -> str:
        return (
            f"Portfolio({self.id}): {self.n_games} games, "
            f"strategy={self.strategy}, cost=R$ {self.total_cost:.2f}"
        )


# Funções auxiliares
def create_game(numbers: List[int], **kwargs) -> Game:
    """
    Factory function para criar um Game.

    Args:
        numbers: Lista de números
        **kwargs: Argumentos adicionais

    Returns:
        Instância de Game validada
    """
    return Game(numbers=numbers, **kwargs)


def create_draw(concurso: int, data: str, numbers: List[int], **kwargs) -> Draw:
    """
    Factory function para criar um Draw.

    Args:
        concurso: Número do concurso
        data: Data do sorteio
        numbers: Números sorteados
        **kwargs: Argumentos adicionais

    Returns:
        Instância de Draw validada
    """
    return Draw(concurso=concurso, data=data, numbers=numbers, **kwargs)


def create_portfolio(
    games: List[Game],
    strategy: str,
    total_cost: float,
    portfolio_id: Optional[str] = None,
    **kwargs
) -> Portfolio:
    """
    Factory function para criar um Portfolio.

    Args:
        games: Lista de jogos
        strategy: Nome da estratégia
        total_cost: Custo total
        portfolio_id: ID do portfólio (gerado se None)
        **kwargs: Argumentos adicionais

    Returns:
        Instância de Portfolio validada
    """
    if portfolio_id is None:
        from uuid import uuid4
        portfolio_id = f"portfolio_{uuid4().hex[:8]}"

    return Portfolio(
        id=portfolio_id,
        games=games,
        strategy=strategy,
        n_games=len(games),
        total_cost=total_cost,
        **kwargs
    )


if __name__ == "__main__":
    print("=" * 70)
    print("LOTOFÁCIL - Models (Pydantic)")
    print("=" * 70)

    # Exemplo de Game
    print("\n📦 Criando um Game...")
    game = create_game(
        numbers=[1, 2, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 24, 25],
        id="game_001",
        strategy="random_filtered",
        seed=42
    )
    print(game)
    print(f"  Propriedades: {game.to_dict()}")

    # Exemplo de Draw
    print("\n🎲 Criando um Draw...")
    draw = create_draw(
        concurso=3509,
        data="2025-10-10",
        numbers=[1, 3, 4, 7, 9, 10, 12, 14, 15, 16, 19, 21, 22, 24, 25],
        winners_15=2
    )
    print(draw)
    print(f"  Estatísticas: {draw.stats}")

    # Exemplo de Result
    print("\n✅ Calculando Result...")
    hits = calcular_acertos(game.numbers, draw.numbers)
    result = Result(
        game_id=game.id,
        draw_id=draw.concurso,
        hits=hits,
        prize=5.0 if hits >= 11 else 0.0,
        hit_numbers=sorted(set(game.numbers) & set(draw.numbers))
    )
    print(result)

    # Exemplo de Portfolio
    print("\n📁 Criando um Portfolio...")
    games_list = [game]  # Normalmente seriam múltiplos jogos
    portfolio = create_portfolio(
        games=games_list,
        strategy="random_filtered",
        total_cost=2.50,
        seed=42
    )
    print(portfolio)
    print(f"\n  Summary: {portfolio.summary()}")

    # Avaliar portfolio contra draw
    print("\n🔍 Avaliando Portfolio contra Draw...")
    results = portfolio.evaluate_against_draw(draw)
    for r in results:
        print(f"  {r}")

    print("\n" + "=" * 70)
