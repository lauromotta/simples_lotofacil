"""
CLI Principal - Lotofácil Pro

Interface de linha de comando para o sistema de análise Lotofácil.

Comandos disponíveis:
- generate: Gera jogos com diferentes estratégias
- backtest: Testa estratégias contra dados históricos
- simulate: Executa simulação Monte Carlo
- analyze: Analisa dados históricos
- etl: Importa dados da API

Exemplo de uso:
    python -m app.cli.main generate --strategy random_pure --n-games 10
    python -m app.cli.main simulate --n-games 10 --simulations 10000
    python -m app.cli.main backtest --strategy random_filtered --days 30
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import track
from typing import Optional
from pathlib import Path

from app.cli import commands

# Criar app Typer
app = typer.Typer(
    name="lotofacil",
    help="Sistema de Análise Lotofácil Pro",
    add_completion=False,
)

# Console Rich para output bonito
console = Console()

# Adicionar comandos
app.add_typer(commands.generate_app, name="generate", help="Gerar jogos")
app.add_typer(commands.simulate_app, name="simulate", help="Simulação Monte Carlo")
app.add_typer(commands.backtest_app, name="backtest", help="Backtest histórico")
app.add_typer(commands.analyze_app, name="analyze", help="Análise de dados")
app.add_typer(commands.etl_app, name="etl", help="Importar dados")


@app.command()
def version():
    """Mostra a versão do sistema."""
    console.print("[bold cyan]Lotofácil Pro v2.0[/bold cyan]")
    console.print("Sistema de Análise Probabilística")
    console.print("\n[yellow]⚠️  AVISO: EV = -53% ROI (casa sempre ganha!)[/yellow]")


@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Modo verbose"),
):
    """
    Sistema de Análise Lotofácil Pro.

    Um sistema completo para geração, análise e backtesting
    de estratégias de loteria baseadas em probabilidade.
    """
    if ctx.invoked_subcommand is None:
        console.print("[bold red]Erro: Nenhum comando especificado[/bold red]")
        console.print("Use --help para ver comandos disponíveis")


if __name__ == "__main__":
    app()
