# Contributing

## Project layout

`julep` is a Python package for authoring typed, durable, capability-bounded agent flows that compile to a frozen JSON IR. Use the [README module map](README.md#module-map) for the package layout and [docs-site/content/docs/concepts/model.md](docs-site/content/docs/concepts/model.md) for the conceptual model.

## Dev setup

```bash
git clone https://github.com/julep-ai/julep
cd julep
uv sync --extra dev
```

The `dev` extra installs everything the full suite needs, including the Temporal E2E dependencies. Use `uv sync --extra test-no-temporal` to reproduce the no-Temporal CI matrix variant.

The package requires Python 3.12 or newer (see `pyproject.toml`). CI tests Python 3.12.

The published package name is `julep`. The console entry point is:

```bash
julep
```

## Running the checks

The canonical local commands are:

```bash
uv run pytest
uv run ruff check julep tests
uv run mypy julep
```

`uv run pytest` and `uv run python -m pytest` are equivalent: `pythonpath = ["."]` in `pyproject.toml` puts the repo root on `sys.path` for both, so tests that import `examples` or `scripts` collect either way. `addopts` already applies `-m 'not live'`; tests marked `live` or `provider_smoke` make billable network calls and are opt-in.

## Test isolation

`DEFAULT_REGISTRY` is a process-global singleton. An autouse fixture in `tests/conftest.py` snapshots and restores its mappings around every test, so the suite must pass in any order and in any subset. Registrations done at module import time survive; registrations done inside a test are rolled back. Each test must register the reasoners, pures, and renderers it needs rather than relying on state left behind by an earlier test.

## What CI runs

CI runs lint and type checks on Python 3.12:

```bash
python -m pip install -e '.[dev]'
ruff check julep
python -m mypy --no-incremental --cache-dir=/dev/null julep
```

CI runs tests on Python 3.12 with Temporal absent:

```bash
python -m pip install -e . pytest
python -c "import julep as c; assert c.HAVE_TEMPORAL is False"
python -m pytest -q
```

CI also runs tests on Python 3.12 with Temporal present:

```bash
python -m pip install -e '.[dev]'
python -c "import julep as c; assert c.HAVE_TEMPORAL is True"
python -m pytest -q
```

Pass `-m live` explicitly to opt into the live provider tests.

## The golden corpus is a contract

`tests/golden/` pins the golden corpus as the cross-language wire-format contract. The committed `tests/golden/golden_hashes.json` values are expected to change only when the IR, manifest JSON, diagnostics, shape projection, or snapshot hashing changes intentionally.

A pull request that moves a pin must be deliberate and explained. Regenerate the corpus only for an intentional wire-format change:

```bash
python -m tests.golden.regenerate --update
```

Review the resulting `tests/golden/golden_hashes.json` diff as part of the format change. If a pin moves unexpectedly, stop and investigate before continuing.

## Replay corpus and worker versioning

`tests/replay/histories/*.json` is a Temporal replay gate over all six registered workflows. `tests/replay/test_replay_corpus.py` replays each recorded history at HEAD so nondeterministic workflow changes fail before they ship.

A corpus failure means a nondeterministic workflow change. Fix it either by gating the change behind `workflow.patched("<ticket>")` and re-recording the corpus only once the deprecation window closes, or by shipping under a new Build ID with worker versioning enabled. Regenerate corpus histories only in the same PR that adds a patched gate or intentionally bumps the versioning story, never just to "fix the test".

Regenerate the corpus with:

```bash
uv run python tests/replay/record_histories.py
```

Build-ID / worker versioning is opt-in and off by default because versioned task queues need Temporal server support. Workers read `JULEP_WORKER_BUILD_ID` and `JULEP_WORKER_VERSIONING=1` through `WorkerServeSettings.from_env`; when versioning is on without an explicit build id, the worker defaults to the package version.

## Testing norm

The [specification](docs-site/content/docs/internals/specification.md) defines conformance in terms of tested invariants: an item is conformant only when its invariant holds in code with a test. A change is done when the behavior is implemented and the relevant tests have been added or adjusted with it.

Regression tests live under `tests/`, mirroring the module under test: `tests/test_<module>.py` for library modules, `tests/cli/` for CLI behavior, `tests/invariants/` for repo-wide invariant checks. Every bug fix gets a test that fails before the fix.

## Style

`ruff` and `mypy` must be clean. Match the surrounding code and keep public APIs typed. The pure core must stay free of any `temporalio` import; only modules under `julep/execution/` may import it.

## Pull requests

Keep pull requests focused. Ensure all CI gates are green. Describe what changed, why it changed, and any intentional golden corpus movement.
