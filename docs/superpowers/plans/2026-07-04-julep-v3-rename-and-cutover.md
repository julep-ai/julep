# Julep 3 Rename and Cutover Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This run executes via dynamic Workflow: opus@medium agents driving codex gpt-5.5@low (`codex exec --model gpt-5.5 ... < /dev/null`).

**Goal:** Rename composable-agents → julep 3.0.0rc1, make julep-ai/julep main adopt this repo (v1 preserved on a `v1` branch), publish the rc to PyPI, and rebrand README + docs-site as Julep 3.

**Architecture:** Two phases. Phase A is the in-repo rename, done and gate-verified privately (core rename first, then parallelizable disjoint-directory sweeps, then goldens + full gates + wheel smoke test). Phase B is the ordered public cutover (PyPI preflight → repo surgery → publish + yanks → docs → housekeeping); Phase B steps run from the orchestrator with `gh`/`uv`/`curl`, with the two irreversible-ish moments (force-push main, PyPI publish) taken only after their preflights pass.

**Tech Stack:** Python 3.12 / setuptools, uv (build + publish), gh CLI, GitHub Pages (fumadocs/Next.js static export), Temporal (unchanged).

**Spec:** `docs/superpowers/specs/2026-07-04-julep-v3-rename-and-cutover-design.md`

## Global Constraints

- New distribution name: `julep`; version: `3.0.0rc1`; import: `julep`; single console script: `julep` → the Typer porcelain (`julep.cli.main:main`). `ca` and `composable-agents` scripts are removed.
- The `julep/cli/` module path stays (internal, invisible to end users; minimal diff). The argparse inspection CLI stays reachable as `python -m julep.cli.artifact`.
- No compat aliases anywhere: `ComposableAgentsError` → `JulepError`, no re-export of old names, no `cli` extra.
- Brand casing in prose: "Julep" (product), "Julep 3" (this release). Positioning line: **"Julep — durable, composable AI agents. Flows that crash and resume, retry safely, and explain every step."**
- Gates (all must pass before Phase B): `python -m pytest` (~1710 tests), `uv run mypy --strict julep` (package only), `ruff check julep`, clean-venv wheel smoke test.
- Never touch: `composable_agents.egg-info/`, `build/`, `dist/`, `docs-site/node_modules/`, `docs-site/out/`, `__pycache__/` (stale artifacts; cleaned, not renamed).
- `codex exec` invocations MUST end with `< /dev/null` (hangs on stdin otherwise) and MUST use `--model gpt-5.5`.
- Commit after every task. Do not push to any remote during Phase A.

---

## Phase A — local rename (this repo)

### Task A1: Core rename — package dir, pyproject, version, errors, CI

**Files:**
- Rename: `composable_agents/` → `julep/` (git mv)
- Modify: `pyproject.toml`, `julep/__init__.py`, `julep/errors.py`, `.github/workflows/ci.yml`, `uv.lock` (regenerated)
- Delete: stale `composable_agents.egg-info/`, `build/`, `dist/`

**Interfaces:**
- Produces: importable package `julep`; distribution metadata name `julep` version `3.0.0rc1`; exception base `JulepError` (all former `ComposableAgentsError` subclasses now inherit from `JulepError`); console script `julep = "julep.cli.main:main"`. All later tasks assume these exact names.

- [ ] **Step 1: Move the package and clean stale artifacts**

```bash
git mv composable_agents julep
rm -rf composable_agents.egg-info build dist
```

- [ ] **Step 2: Rewrite pyproject.toml**

Apply exactly these changes (leave everything else as-is):

```toml
[project]
name = "julep"
version = "3.0.0rc1"
description = "Julep — durable, composable AI agents on Temporal."
keywords = ["agents", "llm", "temporal", "durable-execution", "mcp", "workflow", "julep"]

[project.optional-dependencies]
# ... all extras unchanged EXCEPT:
#   - DELETE the `cli = ["typer>=0.12"]` extra (was a composable-agents back-compat no-op)
#   - in `dev`, change "composable-agents[test-no-temporal]" -> "julep[test-no-temporal]"

[project.urls]
Repository = "https://github.com/julep-ai/julep"
Issues = "https://github.com/julep-ai/julep/issues"

[project.scripts]
julep = "julep.cli.main:main"
# DELETE the `composable-agents` and `ca` script lines

[tool.setuptools.packages.find]
include = ["julep*"]

[tool.setuptools.package-data]
julep = ["py.typed", "execution/_wasm/*.wasm"]

[tool.ruff]
extend-exclude = ["julep/execution/_wasm/wasi_wheels"]

[tool.ruff.lint.per-file-ignores]
"julep/__init__.py" = ["F401"]

[tool.mypy]
packages = ["julep"]
exclude = '(^|/)julep/execution/_wasm/'

[[tool.mypy.overrides]]
module = ["julep.execution.*"]   # was composable_agents.execution.*
# ...
[[tool.mypy.overrides]]
module = ["julep"]               # was composable_agents
# ...
```

- [ ] **Step 3: Sweep the package source**

Inside `julep/` only (74 files mention the old name):

```bash
grep -rl 'composable_agents' julep/ | xargs sed -i 's/composable_agents/julep/g'
grep -rl 'composable-agents' julep/ | xargs sed -i 's/composable-agents/julep/g'
grep -rln 'ComposableAgentsError' julep/ | xargs sed -i 's/ComposableAgentsError/JulepError/g'
```

Then hand-fix prose: `grep -rn 'Composable Agents\|Composable Serverless\|composable agents' julep/` and rewrite each hit as "Julep" (docstrings, help text, comments). In `julep/__init__.py` the version lookup must read:

```python
__version__ = _distribution_version("julep")
```

In `julep/errors.py` the base class docstring should describe Julep, and the class line must be exactly `class JulepError(Exception):`.

Do NOT sed `julep/execution/_wasm/wasi_wheels/` (vendored upstream); verify with `git diff --stat -- julep/execution/_wasm/wasi_wheels` → empty.

- [ ] **Step 4: Update CI workflows**

`.github/workflows/ci.yml`: replace every `composable_agents` with `julep` (ruff target, mypy target, both `import composable_agents as c` assert lines → `import julep as c`). `docs-pages.yml` needs no change (paths only).

- [ ] **Step 5: Regenerate lockfile and verify import**

```bash
uv lock
uv sync --extra dev
python -c "import julep; print(julep.__version__)"
```

Expected: `3.0.0rc1`.

- [ ] **Step 6: Package-only gates**

```bash
ruff check julep
uv run mypy --strict julep
```

Expected: both clean. (Full pytest deferred to A2 — tests still import the old name.)

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "rename: composable_agents -> julep, 3.0.0rc1 (core package + pyproject + CI)"
```

### Task A2: Tests sweep + deploy-identity goldens

**Files:**
- Modify: everything under `tests/` (202 files mention the old name)

**Interfaces:**
- Consumes: package `julep`, `JulepError`, dist name `julep` from A1.
- Produces: full pytest suite green against the renamed package.

- [ ] **Step 1: Mechanical sweep**

```bash
grep -rl 'composable_agents' tests/ | xargs sed -i 's/composable_agents/julep/g'
grep -rl 'composable-agents' tests/ | xargs sed -i 's/composable-agents/julep/g'
grep -rl 'ComposableAgentsError' tests/ | xargs sed -i 's/ComposableAgentsError/JulepError/g'
```

Then `grep -rin 'composable' tests/` and hand-fix remaining prose/fixture hits (e.g. "Composable Agents" in .ctx fixtures, expected help text, service names).

- [ ] **Step 2: Run the suite; fix goldens deliberately**

```bash
python -m pytest
```

Expected first run: failures concentrated in deploy-identity/golden-hash tests (identity hashing includes package identifiers — see PR #15's deploy-fn-shadows-module gotcha: `deploy` the function shadows `deploy` the module in some scopes). For each failing golden: read the assertion, confirm the delta is exactly the rename (module path or dist-name string inside the hashed payload), then update the golden to the newly computed value. Do NOT loosen assertions or hash inputs.

- [ ] **Step 3: Full gates**

```bash
python -m pytest && ruff check julep tests && uv run mypy --strict julep
```

Expected: ~1710 passed; clean; clean.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "rename: sweep tests + update deploy-identity goldens for julep"
```

### Task A3: Sweep examples, scripts, infra, tooling, spikes

**Files:**
- Modify: `examples/` (17 files), `scripts/` (1), `infra/` (1), `tooling/` (12), `spikes/` (8), `TODOS.md`

**Interfaces:**
- Consumes: package `julep`, CLI `julep` from A1.

- [ ] **Step 1: Mechanical sweep + hand-fix**

Same three seds as A2 Step 1 over `examples/ scripts/ infra/ tooling/ spikes/ TODOS.md`, then `grep -rin 'composable\|[^a-z]ca ' examples/ scripts/ infra/ tooling/ spikes/` and hand-fix: prose → "Julep", CLI invocations `ca run` → `julep run` (etc.), image/deployment names in infra manifests → `julep-worker` style, k8s labels included.

- [ ] **Step 2: Verify examples still parse**

```bash
python -m compileall -q examples/ spikes/ tooling/ && python -m pytest -q -k example 2>/dev/null | tail -2
```

Expected: no compile errors; any example-marked tests pass.

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "rename: sweep examples/scripts/infra/tooling/spikes to julep"
```

### Task A4: Sweep docs/ + CONTRIBUTING

**Files:**
- Modify: `docs/` (23 files, incl. plans — historical plans get import/CLI references updated ONLY where they'd mislead a reader running commands today; leave historical narrative intact), `CONTRIBUTING.md`

- [ ] **Step 1: Sweep current-truth docs**

`CONTRIBUTING.md` and any non-plan docs: full rename sweep (imports, dist name, CLI, prose brand). For `docs/plans/*` and `docs/superpowers/*`: do NOT rewrite history; only add nothing, change nothing except this plan/spec pair which already uses the new names.

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "rename: sweep CONTRIBUTING + current docs to julep"
```

### Task A5: README rewrite

**Files:**
- Rewrite: `README.md`

**Interfaces:**
- Consumes: positioning line from Global Constraints; renamed quickstart imports from A1.

- [ ] **Step 1: Rewrite README.md with this structure**

1. `# Julep` + the positioning line as the first paragraph, then one paragraph expanding it (composable durable dataflows, not ad-hoc loops; crash/resume, safe retries, derived projection explains every step, deny-by-default tools; `@flow` define-by-construction; pure core dependency-free, Temporal optional).
2. `## Install` — `pip install --pre julep` (note: rc; final 3.0.0 drops the flag).
3. `## Quickstart` — port the existing 10-minute no-API-key example verbatim but with `from julep import Reasoner, deploy, flow, pure, think, tool`.
4. `## The CLI` — `julep ls | show | graph | run | lint | test | trace | doctor | deploy` one-liner each (source: current ca docs).
5. `## Extras` — table of pip extras (temporal, dbos, http, dotctx, yglu, providers, otel, langfuse, store, wasm).
6. `## Looking for Julep v1?` — exactly: "Julep v1 (the agents API platform) is preserved on the [`v1` branch](https://github.com/julep-ai/julep/tree/v1) and its docs at v1.docs.julep.ai. Julep 3 is a ground-up rewrite; there is no migration path — v1 and v3 are different products."
7. `## License` — Apache-2.0.

- [ ] **Step 2: Verify no stale references and commit**

```bash
grep -in 'composable\|[^a-z]ca[^a-z]' README.md
git add README.md && git commit -m "docs: rewrite README for Julep 3"
```

Expected grep: no hits.

### Task A6: docs-site rebrand

**Files:**
- Modify: `docs-site/content/docs/**` (39 files mention the old name), `docs-site/app/**` (site title/layout), `docs-site/package.json` (name → `julep-docs`)
- Create: `docs-site/content/docs/coming-from-v1.mdx`

- [ ] **Step 1: Sweep content**

Same three seds over `docs-site/content docs-site/app docs-site/lib docs-site/package.json` (NOT node_modules/out), then hand-fix prose brand ("Composable Agents" → "Julep"), site title/metadata in `docs-site/app/layout.tsx` and the home page, and every CLI sample `ca ...` → `julep ...`, every install snippet → `pip install --pre julep`.

- [ ] **Step 2: Add the coming-from-v1 page**

`docs-site/content/docs/coming-from-v1.mdx`: frontmatter title "Coming from Julep v1"; body covers — v1 = hosted agents-API platform, v3 = open-source durable-agents framework; no migration path; v1 code on the `v1` branch; v1 docs at v1.docs.julep.ai; why the reset (one paragraph, honest). Register it in the section `meta.json`.

- [ ] **Step 3: Build and verify**

```bash
cd docs-site && npm ci && npm run build && cd ..
grep -rin 'composable' docs-site/content docs-site/app | grep -v node_modules
```

Expected: build succeeds; grep empty.

- [ ] **Step 4: Commit**

```bash
git add docs-site && git commit -m "docs-site: rebrand to Julep 3 + coming-from-v1 page"
```

### Task A7: Full gates + wheel smoke test (exit gate for Phase A)

- [ ] **Step 1: Whole-tree stale-name audit**

```bash
grep -rn 'composable' --include='*.py' --include='*.toml' --include='*.yml' --include='*.md' --include='*.mdx' --include='*.ctx' . \
  | grep -vE 'node_modules|/out/|egg-info|__pycache__|uv.lock|docs/plans/|docs/superpowers/|wasi_wheels|package-lock'
```

Expected: zero lines. Any hit is a bug in A1–A6 — fix it there.

- [ ] **Step 2: Full gates**

```bash
python -m pytest && ruff check julep tests && uv run mypy --strict julep
```

Expected: all green.

- [ ] **Step 3: Build + clean-venv smoke test**

```bash
uv build
python -m venv /tmp/julep-smoke && /tmp/julep-smoke/bin/pip -q install dist/julep-3.0.0rc1-py3-none-any.whl
/tmp/julep-smoke/bin/python -c "import julep; print(julep.__version__)"
/tmp/julep-smoke/bin/julep --help
/tmp/julep-smoke/bin/python -m julep.cli.artifact --help
```

Expected: `3.0.0rc1`; porcelain help listing run/lint/deploy…; inspection CLI help. Also `twine check dist/*` (or `uv publish --check-url` equivalent) → PASSED.

- [ ] **Step 4: Commit anything outstanding**

```bash
git status --short   # expect only dist/ artifacts (untracked, fine)
```

---

## Phase B — public cutover (orchestrator-run, strict order)

### Task B1: PyPI preflight (BLOCKING — nothing irreversible before this passes)

- [ ] **Step 1:** Verify the julep-ai PyPI account owns project `julep` (web UI: pypi.org/manage/project/julep/ loads). Confirm `UV_PUBLISH_TOKEN` scope covers `julep` (account-scoped token, or mint a project-scoped one). If ownership/token fails → STOP, report to Diwank.
- [ ] **Step 2:** Dry-run credential check without uploading: `uv publish --dry-run 2>/dev/null || twine upload --repository testpypi dist/* --skip-existing` is NOT reliable for name `julep` on TestPyPI; instead rely on Step 1's UI check + `twine check dist/*` from A7.

### Task B2: julep-ai/julep repo surgery

- [ ] **Step 1: Preserve v1 (server-side, no 90MB clone)**

```bash
DEV_SHA=$(gh api repos/julep-ai/julep/branches/dev --jq .commit.commit.tree.sha >/dev/null 2>&1; gh api repos/julep-ai/julep/branches/dev --jq .commit.sha)
gh api repos/julep-ai/julep/git/refs -f ref=refs/heads/v1 -f sha="$DEV_SHA"
# if a `main` branch exists, snapshot it too:
MAIN_SHA=$(gh api repos/julep-ai/julep/branches/main --jq .commit.sha 2>/dev/null) \
  && gh api repos/julep-ai/julep/git/refs -f ref=refs/heads/v1-main -f sha="$MAIN_SHA"
```

Verify: `gh api repos/julep-ai/julep/branches/v1 --jq .name` → `v1`.

- [ ] **Step 2: Push our history as main**

```bash
git remote add julep git@github.com:julep-ai/julep.git
git push julep main:refs/heads/main --force
```

- [ ] **Step 3: Flip default branch + description**

```bash
gh api -X PATCH repos/julep-ai/julep -f default_branch=main
gh repo edit julep-ai/julep --description "Julep — durable, composable AI agents. Flows that crash and resume, retry safely, and explain every step." --homepage "https://docs.julep.ai"
```

Verify: `gh repo view julep-ai/julep --json defaultBranchRef,description`.

- [ ] **Step 4: Branch protection** — if `dev` had a protection rule, replicate a minimal one on `main` (`gh api repos/julep-ai/julep/branches/dev/protection` to inspect; skip silently on 404).

### Task B3: PyPI publish + yanks

- [ ] **Step 1: Publish**

```bash
uv publish   # uses UV_PUBLISH_TOKEN; dist/ from A7
```

- [ ] **Step 2: Smoke test from PyPI**

```bash
python -m venv /tmp/julep-pypi && /tmp/julep-pypi/bin/pip install --pre julep
/tmp/julep-pypi/bin/python -c "import julep; print(julep.__version__)"   # 3.0.0rc1
/tmp/julep-pypi/bin/julep --help
```

- [ ] **Step 3: Yank all 155 old julep releases.** No official bulk API: script the web UI (session cookie + per-release yank form POST), or use chrome-devtools automation with Diwank's login. Verify afterwards: `pip install julep` (no --pre) in a fresh venv → "no matching distribution" (all finals yanked, rc requires --pre). Fallback if automation stalls: yank all 2.x + 1.x finals first (what pip would actually resolve), finish the tail manually.
- [ ] **Step 4: Yank composable-agents 1.0.0 + 1.1.0** (pypi.org/manage/project/composable-agents/). No tombstone upload; the archived GitHub repo is the pointer.

### Task B4: Docs deploy + domain cutover

- [ ] **Step 1:** Enable GitHub Pages on julep-ai/julep (Settings → Pages → source "GitHub Actions" — manual; `docs-pages.yml`'s own comment says default token can't do it). Then `gh workflow run docs-pages.yml -R julep-ai/julep` and confirm deploy job green.
- [ ] **Step 2:** Set custom domain `docs.julep.ai` on the Pages settings; add DNS CNAME `docs.julep.ai → julep-ai.github.io` at the DNS provider (currently `cname.vercel-dns.com` — manual, Diwank's dashboard); wait for cert.
- [ ] **Step 3:** Remap the old Mintlify site to `v1.docs.julep.ai` (Mintlify dashboard + DNS CNAME — manual). Verify old site reachable there, new site at docs.julep.ai.

### Task B5: Housekeeping

- [ ] **Step 1: Pinned announcement** — create issue "Julep 3: ground-up rewrite now on main" on julep-ai/julep (body: what changed, v1 branch pointer, v1.docs link, rc install command); `gh api ... /pin` it.
- [ ] **Step 2: Bulk-close the 122 open issues + open PRs**

```bash
NOTE="Julep's main branch is now Julep 3, a ground-up rewrite (see the pinned announcement). v1 is preserved on the v1 branch and v1.docs.julep.ai. Closing v1-era items; please re-file against v3 if still relevant."
gh issue list -R julep-ai/julep --state open --limit 200 --json number -q '.[].number' \
  | while read -r n; do gh issue close "$n" -R julep-ai/julep -c "$NOTE"; sleep 2; done
gh pr list -R julep-ai/julep --state open --limit 100 --json number -q '.[].number' \
  | while read -r n; do gh pr close "$n" -R julep-ai/julep -c "$NOTE"; sleep 2; done
```

(sleep guards secondary-rate-limits; announcement issue must be created first and excluded.)

- [ ] **Step 3: Tombstone + archive composable-agents** — push a final commit to julep-ai/composable-agents replacing README.md with "# composable-agents → Julep\n\nThis project is now [Julep 3](https://github.com/julep-ai/julep) (`pip install --pre julep`). Full history preserved here read-only."; then `gh repo archive julep-ai/composable-agents -y`.
- [ ] **Step 4: Local remotes** — `git remote set-url origin git@github.com:julep-ai/julep.git; git remote remove julep`. Optionally rename the working dir to `~/github.com/julep-ai/julep` (session-external; do last).
- [ ] **Step 5: Memory + verification sweep** — `pip install --pre julep` fresh-venv check one more time; docs.julep.ai serves Julep 3; repo main renders new README; update project memory.

## Execution notes for the Workflow run

- A1 → A2 are strictly sequential. A3, A4, A5, A6 touch disjoint paths and run in parallel after A1 (they don't need A2). A7 barriers on all of A2–A6.
- Phase B is orchestrator-only (credentials, gh auth, human dashboards); do NOT hand B-tasks to codex agents. B1 gates B2–B5; B2 precedes B3 (repo URL in published metadata must be live); B4/B5 close it out.
- Manual/human moments: PyPI web UI ownership check + yanks (2FA), Pages enablement, DNS + Mintlify dashboards.
