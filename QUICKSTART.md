# Guia Rapido - Lotofacil Pro

Comece a usar o sistema em 5 minutos!

## 1. Instalacao (30 segundos)

```bash
# Clone o repositorio
git clone https://github.com/seu-usuario/lotofacil-pro.git
cd lotofacil-pro/simples_lotofacil

# Crie ambiente virtual
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Instale dependencias
pip install -r requirements.txt
```

## 2. Setup do Banco (20 segundos)

```bash
# Inicializar banco SQLite
python -m app.cli.main etl init

# Importar 3,509 sorteios historicos
python -m app.cli.main etl import
```

Aguarde ~10 segundos para importacao completa.

## 3. Gerar Seus Primeiros Jogos (10 segundos)

```bash
# Gerar 10 jogos aleatorios
python -m app.cli.main generate pure --n-games 10
```

**Output:**
```
✅ Gerados: 10 jogos
💰 Custo: R$ 30.00

                          Primeiros 5 Jogos
┌───┬─────────────────────────────────────────────────────────┬──────┐
│ # │ Numeros                                                 │ Soma │
├───┼─────────────────────────────────────────────────────────┼──────┤
│ 1 │ [1, 2, 3, 4, 5, 6, 9, 10, 12, 13, 14, 16, 17, 23, 24]  │ 159  │
...
```

## 4. Testar Outras Features

### Gerar com filtros
```bash
python -m app.cli.main generate filtered \
  --n-games 10 \
  --sum-min 180 \
  --sum-max 210
```

### Simulacao Monte Carlo (descobre o ROI real)
```bash
python -m app.cli.main simulate run \
  --n-games 10 \
  --simulations 10000
```

**Resultado:** ROI ~-76% (casa sempre ganha!)

### Backtest historico
```bash
python -m app.cli.main backtest run \
  --n-games 10 \
  --days 30
```

### Ver estatisticas
```bash
python -m app.cli.main analyze stats
```

## 5. Usar a API REST (opcional)

```bash
# Iniciar servidor
python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8001
```

Abra no navegador: **http://localhost:8001/docs**

### Testar endpoint
```bash
curl -X POST "http://localhost:8001/generate/pure" \
  -H "Content-Type: application/json" \
  -d '{"n_games": 5, "seed": 42}'
```

## Comandos Uteis

```bash
# Ver todos os comandos
python -m app.cli.main --help

# Ver help de comando especifico
python -m app.cli.main generate --help

# Versao do sistema
python -m app.cli.main version

# Rodar testes
pytest tests/ -v
```

## Proximos Passos

- Leia o [README.md](README.md) completo
- Explore a [documentacao da API](API.md)
- Veja o [CHANGELOG.md](CHANGELOG.md) com todas as features

## Aviso Importante

**Expected Value = -53% ROI**

A probabilidade de lucro e inferior a 1%. Este sistema e apenas para fins educacionais!

---

**Pronto! Voce ja esta rodando o Lotofacil Pro!** 🎉
