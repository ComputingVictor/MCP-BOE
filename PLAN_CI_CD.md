# Plan CI/CD y Estrategia de Branching

## Estrategia de Ramas (GitFlow simplificado)

```
main          ← Producción, siempre estable
  ↑
develop       ← Integración, próxima release
  ↑
feature/*     ← Nuevas funcionalidades (feature/add-search-filter)
bugfix/*      ← Correcciones (bugfix/fix-date-validation)
hotfix/*      ← Fixes urgentes en producción (desde main)
release/*     ← Preparación de releases (desde develop)
```

### Reglas de Ramas
- `main`: Protegida, solo merge via PR desde `develop` o `hotfix/*`
- `develop`: Protegida, solo merge via PR desde `feature/*`, `bugfix/*`, `release/*`
- `feature/*`: Crear desde `develop`, merge a `develop`
- `hotfix/*`: Crear desde `main`, merge a `main` Y `develop`

## Archivos a Crear

### 1. `.github/workflows/ci.yml` - CI en PRs y pushes

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e ".[dev]"
      - run: python -m black --check src/
      - run: python -m flake8 src/
      - run: python -m mypy src/

  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.8', '3.10', '3.11', '3.12']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[test]"
      - run: python -m pytest tests/ -v --cov=src/mcp_boe --cov-report=xml
      - uses: codecov/codecov-action@v4
        if: matrix.python-version == '3.11'

  connectivity:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e .
      - run: python examples/basic_usage.py connectivity
```

### 2. `.github/workflows/release.yml` - Publicación a PyPI

```yaml
name: Release

on:
  push:
    tags: ['v*']

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install build twine
      - run: python -m build
      - run: twine upload dist/*
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
```

### 3. `.github/PULL_REQUEST_TEMPLATE.md`

```markdown
## Descripción
<!-- Qué cambios incluye este PR -->

## Tipo de cambio
- [ ] Feature (nueva funcionalidad)
- [ ] Bugfix (corrección de error)
- [ ] Hotfix (corrección urgente)
- [ ] Docs (documentación)
- [ ] Refactor (sin cambio funcional)

## Checklist
- [ ] Tests añadidos/actualizados
- [ ] Documentación actualizada
- [ ] `black` y `flake8` pasan
- [ ] Funciona con la API del BOE
```

### 4. `.github/dependabot.yml`

```yaml
version: 2
updates:
  - package-ecosystem: pip
    directory: "/"
    schedule:
      interval: weekly
  - package-ecosystem: github-actions
    directory: "/"
    schedule:
      interval: weekly
```

### 5. Protección de ramas (configurar en GitHub Settings)

**main:**
- Require PR before merging
- Require status checks: `lint`, `test`
- Require branches up to date
- No force pushes

**develop:**
- Require PR before merging
- Require status checks: `lint`, `test`

## Pasos de Implementación

1. **Crear rama develop**
   ```bash
   git checkout -b develop
   git push -u origin develop
   ```

2. **Crear archivos de workflow**
   - `.github/workflows/ci.yml`
   - `.github/workflows/release.yml`
   - `.github/PULL_REQUEST_TEMPLATE.md`
   - `.github/dependabot.yml`

3. **Configurar protección en GitHub**
   - Settings → Branches → Add rule

4. **Añadir secrets en GitHub**
   - `PYPI_TOKEN` para releases
   - `CODECOV_TOKEN` para coverage (opcional)

## Flujo de Trabajo Diario

```bash
# Nueva feature
git checkout develop
git pull
git checkout -b feature/mi-feature
# ... trabajo ...
git push -u origin feature/mi-feature
# Crear PR a develop en GitHub

# Hotfix urgente
git checkout main
git pull
git checkout -b hotfix/fix-critico
# ... fix ...
git push -u origin hotfix/fix-critico
# Crear PR a main Y otro a develop
```
