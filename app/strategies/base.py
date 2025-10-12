"""
Classe base e interfaces para estratégias de geração de jogos.

Este módulo define a arquitetura para todas as estratégias de geração:
- BaseStrategy: Classe abstrata para estratégias
- StrategyConfig: Configuração de uma estratégia
- StrategyResult: Resultado da execução de uma estratégia

Todas as estratégias devem implementar o método generate() que
retorna um Portfolio completo com todos os jogos gerados.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from app.core.game import Game
from app.filters.base import FilterChain


# ============================================================================
# DATA CLASSES
# ============================================================================


@dataclass
class StrategyConfig:
    """
    Configuração de uma estratégia de geração.

    Attributes:
        n_games: Quantidade de jogos a gerar
        seed: Seed para reprodutibilidade (None = aleatório)
        filters: FilterChain para validação (None = sem filtros)
        max_attempts: Tentativas máximas por jogo (para estratégias filtradas)
        allow_duplicates: Permite jogos duplicados no portfolio
        metadata: Metadados adicionais
    """

    n_games: int
    seed: Optional[int] = None
    filters: Optional[FilterChain] = None
    max_attempts: int = 1000
    allow_duplicates: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validação pós-inicialização."""
        if self.n_games <= 0:
            raise ValueError("n_games deve ser maior que zero")
        if self.max_attempts <= 0:
            raise ValueError("max_attempts deve ser maior que zero")


@dataclass
class StrategyResult:
    """
    Resultado da execução de uma estratégia.

    Attributes:
        portfolio_id: ID único do portfolio gerado
        strategy_name: Nome da estratégia usada
        games: Lista de jogos gerados
        config: Configuração usada
        stats: Estatísticas da execução
        execution_time: Tempo de execução (segundos)
        success: Se a execução foi bem sucedida
        error_message: Mensagem de erro (se houver)
    """

    portfolio_id: str
    strategy_name: str
    games: List[Game]
    config: StrategyConfig
    stats: Dict[str, Any]
    execution_time: float
    success: bool = True
    error_message: Optional[str] = None

    @property
    def n_games(self) -> int:
        """Quantidade de jogos gerados."""
        return len(self.games)

    @property
    def total_cost(self) -> float:
        """Custo total do portfolio (R$ 3.00 por jogo)."""
        return len(self.games) * 3.0

    def to_dict(self) -> Dict[str, Any]:
        """Converte resultado para dicionário."""
        return {
            "portfolio_id": self.portfolio_id,
            "strategy_name": self.strategy_name,
            "n_games": self.n_games,
            "total_cost": self.total_cost,
            "config": {
                "n_games": self.config.n_games,
                "seed": self.config.seed,
                "has_filters": self.config.filters is not None,
                "max_attempts": self.config.max_attempts,
                "allow_duplicates": self.config.allow_duplicates,
            },
            "stats": self.stats,
            "execution_time": self.execution_time,
            "success": self.success,
            "error_message": self.error_message,
        }


# ============================================================================
# BASE STRATEGY
# ============================================================================


class BaseStrategy(ABC):
    """
    Classe base abstrata para todas as estratégias de geração.

    Todas as estratégias concretas devem herdar desta classe e
    implementar o método _generate_games().

    Attributes:
        name: Nome da estratégia
        description: Descrição da estratégia
    """

    def __init__(self, name: str, description: str):
        """
        Inicializa a estratégia.

        Args:
            name: Nome único da estratégia
            description: Descrição curta da estratégia
        """
        self.name = name
        self.description = description

    @abstractmethod
    def _generate_games(self, config: StrategyConfig) -> List[Game]:
        """
        Gera jogos de acordo com a estratégia (implementação concreta).

        Este método DEVE ser implementado pelas subclasses e é onde
        a lógica específica de cada estratégia é implementada.

        Args:
            config: Configuração da geração

        Returns:
            Lista de jogos gerados

        Raises:
            NotImplementedError: Se não for implementado pela subclasse
        """
        raise NotImplementedError("Subclasses devem implementar _generate_games()")

    def generate(self, config: StrategyConfig) -> StrategyResult:
        """
        Executa a estratégia e retorna resultado completo.

        Este método é o entry point público para todas as estratégias.
        Ele:
        1. Gera um portfolio_id único
        2. Chama _generate_games() (implementação concreta)
        3. Coleta estatísticas
        4. Retorna StrategyResult

        Args:
            config: Configuração da estratégia

        Returns:
            StrategyResult com todos os jogos e estatísticas
        """
        start_time = datetime.now()
        portfolio_id = self._generate_portfolio_id()

        try:
            # Chama implementação concreta
            games = self._generate_games(config)

            # Coleta estatísticas
            stats = self._collect_stats(games, config)

            # Calcula tempo de execução
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            return StrategyResult(
                portfolio_id=portfolio_id,
                strategy_name=self.name,
                games=games,
                config=config,
                stats=stats,
                execution_time=execution_time,
                success=True,
            )

        except Exception as e:
            # Em caso de erro, retorna resultado com falha
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            return StrategyResult(
                portfolio_id=portfolio_id,
                strategy_name=self.name,
                games=[],
                config=config,
                stats={},
                execution_time=execution_time,
                success=False,
                error_message=str(e),
            )

    def _generate_portfolio_id(self) -> str:
        """
        Gera ID único para o portfolio.

        Formato: {strategy_name}_{timestamp}_{uuid}

        Returns:
            Portfolio ID único
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        short_uuid = str(uuid.uuid4())[:8]
        return f"{self.name}_{timestamp}_{short_uuid}"

    def _collect_stats(
        self, games: List[Game], config: StrategyConfig
    ) -> Dict[str, Any]:
        """
        Coleta estatísticas dos jogos gerados.

        Args:
            games: Lista de jogos gerados
            config: Configuração usada

        Returns:
            Dicionário com estatísticas
        """
        if not games:
            return {
                "n_games": 0,
                "total_cost": 0.0,
                "requested_games": config.n_games,
                "success_rate": 0.0,
            }

        # Estatísticas básicas
        stats = {
            "n_games": len(games),
            "total_cost": len(games) * 3.0,
            "requested_games": config.n_games,
            "success_rate": len(games) / config.n_games if config.n_games > 0 else 0.0,
            "has_filters": config.filters is not None,
            "seed": config.seed,
        }

        # Estatísticas dos jogos
        somas = [game.sum for game in games]
        pares = [sum(1 for n in game.numbers if n % 2 == 0) for game in games]

        stats.update(
            {
                "sum_min": min(somas),
                "sum_max": max(somas),
                "sum_avg": sum(somas) / len(somas),
                "even_min": min(pares),
                "even_max": max(pares),
                "even_avg": sum(pares) / len(pares),
            }
        )

        # Estatísticas de filtros (se aplicável)
        if config.filters is not None:
            filter_stats = config.filters.get_all_stats()
            stats["filter_stats"] = {
                name: {
                    "evaluated": fs.total_evaluated,
                    "rejected": fs.total_rejected,
                    "rejection_rate": fs.rejection_rate,
                }
                for name, fs in filter_stats.items()
            }

        return stats

    def validate_config(self, config: StrategyConfig) -> tuple[bool, Optional[str]]:
        """
        Valida configuração antes de executar.

        Override este método se a estratégia tiver validações específicas.

        Args:
            config: Configuração a validar

        Returns:
            Tupla (válido, mensagem_erro)
        """
        if config.n_games <= 0:
            return False, "n_games deve ser maior que zero"

        if config.max_attempts <= 0:
            return False, "max_attempts deve ser maior que zero"

        return True, None

    def __repr__(self) -> str:
        """Representação string da estratégia."""
        return f"{self.__class__.__name__}(name='{self.name}')"


# ============================================================================
# SCRIPT DE DEMONSTRAÇÃO
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("BASE STRATEGY - Classes Abstratas")
    print("=" * 70)

    print("\n✅ Classes definidas:")
    print("   - StrategyConfig")
    print("   - StrategyResult")
    print("   - BaseStrategy (ABC)")

    print("\n📝 Estrutura da estratégia:")
    print("   1. Herdar de BaseStrategy")
    print("   2. Implementar _generate_games(config)")
    print("   3. Usar generate(config) como entry point")
    print("   4. Retorna StrategyResult automaticamente")

    print("\n🎯 Exemplo de uso:")
    print("""
    class MyStrategy(BaseStrategy):
        def __init__(self):
            super().__init__("my_strategy", "Minha estratégia")

        def _generate_games(self, config: StrategyConfig) -> List[Game]:
            # Implementação específica aqui
            games = []
            for i in range(config.n_games):
                # Gerar jogo...
                pass
            return games

    # Usar:
    strategy = MyStrategy()
    config = StrategyConfig(n_games=10, seed=42)
    result = strategy.generate(config)

    print(f"Gerados: {result.n_games} jogos")
    print(f"Custo: R$ {result.total_cost:.2f}")
    """)

    print("\n" + "=" * 70)
    print("✅ Estrutura base pronta para implementação")
    print("=" * 70)
