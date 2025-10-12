"""
Módulo de combinatória e cálculos matemáticos fundamentais.

Implementa funções para:
- Cálculo de combinações
- Distribuição hipergeométrica
- Geração de subsets
- Validação de jogos
"""

import math
from typing import List, Set, Tuple
from itertools import combinations
import numpy as np
from scipy.stats import hypergeom


# Constantes da Lotofácil
UNIVERSO = 25  # Números de 1 a 25
TAMANHO_JOGO = 15  # 15 números por jogo
NUMEROS_SORTEADOS = 15  # 15 números sorteados
ESPACO_AMOSTRAL = math.comb(UNIVERSO, TAMANHO_JOGO)  # 3.268.760


def comb(n: int, k: int) -> int:
    """
    Calcula combinação C(n, k) = n! / (k! * (n-k)!)

    Args:
        n: Total de elementos
        k: Elementos a escolher

    Returns:
        Número de combinações possíveis

    Examples:
        >>> comb(25, 15)
        3268760
        >>> comb(5, 2)
        10
    """
    if k > n or k < 0:
        return 0
    return math.comb(n, k)


def prob_hipergeometrica(acertos: int) -> float:
    """
    Calcula probabilidade exata de acertar k números na Lotofácil
    usando distribuição hipergeométrica.

    Fórmula: P(k) = C(15, k) * C(10, 15-k) / C(25, 15)

    Args:
        acertos: Número de acertos (0 a 15)

    Returns:
        Probabilidade de acertar exatamente k números

    Examples:
        >>> prob_hipergeometrica(15)  # Sena
        3.0590... e-07
        >>> prob_hipergeometrica(11)  # Mais comum
        0.1538...
    """
    if acertos < 0 or acertos > TAMANHO_JOGO:
        return 0.0

    # P(k) = C(15, k) * C(10, 15-k) / C(25, 15)
    numerador = comb(NUMEROS_SORTEADOS, acertos) * comb(
        UNIVERSO - NUMEROS_SORTEADOS, TAMANHO_JOGO - acertos
    )
    denominador = ESPACO_AMOSTRAL

    return numerador / denominador


def prob_hipergeometrica_scipy(acertos: int) -> float:
    """
    Calcula probabilidade usando scipy.stats.hypergeom (mais preciso).

    Args:
        acertos: Número de acertos (0 a 15)

    Returns:
        Probabilidade de acertar exatamente k números
    """
    if acertos < 0 or acertos > TAMANHO_JOGO:
        return 0.0

    # hypergeom.pmf(k, M, n, N)
    # M = tamanho população (25)
    # n = sucessos na população (15 sorteados)
    # N = tamanho amostra (15 do jogo)
    # k = sucessos na amostra (acertos)
    return float(hypergeom.pmf(acertos, UNIVERSO, NUMEROS_SORTEADOS, TAMANHO_JOGO))


def tabela_probabilidades() -> dict[int, float]:
    """
    Gera tabela completa de probabilidades para todos os acertos possíveis.

    Returns:
        Dicionário {acertos: probabilidade}

    Examples:
        >>> tab = tabela_probabilidades()
        >>> tab[15]  # Acertar 15
        3.05...e-07
        >>> tab[11]  # Acertar 11
        0.153...
    """
    return {k: prob_hipergeometrica_scipy(k) for k in range(16)}


def calcular_acertos(jogo: List[int], sorteio: List[int]) -> int:
    """
    Calcula quantos números do jogo foram sorteados.

    Args:
        jogo: Lista de 15 números do jogo
        sorteio: Lista de 15 números sorteados

    Returns:
        Quantidade de acertos (0 a 15)

    Examples:
        >>> calcular_acertos([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15],
        ...                  [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])
        15
        >>> calcular_acertos([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15],
        ...                  [16,17,18,19,20,21,22,23,24,25,1,2,3,4,5])
        5
    """
    set_jogo = set(jogo)
    set_sorteio = set(sorteio)
    return len(set_jogo & set_sorteio)


def validar_jogo(jogo: List[int]) -> Tuple[bool, str]:
    """
    Valida se um jogo é válido segundo as regras da Lotofácil.

    Args:
        jogo: Lista de números do jogo

    Returns:
        Tupla (válido, mensagem_erro)

    Examples:
        >>> validar_jogo([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])
        (True, '')
        >>> validar_jogo([1,2,3,4,5])
        (False, 'Jogo deve ter exatamente 15 números')
    """
    # Verifica tamanho
    if len(jogo) != TAMANHO_JOGO:
        return False, f"Jogo deve ter exatamente {TAMANHO_JOGO} números"

    # Verifica duplicados
    if len(set(jogo)) != len(jogo):
        return False, "Jogo contém números duplicados"

    # Verifica intervalo
    for num in jogo:
        if num < 1 or num > UNIVERSO:
            return False, f"Número {num} fora do intervalo 1-{UNIVERSO}"

    return True, ""


def gerar_combinacoes(numeros: List[int], k: int = TAMANHO_JOGO) -> List[List[int]]:
    """
    Gera todas as combinações possíveis de k números.

    AVISO: Para grandes conjuntos, pode gerar milhões de combinações!

    Args:
        numeros: Lista de números base
        k: Tamanho das combinações (padrão: 15)

    Returns:
        Lista de todas as combinações

    Examples:
        >>> gerar_combinacoes([1,2,3,4,5], 3)
        [[1, 2, 3], [1, 2, 4], [1, 2, 5], [1, 3, 4], [1, 3, 5],
         [1, 4, 5], [2, 3, 4], [2, 3, 5], [2, 4, 5], [3, 4, 5]]
    """
    if k > len(numeros):
        return []

    return [list(comb) for comb in combinations(numeros, k)]


def gerar_jogo_aleatorio(seed: int | None = None) -> List[int]:
    """
    Gera um jogo aleatório válido.

    Args:
        seed: Seed para reprodutibilidade (opcional)

    Returns:
        Lista ordenada de 15 números únicos

    Examples:
        >>> jogo = gerar_jogo_aleatorio(seed=42)
        >>> len(jogo)
        15
        >>> len(set(jogo))
        15
        >>> min(jogo) >= 1 and max(jogo) <= 25
        True
    """
    if seed is not None:
        np.random.seed(seed)

    jogo = np.random.choice(UNIVERSO, TAMANHO_JOGO, replace=False) + 1
    return sorted(jogo.tolist())


def gerar_n_jogos_aleatorios(n: int, seed: int | None = None) -> List[List[int]]:
    """
    Gera N jogos aleatórios únicos.

    Args:
        n: Quantidade de jogos a gerar
        seed: Seed para reprodutibilidade

    Returns:
        Lista de jogos (cada jogo é uma lista de 15 números)

    Raises:
        ValueError: Se n > espaço amostral
    """
    if n > ESPACO_AMOSTRAL:
        raise ValueError(f"Impossível gerar {n} jogos únicos (máximo: {ESPACO_AMOSTRAL})")

    if seed is not None:
        np.random.seed(seed)

    jogos: Set[Tuple[int, ...]] = set()

    while len(jogos) < n:
        jogo = tuple(sorted(np.random.choice(UNIVERSO, TAMANHO_JOGO, replace=False) + 1))
        jogos.add(jogo)

    return [list(jogo) for jogo in jogos]


def soma_jogo(jogo: List[int]) -> int:
    """
    Calcula a soma dos números de um jogo.

    Args:
        jogo: Lista de números

    Returns:
        Soma total

    Examples:
        >>> soma_jogo([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])
        120
    """
    return sum(jogo)


def contar_pares_impares(jogo: List[int]) -> Tuple[int, int]:
    """
    Conta quantos números pares e ímpares há no jogo.

    Args:
        jogo: Lista de números

    Returns:
        Tupla (pares, ímpares)

    Examples:
        >>> contar_pares_impares([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])
        (7, 8)
    """
    pares = sum(1 for n in jogo if n % 2 == 0)
    impares = len(jogo) - pares
    return pares, impares


def maior_sequencia_consecutiva(jogo: List[int]) -> int:
    """
    Encontra o tamanho da maior sequência consecutiva.

    Args:
        jogo: Lista ordenada de números

    Returns:
        Tamanho da maior sequência

    Examples:
        >>> maior_sequencia_consecutiva([1,2,3,5,7,8,10])
        3  # 1,2,3
        >>> maior_sequencia_consecutiva([1,3,5,7,9,11,13])
        1  # Sem consecutivos
    """
    if not jogo:
        return 0

    jogo_sorted = sorted(jogo)
    max_seq = 1
    atual_seq = 1

    for i in range(1, len(jogo_sorted)):
        if jogo_sorted[i] == jogo_sorted[i - 1] + 1:
            atual_seq += 1
            max_seq = max(max_seq, atual_seq)
        else:
            atual_seq = 1

    return max_seq


def distribuicao_quadrantes(jogo: List[int]) -> dict[str, int]:
    """
    Distribui os números por quadrantes.

    Quadrantes:
    - Q1: 1-6
    - Q2: 7-12
    - Q3: 13-18
    - Q4: 19-25

    Args:
        jogo: Lista de números

    Returns:
        Dicionário com contagem por quadrante

    Examples:
        >>> distribuicao_quadrantes([1,2,7,8,13,14,19,20,21,22,23,24,25,3,4])
        {'q1': 3, 'q2': 2, 'q3': 2, 'q4': 7}
    """
    contagem = {"q1": 0, "q2": 0, "q3": 0, "q4": 0}

    for num in jogo:
        if 1 <= num <= 6:
            contagem["q1"] += 1
        elif 7 <= num <= 12:
            contagem["q2"] += 1
        elif 13 <= num <= 18:
            contagem["q3"] += 1
        elif 19 <= num <= 25:
            contagem["q4"] += 1

    return contagem


if __name__ == "__main__":
    # Testes básicos
    print("=" * 60)
    print("LOTOFÁCIL - Módulo de Combinatória")
    print("=" * 60)
    print(f"\nEspaço amostral: {ESPACO_AMOSTRAL:,}")
    print("\nTabela de Probabilidades:")
    print("-" * 40)

    tab = tabela_probabilidades()
    for acertos in range(11, 16):
        prob = tab[acertos]
        chance = 1 / prob if prob > 0 else float("inf")
        print(f"  {acertos} acertos: {prob:.8f} (1 em {chance:,.0f})")

    # Teste de jogo
    print("\n" + "=" * 60)
    print("Exemplo de jogo aleatório (seed=42):")
    jogo = gerar_jogo_aleatorio(seed=42)
    print(f"  Números: {jogo}")
    print(f"  Soma: {soma_jogo(jogo)}")
    pares, impares = contar_pares_impares(jogo)
    print(f"  Pares: {pares}, Ímpares: {impares}")
    print(f"  Maior sequência: {maior_sequencia_consecutiva(jogo)}")
    print(f"  Quadrantes: {distribuicao_quadrantes(jogo)}")
    print("=" * 60)
