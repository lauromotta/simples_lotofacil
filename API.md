# API REST - Documentacao

API REST para o sistema Lotofacil Pro usando FastAPI.

## Inicio Rapido

### Iniciar Servidor
```bash
python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8001
```

### Documentacao Interativa
- **Swagger UI:** http://localhost:8001/docs
- **ReDoc:** http://localhost:8001/redoc

## Endpoints Principais

### POST /generate/pure
Gera jogos aleatorios puros.

### POST /generate/filtered
Gera jogos com filtros (soma, pares).

### POST /simulate
Simulacao Monte Carlo (10k+ iteracoes).

### POST /backtest
Backtest contra historico (3,509 sorteios).

### GET /stats
Estatisticas dos dados historicos.

## Exemplos

### cURL
```bash
curl -X POST "http://localhost:8001/generate/pure"   -H "Content-Type: application/json"   -d '{"n_games": 10, "seed": 42}'
```

### Python
```python
import requests
r = requests.post(
    "http://localhost:8001/generate/pure",
    json={"n_games": 10}
)
print(r.json())
```

**Documentacao completa:** http://localhost:8001/docs
