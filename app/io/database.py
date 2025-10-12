"""
Models SQLAlchemy para persistência de dados.

Define estrutura do banco de dados:
- draws: Sorteios históricos
- draw_stats: Estatísticas calculadas dos sorteios
- runs: Execuções (generate, backtest, simulate)
- portfolios: Carteiras de jogos
- games: Jogos individuais
- results: Resultados de backtesting
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship, sessionmaker, Session, declarative_base
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.types import TypeDecorator, JSON
import json
import enum

Base = declarative_base()


# ============================================================================
# CUSTOM TYPES
# ============================================================================

class JSONType(TypeDecorator):
    """JSON type que funciona tanto em SQLite quanto PostgreSQL."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class IntArrayType(TypeDecorator):
    """Array de inteiros que funciona em SQLite e PostgreSQL."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if dialect.name == 'postgresql':
                return value  # PostgreSQL tem ARRAY nativo
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            if dialect.name == 'postgresql':
                return value
            value = json.loads(value)
        return value


# ============================================================================
# ENUMS
# ============================================================================

class RunKind(enum.Enum):
    """Tipo de execução."""
    GENERATE = "generate"
    BACKTEST = "backtest"
    SIMULATE = "simulate"


# ============================================================================
# MODELS
# ============================================================================

class Draw(Base):
    """
    Sorteio histórico da Lotofácil.

    Armazena resultado oficial de um concurso.
    """
    __tablename__ = "draws"

    id = Column(Integer, primary_key=True, autoincrement=True)
    concurso = Column(Integer, unique=True, nullable=False, index=True)
    data = Column(String(10), nullable=False)  # DD/MM/YYYY
    nums_15 = Column(IntArrayType, nullable=False)  # Array de 15 números
    valor_arrecadado = Column(Float, default=0.0)
    ganhadores_15 = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    # Relacionamentos
    stats = relationship("DrawStats", back_populates="draw", uselist=False)
    results = relationship("Result", back_populates="draw")

    def __repr__(self):
        return f"<Draw(concurso={self.concurso}, data={self.data})>"


class DrawStats(Base):
    """
    Estatísticas calculadas de um sorteio.

    Armazena análises automáticas do sorteio.
    """
    __tablename__ = "draw_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    concurso = Column(Integer, ForeignKey("draws.concurso"), unique=True, nullable=False)

    # Estatísticas básicas
    soma = Column(Integer, nullable=False)
    pares = Column(Integer, nullable=False)
    impares = Column(Integer, nullable=False)
    max_consecutivos = Column(Integer, default=0)

    # Quadrantes
    q1 = Column(Integer, default=0)  # 1-6
    q2 = Column(Integer, default=0)  # 7-12
    q3 = Column(Integer, default=0)  # 13-18
    q4 = Column(Integer, default=0)  # 19-25

    # Repetições
    repetidos_anterior = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.now, nullable=False)

    # Relacionamento
    draw = relationship("Draw", back_populates="stats")

    def __repr__(self):
        return f"<DrawStats(concurso={self.concurso}, soma={self.soma})>"


class Run(Base):
    """
    Execução (generate, backtest, simulate).

    Registra cada execução do sistema com seus parâmetros.
    """
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    kind = Column(SQLEnum(RunKind), nullable=False, index=True)
    params = Column(JSONType, nullable=False)  # Parâmetros da execução
    dataset_version = Column(String(50), nullable=True)
    seed = Column(Integer, nullable=True)
    git_commit = Column(String(40), nullable=True)  # Hash do commit
    status = Column(String(20), default="running", nullable=False)  # running, completed, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)

    # Relacionamentos
    portfolios = relationship("Portfolio", back_populates="run")
    results = relationship("Result", back_populates="run")

    def __repr__(self):
        return f"<Run(id={self.id}, kind={self.kind.value}, status={self.status})>"


class Portfolio(Base):
    """
    Carteira de jogos gerada.

    Agrupa múltiplos jogos de uma mesma execução.
    """
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=False, index=True)
    portfolio_id = Column(String(50), unique=True, nullable=False)  # UUID ou identificador
    strategy = Column(String(50), nullable=False, index=True)
    n_games = Column(Integer, nullable=False)
    total_cost = Column(Float, nullable=False)
    filters = Column(JSONType, nullable=True)  # Filtros aplicados
    extra_metadata = Column(JSONType, nullable=True)  # Metadados adicionais
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    # Relacionamentos
    run = relationship("Run", back_populates="portfolios")
    games = relationship("Game", back_populates="portfolio")

    def __repr__(self):
        return f"<Portfolio(id={self.portfolio_id}, strategy={self.strategy}, n_games={self.n_games})>"


class Game(Base):
    """
    Jogo individual dentro de um portfolio.

    Armazena os 15 números do jogo.
    """
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    game_id = Column(String(50), nullable=False, index=True)  # ID único do jogo
    nums_15 = Column(IntArrayType, nullable=False)  # Array de 15 números

    # Estatísticas do jogo
    soma = Column(Integer, nullable=False)
    pares = Column(Integer, nullable=False)
    impares = Column(Integer, nullable=False)
    max_consecutivos = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.now, nullable=False)

    # Relacionamento
    portfolio = relationship("Portfolio", back_populates="games")

    def __repr__(self):
        return f"<Game(id={self.game_id}, nums={self.nums_15})>"


class Result(Base):
    """
    Resultado de backtesting.

    Armazena resultado de um jogo vs um sorteio.
    """
    __tablename__ = "results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=False, index=True)
    game_id = Column(String(50), nullable=False, index=True)
    concurso = Column(Integer, ForeignKey("draws.concurso"), nullable=False, index=True)

    # Resultado
    acertos = Column(Integer, nullable=False)
    premio = Column(Float, default=0.0)
    custo = Column(Float, nullable=False)
    lucro = Column(Float, nullable=False)  # premio - custo

    created_at = Column(DateTime, default=datetime.now, nullable=False)

    # Relacionamentos
    run = relationship("Run", back_populates="results")
    draw = relationship("Draw", back_populates="results")

    def __repr__(self):
        return f"<Result(game={self.game_id}, concurso={self.concurso}, acertos={self.acertos})>"


# ============================================================================
# DATABASE ENGINE & SESSION
# ============================================================================

class Database:
    """
    Gerenciador de conexão com banco de dados.

    Facilita criação de sessões e gestão do engine.
    """

    def __init__(self, database_url: str = "sqlite:///lotofacil.db"):
        """
        Inicializa conexão com banco.

        Args:
            database_url: URL de conexão (padrão: SQLite local)
        """
        self.database_url = database_url
        self.engine = create_engine(
            database_url,
            echo=False,  # Set True para debug SQL
            pool_pre_ping=True,  # Verificar conexões
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

    def create_tables(self) -> None:
        """Cria todas as tabelas no banco."""
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self) -> None:
        """Remove todas as tabelas (CUIDADO!)."""
        Base.metadata.drop_all(bind=self.engine)

    def get_session(self) -> Session:
        """
        Retorna uma nova sessão.

        Usage:
            db = Database()
            session = db.get_session()
            try:
                # Usar session
                session.commit()
            except:
                session.rollback()
            finally:
                session.close()
        """
        return self.SessionLocal()

    def get_or_create_draw(self, session: Session, concurso: int, **kwargs) -> Draw:
        """
        Obtém ou cria um sorteio.

        Args:
            session: Sessão ativa
            concurso: Número do concurso
            **kwargs: Outros campos do Draw

        Returns:
            Instância de Draw
        """
        draw = session.query(Draw).filter_by(concurso=concurso).first()
        if not draw:
            draw = Draw(concurso=concurso, **kwargs)
            session.add(draw)
            session.commit()
        return draw


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def init_database(database_url: str = "sqlite:///lotofacil.db") -> Database:
    """
    Inicializa banco de dados.

    Args:
        database_url: URL de conexão

    Returns:
        Instância de Database

    Examples:
        >>> db = init_database()
        >>> db.create_tables()
    """
    db = Database(database_url)
    db.create_tables()
    return db


def get_database(database_url: Optional[str] = None) -> Database:
    """
    Factory function para obter Database.

    Args:
        database_url: URL opcional (usa padrão se None)

    Returns:
        Instância de Database
    """
    if database_url is None:
        database_url = "sqlite:///lotofacil.db"
    return Database(database_url)


if __name__ == "__main__":
    print("=" * 70)
    print("DATABASE - Models SQLAlchemy")
    print("=" * 70)

    # Criar banco
    print("\n📦 Criando banco de dados...")
    db = init_database("sqlite:///test_lotofacil.db")
    print("✓ Tabelas criadas!")

    # Criar sessão
    session = db.get_session()

    try:
        # Criar um sorteio de exemplo
        print("\n🎲 Criando sorteio exemplo...")
        draw = Draw(
            concurso=3509,
            data="10/10/2025",
            nums_15=[1, 3, 4, 7, 9, 10, 12, 14, 15, 16, 19, 21, 22, 24, 25],
            valor_arrecadado=10000000.0,
            ganhadores_15=2
        )
        session.add(draw)

        # Criar estatísticas
        print("📊 Criando estatísticas...")
        stats = DrawStats(
            concurso=3509,
            soma=202,
            pares=7,
            impares=8,
            max_consecutivos=2,
            q1=2, q2=3, q3=4, q4=6
        )
        session.add(stats)

        # Criar Run
        print("🔄 Criando execução...")
        run = Run(
            kind=RunKind.GENERATE,
            params={"strategy": "random", "n_games": 10},
            dataset_version="v1.0",
            seed=42,
            status="completed"
        )
        session.add(run)
        session.commit()

        print(f"✓ Run criado: {run}")

        # Criar Portfolio
        print("📁 Criando portfolio...")
        portfolio = Portfolio(
            run_id=run.id,
            portfolio_id="portfolio_test_001",
            strategy="random",
            n_games=2,
            total_cost=5.0,
            filters={"sum_range": {"min": 170, "max": 200}}
        )
        session.add(portfolio)
        session.commit()

        # Criar Games
        print("🎮 Criando jogos...")
        for i in range(2):
            game = Game(
                portfolio_id=portfolio.id,
                game_id=f"game_{i+1}",
                nums_15=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15+i],
                soma=120+i,
                pares=7,
                impares=8,
                max_consecutivos=15
            )
            session.add(game)

        session.commit()
        print("✓ Jogos criados!")

        # Consultar
        print("\n🔍 Consultando dados...")
        draws = session.query(Draw).all()
        print(f"  Sorteios: {len(draws)}")

        runs = session.query(Run).all()
        print(f"  Execuções: {len(runs)}")

        portfolios = session.query(Portfolio).all()
        print(f"  Portfolios: {len(portfolios)}")

        games = session.query(Game).all()
        print(f"  Jogos: {len(games)}")

        print("\n✅ Teste completo!")

    except Exception as e:
        session.rollback()
        print(f"\n❌ Erro: {e}")
        raise
    finally:
        session.close()

    print("\n" + "=" * 70)
