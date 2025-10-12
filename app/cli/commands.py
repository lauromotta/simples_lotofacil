"""
Comandos CLI para Lotofácil Pro.

Este módulo contém todos os comandos disponíveis na CLI.
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from typing import Optional
from pathlib import Path
import json

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

console = Console()

# ============================================================================
# GENERATE - Gerar Jogos
# ============================================================================

generate_app = typer.Typer()


@generate_app.command("pure")
def generate_pure(
    n_games: int = typer.Option(10, "--n-games", "-n", help="Quantidade de jogos"),
    seed: Optional[int] = typer.Option(None, "--seed", "-s", help="Seed para reprodutibilidade"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Arquivo de saída (.json)"),
):
    """Gera jogos com estratégia aleatória pura."""
    console.print(f"\n[bold cyan]Gerando {n_games} jogos (RandomPure)...[/bold cyan]")

    strategy = RandomPureStrategy()
    config = StrategyConfig(n_games=n_games, seed=seed)
    result = strategy.generate(config)

    # Mostrar resumo
    console.print(f"\n✅ [green]Gerados: {result.n_games} jogos[/green]")
    console.print(f"💰 Custo: R$ {result.total_cost:.2f}")
    console.print(f"⏱️  Tempo: {result.execution_time:.4f}s")

    # Mostrar primeiros jogos
    table = Table(title="Primeiros 5 Jogos")
    table.add_column("#", style="cyan")
    table.add_column("Números", style="white")
    table.add_column("Soma", style="yellow")

    for i, game in enumerate(result.games[:5]):
        table.add_row(str(i + 1), str(game.numbers), str(game.sum))

    console.print(table)

    # Salvar se solicitado
    if output:
        data = {
            "portfolio_id": result.portfolio_id,
            "strategy": result.strategy_name,
            "n_games": result.n_games,
            "games": [{"numbers": g.numbers, "sum": g.sum} for g in result.games],
        }
        output.write_text(json.dumps(data, indent=2))
        console.print(f"\n💾 Salvo em: {output}")


@generate_app.command("filtered")
def generate_filtered(
    n_games: int = typer.Option(10, "--n-games", "-n", help="Quantidade de jogos"),
    seed: Optional[int] = typer.Option(None, "--seed", "-s", help="Seed"),
    sum_min: int = typer.Option(180, "--sum-min", help="Soma mínima"),
    sum_max: int = typer.Option(210, "--sum-max", help="Soma máxima"),
    pares_min: int = typer.Option(6, "--pares-min", help="Pares mínimo"),
    pares_max: int = typer.Option(9, "--pares-max", help="Pares máximo"),
):
    """Gera jogos com filtros aplicados."""
    console.print(f"\n[bold cyan]Gerando {n_games} jogos (RandomFiltered)...[/bold cyan]")

    # Criar filtros
    filters = FilterChain([
        SumRangeFilter(min_sum=sum_min, max_sum=sum_max),
        EvenOddFilter(min_even=pares_min, max_even=pares_max),
    ])

    strategy = RandomFilteredStrategy()
    config = StrategyConfig(n_games=n_games, seed=seed, filters=filters, max_attempts=10000)
    result = strategy.generate(config)

    # Resumo
    console.print(f"\n✅ [green]Gerados: {result.n_games} jogos[/green]")
    console.print(f"💰 Custo: R$ {result.total_cost:.2f}")
    console.print(f"🎯 Filtros: Soma [{sum_min}-{sum_max}], Pares [{pares_min}-{pares_max}]")

    # Tabela
    table = Table(title="Primeiros 5 Jogos")
    table.add_column("#", style="cyan")
    table.add_column("Números", style="white")
    table.add_column("Soma", style="yellow")
    table.add_column("Pares", style="green")

    for i, game in enumerate(result.games[:5]):
        pares = sum(1 for n in game.numbers if n % 2 == 0)
        table.add_row(str(i + 1), str(game.numbers), str(game.sum), str(pares))

    console.print(table)


@generate_app.command("wheeling")
def generate_wheeling(
    wheel_size: int = typer.Option(18, "--wheel-size", "-w", help="Tamanho do wheeling (quantos números usar)"),
    n_games: int = typer.Option(50, "--n-games", "-n", help="Quantidade de jogos a gerar"),
    seed: Optional[int] = typer.Option(None, "--seed", "-s", help="Seed"),
):
    """Gera jogos usando wheeling system."""
    console.print(f"\n[bold cyan]Gerando jogos (Wheeling)...[/bold cyan]")

    if wheel_size < 15 or wheel_size > 25:
        console.print(f"[red]❌ Erro: wheel_size deve estar entre 15 e 25 (fornecido: {wheel_size})[/red]")
        return

    strategy = WheelingStrategy(wheel_size=wheel_size)
    config = StrategyConfig(n_games=n_games, seed=seed)
    result = strategy.generate(config)

    # Resumo
    console.print(f"\n✅ [green]Gerados: {result.n_games} jogos[/green]")
    console.print(f"💰 Custo: R$ {result.total_cost:.2f}")
    console.print(f"🎯 Wheeling: {wheel_size} números selecionados")
    console.print(f"⏱️  Tempo: {result.execution_time:.4f}s")

    # Tabela
    table = Table(title="Primeiros 5 Jogos")
    table.add_column("#", style="cyan")
    table.add_column("Números", style="white")
    table.add_column("Soma", style="yellow")

    for i, game in enumerate(result.games[:5]):
        table.add_row(str(i + 1), str(game.numbers), str(game.sum))

    console.print(table)


@generate_app.command("hybrid")
def generate_hybrid(
    n_games: int = typer.Option(20, "--n-games", "-n", help="Total de jogos"),
    seed: Optional[int] = typer.Option(None, "--seed", "-s", help="Seed"),
):
    """Gera jogos usando estratégia híbrida (50% Pure + 50% Filtered)."""
    console.print(f"\n[bold cyan]Gerando {n_games} jogos (Hybrid)...[/bold cyan]")

    # Criar alocações
    filters = FilterChain([
        SumRangeFilter(min_sum=180, max_sum=210),
        EvenOddFilter(min_even=6, max_even=9),
    ])

    allocations = [
        StrategyAllocation(
            strategy=RandomPureStrategy(),
            percentage=0.5,  # 50%
        ),
        StrategyAllocation(
            strategy=RandomFilteredStrategy(),
            percentage=0.5,  # 50%
            config_override={"filters": filters, "max_attempts": 10000}
        ),
    ]

    strategy = HybridStrategy(allocations=allocations)
    config = StrategyConfig(n_games=n_games, seed=seed)
    result = strategy.generate(config)

    # Resumo
    console.print(f"\n✅ [green]Gerados: {result.n_games} jogos[/green]")
    console.print(f"💰 Custo: R$ {result.total_cost:.2f}")
    console.print(f"🎯 Mix: 50% Pure + 50% Filtered")

    # Tabela
    table = Table(title="Primeiros 5 Jogos")
    table.add_column("#", style="cyan")
    table.add_column("Números", style="white")
    table.add_column("Soma", style="yellow")
    table.add_column("Estratégia", style="magenta")

    for i, game in enumerate(result.games[:5]):
        table.add_row(str(i + 1), str(game.numbers), str(game.sum), game.strategy)

    console.print(table)


# ============================================================================
# SIMULATE - Monte Carlo
# ============================================================================

simulate_app = typer.Typer()


@simulate_app.command()
def run(
    n_games: int = typer.Option(10, "--n-games", "-n", help="Jogos no portfolio"),
    simulations: int = typer.Option(10000, "--simulations", "-s", help="Simulações"),
    seed: Optional[int] = typer.Option(None, "--seed", help="Seed"),
):
    """Executa simulação Monte Carlo."""
    console.print(f"\n[bold cyan]Simulação Monte Carlo[/bold cyan]")
    console.print(f"Jogos: {n_games} | Simulações: {simulations:,}\n")

    # Gerar jogos
    strategy = RandomPureStrategy()
    config = StrategyConfig(n_games=n_games, seed=seed)
    result = strategy.generate(config)

    # Simular com progress bar
    simulator = MonteCarloSimulator()

    with Progress() as progress:
        task = progress.add_task("[cyan]Simulando...", total=simulations)

        def callback(current, total):
            progress.update(task, completed=current)

        sim_result = simulator.run(
            result.games,
            n_simulations=simulations,
            seed=seed,
            progress_callback=callback,
        )

    # Resultados
    console.print(f"\n[bold green]✅ Simulação completa![/bold green]\n")

    # Painel de resultados
    results_text = f"""
[yellow]Custo Total:[/yellow] R$ {sim_result.total_cost:.2f}
[yellow]Lucro Esperado:[/yellow] R$ {sim_result.expected_profit:.2f}
[yellow]ROI Esperado:[/yellow] {sim_result.expected_roi:.2f}%

[cyan]Probabilidades:[/cyan]
  P(Lucro > 0): {sim_result.probability_profit:.2f}%
  P(Prejuízo):  {100 - sim_result.probability_profit:.2f}%

[magenta]Percentis de Lucro:[/magenta]
  P5  (pior 5%): R$ {sim_result.percentiles['p5']:.2f}
  P50 (mediana):  R$ {sim_result.percentiles['p50']:.2f}
  P95 (top 5%):   R$ {sim_result.percentiles['p95']:.2f}

[red]VaR 95%:[/red] R$ {sim_result.var_95:.2f}
[green]Melhor caso:[/green] R$ {sim_result.best_case:.2f}
[red]Pior caso:[/red] R$ {sim_result.worst_case:.2f}
"""

    console.print(Panel(results_text, title="Resultados Monte Carlo", border_style="cyan"))


# ============================================================================
# BACKTEST - Teste Histórico
# ============================================================================

backtest_app = typer.Typer()


@backtest_app.command()
def run(
    n_games: int = typer.Option(10, "--n-games", "-n", help="Jogos"),
    days: int = typer.Option(30, "--days", "-d", help="Últimos N concursos"),
    db: str = typer.Option("sqlite:///lotofacil.db", "--database", help="Database URL"),
):
    """Executa backtest com dados históricos."""
    console.print(f"\n[bold cyan]Backtest Histórico[/bold cyan]\n")

    try:
        # Conectar ao banco
        database = get_database(db)
        session = database.get_session()

        # Buscar sorteios
        draws = session.query(Draw).order_by(Draw.concurso.desc()).limit(days).all()

        if not draws:
            console.print("[red]❌ Nenhum sorteio encontrado no banco[/red]")
            console.print("Execute: python -m app.cli.main etl import")
            return

        console.print(f"📊 Sorteios encontrados: {len(draws)}")

        # Gerar jogos
        strategy = RandomPureStrategy()
        config = StrategyConfig(n_games=n_games, seed=42)
        result = strategy.generate(config)

        # Backtest
        backtester = Backtester()
        bt_result = backtester.run(result.games, draws)

        # Resultados
        console.print(f"\n[bold green]✅ Backtest completo![/bold green]\n")

        results_text = f"""
[yellow]Jogos:[/yellow] {bt_result.n_games}
[yellow]Concursos:[/yellow] {len(bt_result.concursos_testados)}
[yellow]Custo:[/yellow] R$ {bt_result.total_custo:.2f}

[cyan]Resultados:[/cyan]
  Premio: R$ {bt_result.total_premio:.2f}
  Lucro:  R$ {bt_result.total_lucro:.2f}
  ROI:    {bt_result.roi:.2f}%

[magenta]Estatísticas:[/magenta]
  Win rate: {bt_result.win_rate:.2f}%
"""

        console.print(Panel(results_text, title="Resultados Backtest", border_style="green"))

        session.close()

    except Exception as e:
        console.print(f"[red]❌ Erro: {e}[/red]")


# ============================================================================
# ANALYZE - Análise de Dados
# ============================================================================

analyze_app = typer.Typer()


@analyze_app.command("stats")
def analyze_stats(
    db: str = typer.Option("sqlite:///lotofacil.db", "--database", help="Database URL"),
):
    """Mostra estatísticas dos dados históricos."""
    try:
        database = get_database(db)
        session = database.get_session()

        from sqlalchemy import func
        from app.io.database import DrawStats

        total = session.query(func.count(Draw.id)).scalar()

        if total == 0:
            console.print("[red]❌ Nenhum dado no banco[/red]")
            return

        # Estatísticas
        avg_soma = session.query(func.avg(DrawStats.soma)).scalar()
        avg_pares = session.query(func.avg(DrawStats.pares)).scalar()

        primeiro = session.query(Draw).order_by(Draw.concurso).first()
        ultimo = session.query(Draw).order_by(Draw.concurso.desc()).first()

        stats_text = f"""
[yellow]Total de Sorteios:[/yellow] {total:,}
[yellow]Período:[/yellow] {primeiro.data} a {ultimo.data}

[cyan]Estatísticas Médias:[/cyan]
  Soma: {avg_soma:.2f}
  Pares: {avg_pares:.2f}
"""

        console.print(Panel(stats_text, title="Dados Históricos", border_style="blue"))

        session.close()

    except Exception as e:
        console.print(f"[red]❌ Erro: {e}[/red]")


# ============================================================================
# ETL - Importar Dados
# ============================================================================

etl_app = typer.Typer()


@etl_app.command("init")
def etl_init(
    db: str = typer.Option("sqlite:///lotofacil.db", "--database", help="Database URL"),
):
    """Inicializa o banco de dados (cria tabelas)."""
    console.print("\n[bold cyan]Inicializando banco de dados...[/bold cyan]\n")

    try:
        database = init_database(db)
        console.print("[bold green]✅ Banco de dados inicializado![/bold green]")
        console.print(f"📦 Tabelas criadas: draws, draw_stats, runs, portfolios, games, results")
        console.print(f"📍 Local: {db}")

    except Exception as e:
        console.print(f"[red]❌ Erro: {e}[/red]")


@etl_app.command("import")
def etl_import(
    db: str = typer.Option("sqlite:///lotofacil.db", "--database", help="Database URL"),
):
    """Importa dados históricos da API."""
    console.print("\n[bold cyan]Importando dados históricos...[/bold cyan]\n")

    try:
        result = import_historical_data(database_url=db, update_existing=False)

        if result["success"]:
            console.print("[bold green]✅ Importação concluída![/bold green]\n")
            console.print(f"Total: {result['total_draws']} sorteios")
            console.print(f"Inseridos: {result['inserted']}")
            console.print(f"Tempo: {result['elapsed_seconds']:.2f}s")
        else:
            console.print("[red]❌ Importação falhou[/red]")

    except Exception as e:
        console.print(f"[red]❌ Erro: {e}[/red]")
