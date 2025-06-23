# Python 3.13 Migration Plan for agents-api

## Assessment Summary
Switching to Python 3.13 is **mostly feasible** with some caveats. Most critical dependencies support Python 3.13, but there are a few blockers.

## Key Findings

### ✅ Dependencies that support Python 3.13:
- **temporalio**: Full support (dropped Python 3.8, added 3.13)
- **uvloop 0.21.0**: Full support with cp313 wheels
- **numpy 2.0+**: Full support (requires 2.0 or higher)
- **FastAPI, Pydantic, and most other dependencies**: Compatible

### ❌ Blockers:
- **pytype**: Only supports Python 3.8-3.12, no 3.13 support yet
  - This is used for type checking in the development workflow

## Migration Plan

### 1. Update Python version constraints:
- `agents-api/pyproject.toml`: Change `requires-python = ">=3.12,<3.13"` to `requires-python = ">=3.12,<3.14"`
- `agents-api/.python-version`: Change from `3.12` to `3.13`
- `agents-api/Dockerfile`: Change `FROM python:3.12-slim` to `FROM python:3.13-slim`
- `agents-api/Dockerfile.worker`: Update similarly

### 2. Handle pytype incompatibility:
- **Option A**: Replace pytype with pyright (already in dev dependencies) for type checking
- **Option B**: Keep pytype but run it with Python 3.12 while running the service with 3.13
- **Option C**: Wait for pytype to add Python 3.13 support

### 3. Update other services for consistency:
- `integrations-service` uses same Python constraints (`>=3.12,<3.13`)
- `cli` service uses `>=3.11,<3.13`
- Both would need similar updates

### 4. Update CI/CD:
- GitHub Actions workflows use `uv python install` which respects `.python-version`
- Docker builds will automatically use new Python version
- No manual changes needed for workflows

### 5. Testing Plan:
- Run full test suite with Python 3.13
- Check for any deprecation warnings or compatibility issues
- Test Docker builds and deployments
- Verify all integration tests pass

## Recommendation
The migration is mostly trivial except for the pytype issue. I recommend proceeding with **Option A** (replacing pytype with pyright) since pyright is already in your dev dependencies and supports Python 3.13.

## Implementation Steps
1. Replace pytype with pyright in poe tasks
2. Update all Python version references
3. Run `uv sync` to update dependencies
4. Run full test suite
5. Update Docker images
6. Test in staging environment

## Estimated Effort
- Low complexity: Most changes are version string updates
- Main effort: Replacing pytype with pyright configuration
- Timeline: 1-2 hours of work + testing time