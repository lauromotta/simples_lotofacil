"""
API REST - Lotofácil Pro

Sistema profissional de análise probabilística da Lotofácil.
Expõe todas as funcionalidades via HTTP REST API.

Endpoints:
- POST /generate/pure - Gera jogos aleatórios puros
- POST /generate/filtered - Gera jogos com filtros
- POST /generate/wheeling - Gera jogos com wheeling
- POST /generate/hybrid - Gera jogos híbridos
- POST /simulate - Executa simulação Monte Carlo
- POST /backtest - Executa backtest histórico
- GET /stats - Retorna estatísticas históricas
- POST /etl/import - Importa dados da API
- GET /health - Health check

Tecnologias:
- FastAPI 0.104+
- Pydantic 2.x para validação
- Uvicorn como servidor ASGI
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import uvicorn

from app.core.game import Game
from app.strategies import (
    RandomPureStrategy,
    RandomFilteredStrategy,
    WheelingStrategy,
    HybridStrategy,
    StrategyConfig,
    StrategyAllocation,
)
from app.filters import FilterChain, SumRangeFilter, EvenOddFilter
from app.monte_carlo import MonteCarloSimulator
from app.backtest import Backtester
from app.io.database import get_database, Draw, init_database
from app.io.etl import import_historical_data


# ============================================================================
# PYDANTIC MODELS (Request/Response)
# ============================================================================

class GeneratePureRequest(BaseModel):
    """Request para geração aleatória pura."""
    n_games: int = Field(10, ge=1, le=1000, description="Quantidade de jogos")
    seed: Optional[int] = Field(None, description="Seed para reprodutibilidade")

    class Config:
        json_schema_extra = {
            "example": {
                "n_games": 10,
                "seed": 42
            }
        }


class GenerateFilteredRequest(BaseModel):
    """Request para geração com filtros."""
    n_games: int = Field(10, ge=1, le=1000, description="Quantidade de jogos")
    seed: Optional[int] = Field(None, description="Seed")
    sum_min: int = Field(180, ge=120, le=240, description="Soma mínima")
    sum_max: int = Field(210, ge=120, le=300, description="Soma máxima")
    even_min: int = Field(6, ge=0, le=15, description="Pares mínimos")
    even_max: int = Field(9, ge=0, le=15, description="Pares máximos")
    max_attempts: int = Field(10000, ge=100, le=100000, description="Tentativas max")

    class Config:
        json_schema_extra = {
            "example": {
                "n_games": 10,
                "sum_min": 180,
                "sum_max": 210,
                "even_min": 6,
                "even_max": 9
            }
        }


class GenerateWheelingRequest(BaseModel):
    """Request para wheeling."""
    wheel_size: int = Field(18, ge=15, le=25, description="Tamanho do wheeling")
    n_games: int = Field(50, ge=1, le=1000, description="Quantidade de jogos")
    seed: Optional[int] = Field(None, description="Seed")

    class Config:
        json_schema_extra = {
            "example": {
                "wheel_size": 18,
                "n_games": 50,
                "seed": 42
            }
        }


class GenerateHybridRequest(BaseModel):
    """Request para estratégia híbrida."""
    n_games: int = Field(20, ge=1, le=1000, description="Quantidade de jogos")
    seed: Optional[int] = Field(None, description="Seed")
    pure_percentage: float = Field(0.5, ge=0.0, le=1.0, description="% Pure (0.0-1.0)")
    filtered_percentage: float = Field(0.5, ge=0.0, le=1.0, description="% Filtered (0.0-1.0)")

    @validator('filtered_percentage')
    def percentages_must_sum_to_one(cls, v, values):
        if 'pure_percentage' in values:
            total = values['pure_percentage'] + v
            if abs(total - 1.0) > 0.01:
                raise ValueError(f'Percentages must sum to 1.0 (got {total})')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "n_games": 20,
                "pure_percentage": 0.5,
                "filtered_percentage": 0.5
            }
        }


class SimulateRequest(BaseModel):
    """Request para simulação Monte Carlo."""
    n_games: int = Field(10, ge=1, le=100, description="Quantidade de jogos")
    n_simulations: int = Field(10000, ge=100, le=100000, description="Quantidade de simulações")
    seed: Optional[int] = Field(None, description="Seed")

    class Config:
        json_schema_extra = {
            "example": {
                "n_games": 10,
                "n_simulations": 10000,
                "seed": 42
            }
        }


class BacktestRequest(BaseModel):
    """Request para backtest histórico."""
    n_games: int = Field(10, ge=1, le=100, description="Quantidade de jogos")
    days: int = Field(30, ge=1, le=365, description="Dias de histórico")
    seed: Optional[int] = Field(None, description="Seed")

    class Config:
        json_schema_extra = {
            "example": {
                "n_games": 10,
                "days": 30,
                "seed": 42
            }
        }


class GameResponse(BaseModel):
    """Response com um jogo."""
    numbers: List[int] = Field(..., description="15 números do jogo")
    sum: int = Field(..., description="Soma dos números")
    even_count: int = Field(..., description="Quantidade de pares")
    strategy: str = Field(..., description="Estratégia usada")

    class Config:
        json_schema_extra = {
            "example": {
                "numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
                "sum": 120,
                "even_count": 7,
                "strategy": "random_pure"
            }
        }


class GenerateResponse(BaseModel):
    """Response de geração de jogos."""
    success: bool = True
    n_games: int
    total_cost: float
    execution_time: float
    games: List[GameResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "n_games": 10,
                "total_cost": 30.0,
                "execution_time": 0.005,
                "games": []
            }
        }


class SimulateResponse(BaseModel):
    """Response de simulação Monte Carlo."""
    success: bool = True
    n_simulations: int
    n_games: int
    total_cost: float
    expected_profit: float
    expected_roi: float
    probability_profit: float
    probability_loss: float
    var_95: float
    percentiles: Dict[str, float]

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "n_simulations": 10000,
                "n_games": 10,
                "total_cost": 30.0,
                "expected_profit": -23.0,
                "expected_roi": -76.7,
                "probability_profit": 0.5,
                "probability_loss": 98.9,
                "var_95": -30.0,
                "percentiles": {"p5": -30.0, "p50": -25.0, "p95": -10.0}
            }
        }


class BacktestResponse(BaseModel):
    """Response de backtest."""
    success: bool = True
    n_games: int
    n_concursos: int
    total_cost: float
    total_prize: float
    total_profit: float
    roi: float
    win_rate: float

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "n_games": 10,
                "n_concursos": 30,
                "total_cost": 30.0,
                "total_prize": 135.0,
                "total_profit": 105.0,
                "roi": 350.0,
                "win_rate": 9.67
            }
        }


class StatsResponse(BaseModel):
    """Response de estatísticas."""
    success: bool = True
    total_draws: int
    first_draw: str
    last_draw: str
    avg_sum: float
    avg_even: float

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "total_draws": 3509,
                "first_draw": "2003-09-29",
                "last_draw": "2025-10-10",
                "avg_sum": 195.18,
                "avg_even": 7.20
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    version: str = "2.0"
    timestamp: datetime


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Lotofácil Pro API",
    description="Sistema profissional de análise probabilística da Lotofácil",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware (permitir acesso de qualquer origem)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        version="2.0",
        timestamp=datetime.now()
    )


@app.get("/", tags=["System"])
async def root():
    """Root endpoint com informações da API."""
    return {
        "name": "Lotofácil Pro API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
        "warning": "⚠️ Expected Value = -53% ROI (casa sempre ganha!)"
    }


# ============================================================================
# GENERATE ENDPOINTS
# ============================================================================

@app.post("/generate/pure", response_model=GenerateResponse, tags=["Generate"])
async def generate_pure(request: GeneratePureRequest):
    """
    Gera jogos usando estratégia aleatória pura.

    - **n_games**: Quantidade de jogos (1-1000)
    - **seed**: Seed para reprodutibilidade (opcional)

    Retorna lista de jogos com números, soma, pares e custo total.
    """
    try:
        strategy = RandomPureStrategy()
        config = StrategyConfig(n_games=request.n_games, seed=request.seed)
        result = strategy.generate(config)

        games = [
            GameResponse(
                numbers=game.numbers,
                sum=game.sum,
                even_count=sum(1 for n in game.numbers if n % 2 == 0),
                strategy=game.strategy
            )
            for game in result.games
        ]

        return GenerateResponse(
            success=True,
            n_games=result.n_games,
            total_cost=result.total_cost,
            execution_time=result.execution_time,
            games=games
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate/filtered", response_model=GenerateResponse, tags=["Generate"])
async def generate_filtered(request: GenerateFilteredRequest):
    """
    Gera jogos usando filtros de validação.

    - **n_games**: Quantidade de jogos
    - **sum_min/sum_max**: Filtro de soma (120-300)
    - **even_min/even_max**: Filtro de pares (0-15)
    - **max_attempts**: Tentativas máximas por jogo

    Retorna jogos que passam em todos os filtros.
    """
    try:
        filters = FilterChain([
            SumRangeFilter(min_sum=request.sum_min, max_sum=request.sum_max),
            EvenOddFilter(min_even=request.even_min, max_even=request.even_max),
        ])

        strategy = RandomFilteredStrategy()
        config = StrategyConfig(
            n_games=request.n_games,
            seed=request.seed,
            filters=filters,
            max_attempts=request.max_attempts
        )
        result = strategy.generate(config)

        games = [
            GameResponse(
                numbers=game.numbers,
                sum=game.sum,
                even_count=sum(1 for n in game.numbers if n % 2 == 0),
                strategy=game.strategy
            )
            for game in result.games
        ]

        return GenerateResponse(
            success=True,
            n_games=result.n_games,
            total_cost=result.total_cost,
            execution_time=result.execution_time,
            games=games
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate/wheeling", response_model=GenerateResponse, tags=["Generate"])
async def generate_wheeling(request: GenerateWheelingRequest):
    """
    Gera jogos usando sistema de wheeling.

    - **wheel_size**: Tamanho do wheeling (15-25 números)
    - **n_games**: Quantidade de jogos a gerar
    - **seed**: Seed para reprodutibilidade

    Seleciona wheel_size números e gera combinações sistemáticas.
    """
    try:
        strategy = WheelingStrategy(wheel_size=request.wheel_size)
        config = StrategyConfig(n_games=request.n_games, seed=request.seed)
        result = strategy.generate(config)

        games = [
            GameResponse(
                numbers=game.numbers,
                sum=game.sum,
                even_count=sum(1 for n in game.numbers if n % 2 == 0),
                strategy=game.strategy
            )
            for game in result.games
        ]

        return GenerateResponse(
            success=True,
            n_games=result.n_games,
            total_cost=result.total_cost,
            execution_time=result.execution_time,
            games=games
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate/hybrid", response_model=GenerateResponse, tags=["Generate"])
async def generate_hybrid(request: GenerateHybridRequest):
    """
    Gera jogos usando estratégia híbrida (mix de Pure + Filtered).

    - **n_games**: Quantidade total de jogos
    - **pure_percentage**: % de jogos Pure (0.0-1.0)
    - **filtered_percentage**: % de jogos Filtered (0.0-1.0)

    As percentagens devem somar 1.0.
    """
    try:
        filters = FilterChain([
            SumRangeFilter(min_sum=180, max_sum=210),
            EvenOddFilter(min_even=6, max_even=9),
        ])

        allocations = [
            StrategyAllocation(
                strategy=RandomPureStrategy(),
                percentage=request.pure_percentage,
            ),
            StrategyAllocation(
                strategy=RandomFilteredStrategy(),
                percentage=request.filtered_percentage,
                config_override={"filters": filters, "max_attempts": 10000}
            ),
        ]

        strategy = HybridStrategy(allocations=allocations)
        config = StrategyConfig(n_games=request.n_games, seed=request.seed)
        result = strategy.generate(config)

        games = [
            GameResponse(
                numbers=game.numbers,
                sum=game.sum,
                even_count=sum(1 for n in game.numbers if n % 2 == 0),
                strategy=game.strategy
            )
            for game in result.games
        ]

        return GenerateResponse(
            success=True,
            n_games=result.n_games,
            total_cost=result.total_cost,
            execution_time=result.execution_time,
            games=games
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SIMULATE ENDPOINT
# ============================================================================

@app.post("/simulate", response_model=SimulateResponse, tags=["Analysis"])
async def simulate(request: SimulateRequest):
    """
    Executa simulação Monte Carlo.

    - **n_games**: Quantidade de jogos a testar
    - **n_simulations**: Quantidade de simulações (sorteios aleatórios)
    - **seed**: Seed para reprodutibilidade

    Retorna estatísticas completas: ROI, probabilidades, percentis, VaR.
    """
    try:
        # Gerar jogos
        strategy = RandomPureStrategy()
        config = StrategyConfig(n_games=request.n_games, seed=request.seed)
        result = strategy.generate(config)

        # Simular
        simulator = MonteCarloSimulator()
        sim_result = simulator.run(
            games=result.games,
            n_simulations=request.n_simulations,
            seed=request.seed
        )

        return SimulateResponse(
            success=True,
            n_simulations=sim_result.n_simulations,
            n_games=sim_result.n_games,
            total_cost=sim_result.total_cost,
            expected_profit=sim_result.expected_profit,
            expected_roi=sim_result.expected_roi,
            probability_profit=sim_result.probability_profit,
            probability_loss=100 - sim_result.probability_profit - sim_result.probability_breakeven,
            var_95=sim_result.var_95,
            percentiles=sim_result.percentiles
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BACKTEST ENDPOINT
# ============================================================================

@app.post("/backtest", response_model=BacktestResponse, tags=["Analysis"])
async def backtest(request: BacktestRequest):
    """
    Executa backtest contra dados históricos.

    - **n_games**: Quantidade de jogos a testar
    - **days**: Dias de histórico para testar
    - **seed**: Seed para reprodutibilidade

    Retorna resultados reais: ROI, prêmios, win rate contra sorteios passados.
    """
    try:
        # Buscar sorteios históricos
        db = get_database()
        session = db.get_session()

        draws = session.query(Draw).order_by(Draw.concurso.desc()).limit(request.days).all()
        session.close()

        if not draws:
            raise HTTPException(status_code=404, detail="Nenhum sorteio encontrado. Execute 'etl import' primeiro.")

        # Gerar jogos
        strategy = RandomPureStrategy()
        config = StrategyConfig(n_games=request.n_games, seed=request.seed)
        result = strategy.generate(config)

        # Backtest
        backtester = Backtester()
        bt_result = backtester.run(games=result.games, draws=draws)

        return BacktestResponse(
            success=True,
            n_games=bt_result.n_games,
            n_concursos=len(draws),
            total_cost=bt_result.total_custo,
            total_prize=bt_result.total_premio,
            total_profit=bt_result.total_lucro,
            roi=bt_result.roi,
            win_rate=bt_result.win_rate
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STATS ENDPOINT
# ============================================================================

@app.get("/stats", response_model=StatsResponse, tags=["Data"])
async def get_stats():
    """
    Retorna estatísticas dos sorteios históricos.

    - Total de sorteios no banco
    - Período (primeiro e último sorteio)
    - Média de soma e pares
    """
    try:
        db = get_database()
        session = db.get_session()

        total = session.query(Draw).count()

        if total == 0:
            raise HTTPException(status_code=404, detail="Nenhum sorteio encontrado. Execute 'POST /etl/import' primeiro.")

        first_draw = session.query(Draw).order_by(Draw.concurso.asc()).first()
        last_draw = session.query(Draw).order_by(Draw.concurso.desc()).first()

        # Calcular médias
        all_draws = session.query(Draw).all()
        sums = [sum(d.nums_15) for d in all_draws]
        evens = [sum(1 for n in d.nums_15 if n % 2 == 0) for d in all_draws]

        session.close()

        return StatsResponse(
            success=True,
            total_draws=total,
            first_draw=first_draw.data,  # Already a string
            last_draw=last_draw.data,  # Already a string
            avg_sum=sum(sums) / len(sums),
            avg_even=sum(evens) / len(evens)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ETL ENDPOINT
# ============================================================================

@app.post("/etl/import", tags=["Data"])
async def etl_import(background_tasks: BackgroundTasks):
    """
    Importa dados históricos da API da Lotofácil.

    Executa em background e retorna imediatamente.
    Importa todos os sorteios desde 2003.
    """
    def run_import():
        try:
            import_historical_data(database_url="sqlite:///lotofacil.db", update_existing=False)
        except Exception as e:
            print(f"Erro na importação: {e}")

    background_tasks.add_task(run_import)

    return {
        "success": True,
        "message": "Importação iniciada em background. Use GET /stats para verificar."
    }


# ============================================================================
# MAIN (para rodar com python)
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
