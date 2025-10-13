# 🎰 Lotofacil Pro - Sistema de Analise Probabilistica

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Sistema profissional de analise probabilistica da Lotofacil com multiplas estrategias de geracao, backtesting historico, simulacao Monte Carlo e API REST completa.

## 🚀 Caracteristicas Principais

### 🎯 Estrategias de Geracao
- **Random Pure**: Geracao aleatoria pura (25,000 jogos/s)
- **Random Filtered**: Geracao com filtros aplicados (12,500 jogos/s)
- **Wheeling**: Sistema de cobertura completa (100,000 jogos/s)
- **Hybrid**: Combinacao de estrategias com alocacao customizada

### 📊 Analise Avancada
- **Monte Carlo Simulation**: Simula 10,000+ sorteios aleatorios
- **Historical Backtesting**: Testa contra 3,509 sorteios historicos (2003-2025)
- **Walk-Forward Validation**: Validacao temporal para evitar overfitting
- **Value at Risk (VaR)**: Metricas de risco financeiro

### 🔧 Wheeling Systems
- **2-wise Coverage**: Garante todos os pares em apenas 3 jogos!
- **Abbreviated Wheeling**: Reduz 816 jogos para 11 (economia de 98.7%)
- **Key Number Wheeling**: Numeros fixos em todos os jogos
- **Coverage Analyzer**: Analisa 1-wise, 2-wise, 3-wise coverage

### 🖥️ Interfaces

#### CLI (Command Line Interface)
```bash
# Gerar jogos
python -m app.cli.main generate pure --n-games 10
python -m app.cli.main generate filtered --sum-min 180 --sum-max 210
python -m app.cli.main generate wheeling --wheel-size 18 --n-games 20
python -m app.cli.main generate hybrid --n-games 20

# Simulacao Monte Carlo
python -m app.cli.main simulate run --n-games 10 --simulations 10000

# Backtest historico
python -m app.cli.main backtest run --n-games 10 --days 30

# Estatisticas
python -m app.cli.main analyze stats

# ETL
python -m app.cli.main etl init      # Inicializar banco
python -m app.cli.main etl import    # Importar 3,509 sorteios
```

#### REST API (FastAPI)
```bash
# Iniciar servidor
python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8001

# Documentacao interativa
http://localhost:8001/docs      # Swagger UI
http://localhost:8001/redoc     # ReDoc
```

**Endpoints disponiveis:**
- `POST /generate/pure` - Geracao aleatoria pura
- `POST /generate/filtered` - Geracao com filtros
- `POST /generate/wheeling` - Wheeling system
- `POST /generate/hybrid` - Estrategia hibrida
- `POST /simulate` - Simulacao Monte Carlo
- `POST /backtest` - Backtest historico
- `GET /stats` - Estatisticas historicas
- `POST /etl/import` - Importar dados (background)
- `GET /health` - Health check

## 📦 Instalacao

### Requisitos
- Python 3.11+
- pip

### Setup Rapido
```bash
# Clonar repositorio
git clone https://github.com/seu-usuario/lotofacil-pro.git
cd lotofacil-pro/simples_lotofacil

# Criar ambiente virtual (recomendado)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Inicializar banco de dados
python -m app.cli.main etl init

# Importar dados historicos (3,509 sorteios)
python -m app.cli.main etl import
```

## 🎯 Uso Basico

### CLI Examples

#### Gerar 10 jogos aleatorios
```bash
python -m app.cli.main generate pure --n-games 10 --seed 42
```

**Output:**
```
Gerando 10 jogos (RandomPure)...

✅ Gerados: 10 jogos
💰 Custo: R$ 30.00
⏱️  Tempo: 0.0080s

                          Primeiros 5 Jogos
┌───┬─────────────────────────────────────────────────────────┬──────┐
│ # │ Numeros                                                 │ Soma │
├───┼─────────────────────────────────────────────────────────┼──────┤
│ 1 │ [1, 2, 3, 4, 5, 6, 9, 10, 12, 13, 14, 16, 17, 23, 24]  │ 159  │
│ 2 │ [1, 2, 3, 4, 5, 6, 8, 9, 11, 13, 14, 18, 20, 21, 24]   │ 159  │
│ 3 │ [1, 4, 5, 6, 10, 11, 13, 14, 16, 17, 18, 19, 22, 23, 25]│ 204  │
└───┴─────────────────────────────────────────────────────────┴──────┘
```

#### Gerar jogos com filtros
```bash
python -m app.cli.main generate filtered \
  --n-games 10 \
  --sum-min 180 \
  --sum-max 210 \
  --even-min 6 \
  --even-max 9
```

#### Simulacao Monte Carlo
```bash
python -m app.cli.main simulate run \
  --n-games 10 \
  --simulations 10000 \
  --seed 42
```

**Output:**
```
┌────────────────────────── Resultados Monte Carlo ───────────────────────────┐
│                                                                             │
│ Custo Total: R$ 30.00                                                       │
│ Lucro Esperado: R$ -23.00                                                   │
│ ROI Esperado: -76.74%                                                       │
│                                                                             │
│ Probabilidades:                                                             │
│   P(Lucro > 0): 0.49%                                                       │
│   P(Prejuizo):  98.90%                                                      │
│                                                                             │
│ VaR 95%: R$ -30.00                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### API Examples

#### Gerar jogos via API
```bash
curl -X POST "http://localhost:8001/generate/pure" \
  -H "Content-Type: application/json" \
  -d '{"n_games": 10, "seed": 42}'
```

**Response:**
```json
{
  "success": true,
  "n_games": 10,
  "total_cost": 30.0,
  "execution_time": 0.008,
  "games": [
    {
      "numbers": [1, 2, 3, 4, 5, 6, 9, 10, 12, 13, 14, 16, 17, 23, 24],
      "sum": 159,
      "even_count": 8,
      "strategy": "random_pure"
    }
  ]
}
```

#### Simulacao Monte Carlo via API
```bash
curl -X POST "http://localhost:8001/simulate" \
  -H "Content-Type: application/json" \
  -d '{"n_games": 10, "n_simulations": 10000, "seed": 42}'
```

#### Ver estatisticas historicas
```bash
curl "http://localhost:8001/stats"
```

**Response:**
```json
{
  "success": true,
  "total_draws": 3509,
  "first_draw": "29/09/2003",
  "last_draw": "10/10/2025",
  "avg_sum": 195.18,
  "avg_even": 7.20
}
```

## 🏗️ Arquitetura do Projeto

```
simples_lotofacil/
├── app/
│   ├── core/                    # Modulos base
│   │   ├── game.py              # Modelo Game (Pydantic)
│   │   ├── math_utils.py        # Funcoes matematicas
│   │   └── constants.py         # Constantes
│   │
│   ├── filters/                 # Sistema de filtros
│   │   ├── base.py              # BaseFilter abstrato
│   │   ├── sum_range.py         # Filtro de soma
│   │   ├── even_odd.py          # Filtro de pares/impares
│   │   ├── consecutive.py       # Filtro de consecutivos
│   │   └── chain.py             # FilterChain
│   │
│   ├── strategies/              # Estrategias de geracao
│   │   ├── base.py              # BaseStrategy abstrato
│   │   ├── random_pure.py       # Random puro
│   │   ├── random_filtered.py   # Random com filtros
│   │   ├── wheeling.py          # Wheeling system
│   │   └── hybrid.py            # Estrategia hibrida
│   │
│   ├── wheeling/                # Wheeling avancado
│   │   ├── coverage.py          # CoverageAnalyzer
│   │   ├── two_wise.py          # 2-wise coverage
│   │   ├── key_number.py        # Key number wheeling
│   │   └── abbreviated.py       # Abbreviated wheeling
│   │
│   ├── backtest/                # Backtesting
│   │   ├── base.py              # Backtester
│   │   └── walk_forward.py      # Walk-forward validation
│   │
│   ├── monte_carlo/             # Simulacao Monte Carlo
│   │   └── simulator.py         # MonteCarloSimulator
│   │
│   ├── io/                      # Input/Output
│   │   ├── database.py          # SQLAlchemy models
│   │   └── etl.py               # ETL pipeline
│   │
│   ├── cli/                     # Command Line Interface
│   │   ├── main.py              # Typer app
│   │   └── commands.py          # CLI commands
│   │
│   └── api/                     # REST API
│       ├── main.py              # FastAPI app
│       └── __init__.py
│
├── tests/                       # Testes
│   ├── test_filters.py
│   ├── test_strategies.py
│   ├── test_wheeling.py
│   ├── test_backtest.py
│   └── test_monte_carlo.py
│
├── requirements.txt             # Dependencias
├── README.md                    # Este arquivo
└── lotofacil.db                 # Banco SQLite (gerado)
```

## 📊 Resultados e Estatisticas

### Performance Benchmarks

| Estrategia         | Jogos/segundo | Complexidade |
|-------------------|---------------|--------------|
| Random Pure       | 25,000        | O(n)         |
| Random Filtered   | 12,500        | O(n*f)       |
| Wheeling          | 100,000       | O(C(n,k))    |
| Hybrid            | 20,000        | O(n*m)       |

### Wheeling Efficiency

| Sistema              | Jogos | Cobertura | Economia  |
|---------------------|-------|-----------|-----------|
| Full Wheel (18)     | 816   | 100%      | -         |
| Abbreviated Wheel   | 11    | 90%+      | R$ 2,415  |
| 2-wise Coverage     | 3     | 100% pares| 99.6%     |

### Expected Value Analysis

Baseado em **10,000 simulacoes Monte Carlo** com 10 jogos:

| Metrica                  | Valor      |
|--------------------------|------------|
| ROI Esperado             | -76.74%    |
| Probabilidade de Lucro   | 0.49%      |
| Probabilidade de Prejuizo| 98.90%     |
| VaR 95%                  | -R$ 30.00  |
| Mediana de Lucro         | -R$ 25.00  |

**⚠️ AVISO:** Expected Value = -53% ROI. A casa sempre ganha no longo prazo!

## 🧪 Testes

### Executar todos os testes
```bash
pytest tests/ -v
```

### Testes por modulo
```bash
pytest tests/test_filters.py -v
pytest tests/test_strategies.py -v
pytest tests/test_wheeling.py -v
pytest tests/test_backtest.py -v
pytest tests/test_monte_carlo.py -v
```

### Coverage
```bash
pytest --cov=app tests/
```

## 📚 Documentacao Tecnica

### Modelos Principais

#### Game (Pydantic)
```python
class Game(BaseModel):
    numbers: List[int]              # 15 numeros ordenados
    sum: int                        # Soma dos numeros
    strategy: str                   # Estrategia usada
    seed: Optional[int] = None      # Seed (reprodutibilidade)
```

#### StrategyConfig
```python
@dataclass
class StrategyConfig:
    n_games: int                           # Quantidade de jogos
    seed: Optional[int] = None             # Seed
    filters: Optional[FilterChain] = None  # Filtros
    max_attempts: int = 1000               # Tentativas max
    allow_duplicates: bool = False         # Permitir duplicatas
```

#### FilterChain
```python
chain = FilterChain([
    SumRangeFilter(min_sum=180, max_sum=210),
    EvenOddFilter(min_even=6, max_even=9),
    ConsecutiveFilter(max_consecutive=3)
])
```

### Algoritmos

#### Monte Carlo Simulation
1. Gera N jogos usando estrategia escolhida
2. Para cada simulacao (1 a 10,000):
   - Gera sorteio aleatorio
   - Compara com todos os jogos
   - Calcula premios e lucro
3. Agrega estatisticas: media, percentis, VaR, probabilidades

#### Walk-Forward Validation
1. Divide historico em janelas (train + test)
2. Para cada janela:
   - Treina/gera jogos com dados do passado
   - Testa contra sorteios futuros
3. Avalia consistencia (std de ROI entre janelas)

#### 2-wise Coverage (Greedy)
1. Lista todas as combinacoes de pares (C(n,2) = 153 para 18 numeros)
2. Enquanto ha pares nao cobertos:
   - Gera jogo que cobre maximo de pares pendentes
   - Marca pares como cobertos
3. Resultado: 100% coverage em ~3 jogos

## 🛠️ Tecnologias Utilizadas

- **Python 3.11+**: Linguagem base
- **FastAPI**: Framework web moderno e rapido
- **Typer**: CLI profissional
- **Rich**: Output colorido e formatado no terminal
- **Pydantic 2.x**: Validacao de dados
- **SQLAlchemy 2.0**: ORM para banco de dados
- **NumPy**: Computacao numerica
- **Pandas**: Manipulacao de dados
- **SciPy**: Funcoes estatisticas
- **Uvicorn**: Servidor ASGI

## 📖 API Publica Utilizada

Este sistema consome a API publica da Lotofacil:
```
https://loteriascaixa-api.herokuapp.com/api/lotofacil
```

**Dados fornecidos:**
- Historico completo (3,509+ sorteios desde 2003)
- Resultados atualizados
- Informacoes de premiacao
- Dados de arrecadacao

## 🤝 Contribuindo

Contribuicoes sao bem-vindas! Para contribuir:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudancas (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Guidelines
- Siga PEP 8
- Adicione testes para novas features
- Mantenha type hints (100% coverage)
- Documente funcoes com docstrings
- Use conventional commits

## 📝 Licenca

Este projeto esta sob a licenca MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## ⚠️ Aviso Legal

Este software e destinado **APENAS** para fins educacionais e de pesquisa em probabilidade e estatistica.

- Nao incentivamos jogos de azar
- Jogue com responsabilidade
- O Expected Value da Lotofacil e negativo (-53% ROI)
- A probabilidade de lucro e inferior a 1%
- Este sistema NAO aumenta suas chances de ganhar

**A casa sempre ganha no longo prazo.**

## 🙏 Agradecimentos

- API Loterias Caixa (https://loteriascaixa-api.herokuapp.com)
- Comunidade Python Brasil
- Contribuidores open source

## 📞 Contato

- GitHub: [@lauromotta](https://github.com/lauromotta)
- Issues: [GitHub Issues](https://github.com/lauromotta/lotofacil-pro/issues)

---

**Desenvolvido com ❤️ e Python 3.11**

*Ultima atualizacao: Outubro 2025*
