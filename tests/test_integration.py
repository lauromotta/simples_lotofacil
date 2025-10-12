"""
Testes de integracao basicos para Lotofacil Pro.

Execute com: pytest tests/ -v
"""

import pytest
from app.core.game import Game
from app.core.combinatorics import comb
from app.strategies import RandomPureStrategy, RandomFilteredStrategy, StrategyConfig
from app.filters import FilterChain, SumRangeFilter, EvenOddFilter


def test_game_creation():
    """Testa criacao de jogo valido."""
    game = Game(numbers=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])
    assert len(game.numbers) == 15
    assert game.sum == 120
    assert all(1 <= n <= 25 for n in game.numbers)


def test_combinatorics():
    """Testa calculo combinatorio."""
    # C(25, 15) = 3,268,760
    total = comb(25, 15)
    assert total == 3268760


def test_random_pure_strategy():
    """Testa geracao com RandomPureStrategy."""
    strategy = RandomPureStrategy()
    config = StrategyConfig(n_games=10, seed=42)
    result = strategy.generate(config)
    
    assert result.n_games == 10
    assert result.total_cost == 30.0  # 10 jogos * R$ 3.00
    assert len(result.games) == 10
    
    # Verifica que todos os jogos sao validos
    for game in result.games:
        assert len(game.numbers) == 15
        assert len(set(game.numbers)) == 15  # Sem duplicatas
        assert all(1 <= n <= 25 for n in game.numbers)


def test_random_filtered_strategy():
    """Testa geracao com filtros."""
    chain = FilterChain([
        SumRangeFilter(min_sum=180, max_sum=210),
        EvenOddFilter(min_even=6, max_even=9),
    ])
    
    strategy = RandomFilteredStrategy()
    config = StrategyConfig(n_games=5, seed=42, filters=chain, max_attempts=10000)
    result = strategy.generate(config)
    
    assert result.n_games == 5
    
    # Todos os jogos devem passar nos filtros
    for game in result.games:
        assert 180 <= game.sum <= 210
        even_count = sum(1 for n in game.numbers if n % 2 == 0)
        assert 6 <= even_count <= 9


def test_reproducibility():
    """Testa reprodutibilidade com seed."""
    strategy = RandomPureStrategy()
    
    # Gera 2 vezes com mesmo seed
    result1 = strategy.generate(StrategyConfig(n_games=5, seed=42))
    result2 = strategy.generate(StrategyConfig(n_games=5, seed=42))
    
    # Devem ser identicos
    for g1, g2 in zip(result1.games, result2.games):
        assert g1.numbers == g2.numbers


def test_cli_version():
    """Testa que CLI pode ser importada."""
    from app.cli import main
    assert main.app is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
