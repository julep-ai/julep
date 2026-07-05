---
title: "Contributing"
description: "Development setup, CI checks, golden corpus rules, and pull request expectations."
---

## Project layout

`julep` is a Python package for authoring typed, durable, capability-bounded agent flows that compile to a frozen JSON IR. Use the [README module map](/docs#module-map) for the package layout and [Concepts](/docs/concepts/model) for the conceptual model.

## Dev setup

```bash
git clone https://github.com/julep-ai/julep-v2
cd julep-v2
python -m pip install -e '.[dev]'
```

The package requires Python 3.12 or newer (see `pyproject.toml`). CI tests Python 3.12.

The published package name is `julep`. The console entry point is:

```bash
julep
```

## Running the checks

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

## The golden corpus is a contract

`tests/golden/` pins the golden corpus as the cross-language wire-format contract. The committed `tests/golden/golden_hashes.json` values are expected to change only when the IR, manifest JSON, diagnostics, shape projection, or snapshot hashing changes intentionally.

A pull request that moves a pin must be deliberate and explained. Regenerate the corpus only for an intentional wire-format change:

```bash
python -m tests.golden.regenerate --update
```

Review the resulting `tests/golden/golden_hashes.json` diff as part of the format change. If a pin moves unexpectedly, stop and investigate before continuing.

## Testing norm

The [specification](/docs/internals/specification) defines conformance in terms of tested invariants: an item is conformant only when its invariant holds in code with a test. A change is done when the behavior is implemented and the relevant tests have been added or adjusted with it.

## Style

`ruff` and `mypy` must be clean. Match the surrounding code and keep public APIs typed. The pure core must stay free of any `temporalio` import; only modules under `julep/execution/` may import it.

## Pull requests

Keep pull requests focused. Ensure all CI gates are green. Describe what changed, why it changed, and any intentional golden corpus movement.

<!-- ported-by ca-docs-site: development/contributing -->
