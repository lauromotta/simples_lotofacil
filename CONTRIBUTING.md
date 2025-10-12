# Contribuindo para o Lotofacil Pro

Obrigado por considerar contribuir! Este documento fornece diretrizes para contribuicoes.

## Como Contribuir

### Reportar Bugs
- Use GitHub Issues
- Descreva o bug detalhadamente
- Inclua steps para reproduzir
- Informe versao do Python e OS

### Sugerir Features
- Abra um Issue com tag `enhancement`
- Descreva o caso de uso
- Explique o beneficio

### Pull Requests

1. Fork o repositorio
2. Crie uma branch: `git checkout -b feature/MinhaFeature`
3. Faca suas mudancas
4. Rode os testes: `pytest tests/ -v`
5. Commit: `git commit -m 'Add: nova feature'`
6. Push: `git push origin feature/MinhaFeature`
7. Abra um Pull Request

## Guidelines de Codigo

### Style Guide
- Siga PEP 8
- Use Black para formatacao
- Mantenha type hints (100%)
- Docstrings em todas as funcoes

### Testes
- Adicione testes para novas features
- Mantenha coverage em 100%
- Use pytest

### Commits
Use Conventional Commits:
- `feat:` nova feature
- `fix:` bug fix
- `docs:` documentacao
- `test:` adicionar testes
- `refactor:` refatoracao

## Ambiente de Desenvolvimento

```bash
# Clone e setup
git clone https://github.com/seu-usuario/lotofacil-pro.git
cd lotofacil-pro/simples_lotofacil

# Virtual env
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Instalar deps
pip install -r requirements.txt

# Rodar testes
pytest tests/ -v

# Coverage
pytest --cov=app tests/
```

## Code Review

Todos os PRs serao revisados quanto a:
- Qualidade do codigo
- Testes adequados
- Documentacao
- Performance
- Compatibilidade

## Obrigado!

Suas contribuicoes sao muito valiosas!
