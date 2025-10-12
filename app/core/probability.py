"""
Módulo de probabilidade e cálculos de valor esperado (Expected Value).

Implementa:
- Cálculo de EV (Expected Value)
- Análise de ROI teórico
- Distribuição de prêmios
- Análise de risco/retorno
"""

from typing import Dict
from dataclasses import dataclass
from app.core.combinatorics import tabela_probabilidades, ESPACO_AMOSTRAL


# Valores médios de premiação (podem variar por concurso)
PREMIOS_PADRAO = {
    15: 1_500_000.00,  # 15 pontos - Sena
    14: 1_500.00,      # 14 pontos
    13: 25.00,         # 13 pontos
    12: 10.00,         # 12 pontos
    11: 5.00,          # 11 pontos
}

# Preços por quantidade de números
PRECOS = {
    15: 2.50,
    16: 40.00,
    17: 340.00,
    18: 2_040.00,
    19: 9_690.00,
    20: 38_760.00,
}


@dataclass
class ExpectedValue:
    """
    Resultado do cálculo de Expected Value.

    Attributes:
        ev: Expected Value (valor esperado de retorno)
        custo: Custo da aposta
        retorno_esperado: EV absoluto
        roi_percentual: ROI em percentual
        lucro_esperado: Lucro esperado (ev - custo)
        probabilidade_lucro: Probabilidade de ter lucro
    """
    ev: float
    custo: float
    retorno_esperado: float
    roi_percentual: float
    lucro_esperado: float
    probabilidade_lucro: float

    def __str__(self) -> str:
        return (
            f"Expected Value Analysis:\n"
            f"  Custo: R$ {self.custo:.2f}\n"
            f"  EV: R$ {self.ev:.2f}\n"
            f"  Retorno Esperado: R$ {self.retorno_esperado:.2f}\n"
            f"  Lucro Esperado: R$ {self.lucro_esperado:.2f}\n"
            f"  ROI: {self.roi_percentual:.2f}%\n"
            f"  P(lucro): {self.probabilidade_lucro:.4f}"
        )


def calcular_ev(
    premios: Dict[int, float] | None = None,
    custo: float = PRECOS[15]
) -> ExpectedValue:
    """
    Calcula o Expected Value (Valor Esperado) de um jogo da Lotofácil.

    EV = Σ(P(k) * Premio(k)) - Custo

    Args:
        premios: Dicionário {acertos: premio}. Se None, usa PREMIOS_PADRAO
        custo: Custo da aposta (padrão: R$ 2,50 para 15 números)

    Returns:
        ExpectedValue com análise completa

    Examples:
        >>> ev = calcular_ev()
        >>> ev.roi_percentual < 0  # EV é negativo na loteria
        True
    """
    if premios is None:
        premios = PREMIOS_PADRAO

    probabilidades = tabela_probabilidades()

    # Calcular EV: soma de (probabilidade * premio) para cada faixa
    ev_total = 0.0
    for acertos in range(11, 16):  # 11 a 15 pontos pagam prêmio
        prob = probabilidades[acertos]
        premio = premios.get(acertos, 0.0)
        ev_total += prob * premio

    # Retorno esperado (bruto)
    retorno_esperado = ev_total

    # Lucro esperado (líquido)
    lucro_esperado = ev_total - custo

    # ROI percentual
    roi_percentual = (lucro_esperado / custo) * 100 if custo > 0 else 0

    # Probabilidade de ter algum lucro (11 a 15 pontos)
    prob_lucro = sum(probabilidades[k] for k in range(11, 16))

    return ExpectedValue(
        ev=ev_total,
        custo=custo,
        retorno_esperado=retorno_esperado,
        roi_percentual=roi_percentual,
        lucro_esperado=lucro_esperado,
        probabilidade_lucro=prob_lucro
    )


def calcular_ev_portfolio(
    n_jogos: int,
    n_numeros: int = 15,
    premios: Dict[int, float] | None = None
) -> ExpectedValue:
    """
    Calcula EV para um portfólio de N jogos.

    Args:
        n_jogos: Quantidade de jogos
        n_numeros: Números por jogo (15-20)
        premios: Dicionário de prêmios

    Returns:
        ExpectedValue do portfólio completo
    """
    custo_unitario = PRECOS.get(n_numeros, PRECOS[15])
    custo_total = custo_unitario * n_jogos

    ev_unitario = calcular_ev(premios, custo_unitario)

    # EV escala linearmente com número de jogos
    return ExpectedValue(
        ev=ev_unitario.ev * n_jogos,
        custo=custo_total,
        retorno_esperado=ev_unitario.retorno_esperado * n_jogos,
        roi_percentual=ev_unitario.roi_percentual,  # ROI% é o mesmo
        lucro_esperado=ev_unitario.lucro_esperado * n_jogos,
        probabilidade_lucro=ev_unitario.probabilidade_lucro
    )


def probabilidade_pelo_menos_k_acertos(k: int) -> float:
    """
    Calcula probabilidade de acertar pelo menos k números.

    P(X >= k) = Σ P(i) para i >= k

    Args:
        k: Mínimo de acertos desejado

    Returns:
        Probabilidade acumulada

    Examples:
        >>> probabilidade_pelo_menos_k_acertos(11)  # Qualquer prêmio
        0.222...
        >>> probabilidade_pelo_menos_k_acertos(15)  # Só sena
        3.05...e-07
    """
    if k < 0 or k > 15:
        return 0.0

    probabilidades = tabela_probabilidades()
    return sum(probabilidades[i] for i in range(k, 16))


def analise_risco_retorno(
    n_jogos: int,
    n_numeros: int = 15,
    premios: Dict[int, float] | None = None
) -> Dict[str, float]:
    """
    Análise completa de risco e retorno.

    Args:
        n_jogos: Quantidade de jogos
        n_numeros: Números por jogo
        premios: Prêmios customizados

    Returns:
        Dicionário com métricas de risco/retorno
    """
    ev = calcular_ev_portfolio(n_jogos, n_numeros, premios)
    prob_tbl = tabela_probabilidades()

    # Variância e desvio padrão
    # Var(X) = E[X²] - E[X]²
    if premios is None:
        premios = PREMIOS_PADRAO

    e_x = ev.retorno_esperado / n_jogos  # EV por jogo
    e_x2 = sum(prob_tbl[k] * (premios.get(k, 0) ** 2) for k in range(11, 16))

    variancia = e_x2 - (e_x ** 2)
    desvio_padrao = variancia ** 0.5
    volatilidade = desvio_padrao * (n_jogos ** 0.5)  # Escala com √n

    # Sharpe Ratio (aproximado)
    # Sharpe = (Retorno - Risk-free) / Volatilidade
    # Assumindo risk-free = 0 para simplificar
    sharpe = ev.lucro_esperado / volatilidade if volatilidade > 0 else 0

    return {
        "ev_total": ev.ev,
        "custo_total": ev.custo,
        "lucro_esperado": ev.lucro_esperado,
        "roi_percentual": ev.roi_percentual,
        "probabilidade_premio": ev.probabilidade_lucro,
        "desvio_padrao_jogo": desvio_padrao,
        "volatilidade_portfolio": volatilidade,
        "sharpe_ratio": sharpe,
        "max_perda": -ev.custo,  # Pior cenário: perder tudo
        "max_ganho_teorico": premios.get(15, 0) * n_jogos,  # Todos com 15 pontos (impossível)
    }


def distribuicao_premios_esperada(
    n_jogos: int,
    premios: Dict[int, float] | None = None
) -> Dict[int, float]:
    """
    Calcula distribuição esperada de prêmios para N jogos.

    Retorna quantidade esperada de cada tipo de acerto.

    Args:
        n_jogos: Quantidade de jogos
        premios: Prêmios (para referência)

    Returns:
        Dicionário {acertos: quantidade_esperada}

    Examples:
        >>> dist = distribuicao_premios_esperada(1000)
        >>> dist[11] > dist[15]  # 11 pontos é mais comum que 15
        True
    """
    prob_tbl = tabela_probabilidades()

    distribuicao = {}
    for acertos in range(11, 16):
        quantidade_esperada = n_jogos * prob_tbl[acertos]
        distribuicao[acertos] = quantidade_esperada

    return distribuicao


def break_even_jogos(
    premio_15: float = PREMIOS_PADRAO[15],
    custo: float = PRECOS[15]
) -> int:
    """
    Calcula quantos jogos seriam necessários para break-even estatístico.

    Este é um cálculo puramente teórico e não representa garantia.

    Args:
        premio_15: Valor do prêmio de 15 acertos
        custo: Custo por jogo

    Returns:
        Número de jogos para EV = 0 (aprox)
    """
    prob_15 = tabela_probabilidades()[15]

    # Para break-even: custo_total = premio_15 * prob_15 * n_jogos
    # Mas loteria tem múltiplas faixas, então isso é aproximação

    ev_jogo = calcular_ev({15: premio_15, 14: 0, 13: 0, 12: 0, 11: 0}, custo)

    if ev_jogo.lucro_esperado >= 0:
        return 1  # Já positivo (muito improvável)

    # Aproximação: quantos jogos até compensar a casa
    jogos_necessarios = int(abs(custo / ev_jogo.lucro_esperado))

    return jogos_necessarios


if __name__ == "__main__":
    print("=" * 70)
    print("LOTOFÁCIL - Análise de Probabilidade e Expected Value")
    print("=" * 70)

    # Análise de 1 jogo
    print("\n📊 Análise de 1 jogo (15 números - R$ 2,50)")
    print("-" * 70)
    ev_simples = calcular_ev()
    print(ev_simples)

    # Análise de portfólio
    print("\n📊 Análise de Portfólio (100 jogos)")
    print("-" * 70)
    ev_port = calcular_ev_portfolio(100)
    print(f"  Custo Total: R$ {ev_port.custo:.2f}")
    print(f"  Retorno Esperado: R$ {ev_port.retorno_esperado:.2f}")
    print(f"  Lucro Esperado: R$ {ev_port.lucro_esperado:.2f}")
    print(f"  ROI: {ev_port.roi_percentual:.2f}%")

    # Distribuição esperada
    print("\n📊 Distribuição Esperada de Acertos (1000 jogos)")
    print("-" * 70)
    dist = distribuicao_premios_esperada(1000)
    for acertos in sorted(dist.keys(), reverse=True):
        qtd = dist[acertos]
        premio = PREMIOS_PADRAO.get(acertos, 0)
        total = qtd * premio
        print(f"  {acertos} pontos: {qtd:8.2f} jogos → R$ {total:12,.2f}")

    # Risco e retorno
    print("\n📊 Análise de Risco e Retorno (100 jogos)")
    print("-" * 70)
    risco = analise_risco_retorno(100)
    print(f"  EV Total: R$ {risco['ev_total']:.2f}")
    print(f"  Volatilidade: R$ {risco['volatilidade_portfolio']:.2f}")
    print(f"  Sharpe Ratio: {risco['sharpe_ratio']:.4f}")
    print(f"  Max Perda: R$ {risco['max_perda']:.2f}")

    # Probabilidades acumuladas
    print("\n📊 Probabilidades Acumuladas")
    print("-" * 70)
    for k in [11, 12, 13, 14, 15]:
        prob = probabilidade_pelo_menos_k_acertos(k)
        print(f"  P(X >= {k}): {prob:.6f} ({1/prob:.0f} em 1)")

    print("\n" + "=" * 70)
    print("⚠️  AVISO: EV negativo significa que a casa sempre ganha no longo prazo.")
    print("=" * 70)
