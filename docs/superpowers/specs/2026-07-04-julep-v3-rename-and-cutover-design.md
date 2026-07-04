# Julep 3 rename and cutover — design

**Date:** 2026-07-04
**Status:** Approved (design review with Diwank, 2026-07-04)

## Summary

Rename the `composable-agents` package to `julep`, make julep-ai/julep's `main` adopt this
repository's content and history (preserving the original product on a `v1` branch), publish
the framework to PyPI as `julep==3.0.0rc1`, and overhaul the README and docs-site under the
new **Julep 3** branding. Hard cutover: composable-agents has no users, and the old `julep`
SDK on PyPI sees only bot-level traffic (~10–30 downloads/day).

## Key decisions (with rationale)

| Decision | Choice | Why |
|---|---|---|
| PyPI version | `3.0.0rc1`, branded **Julep 3** | PyPI `julep` is already at 2.21.0 (155 SDK releases); `2.0.0` filenames are permanently burned (PyPI forbids filename reuse even after deletion). PEP 440 epochs (`1!2.0.0`) were rejected: bare specifiers default to epoch 0, so `julep==2.0.0` would never match, and the `1!` prefix is a permanent tax. Product branding follows the package: v3, not v2. |
| Old SDK releases | Yank all 155 | pip stops resolving them (the rc becomes the default pick with `--pre`); exact pins and lockfiles keep working with a warning. Reversible, unlike delete. |
| Rename depth | Full: import `julep`, dist `julep`, CLI `julep` | One coherent brand. No aliases, no compat shims — zero existing users. |
| `ca` CLI alias | Dropped | Hard cutover; one name in all docs. |
| New `main` history | This repo's full history | Real blame/bisect from day one. Cosmetic cost accepted: commit messages' `(#N)` references autolink to old julep PRs. |
| v1 issues/PRs | Bulk-close with migration note | Clean slate matches the reset story; pinned announcement explains. |
| composable-agents repo | Tombstone README, then archive | History and PRs #1–15 stay browsable forever. |
| Docs domain | docs.julep.ai cuts over; v1 docs archived | New fumadocs site takes the domain; the old Mintlify site remaps to v1.docs.julep.ai. |
| Cutover sequencing | Rename verified privately first, then ordered public flip | Approach A: every risky step happens after all gates are green locally; irreversible steps (PyPI) come last-but-one. |

## Current state (facts gathered 2026-07-04)

- This repo: local `julep-v2`, remote `julep-ai/composable-agents`. Package `composable-agents`
  1.1.0, import `composable_agents`, console scripts `composable-agents` (argparse inspection
  CLI, `cli.py`) and `ca` (Typer developer porcelain, `ca/cli.py`). 312 files mention
  "composable".
- julep-ai/julep: public, 6,602 stars, 973 forks, default branch `dev`, 122 open issues,
  82 branches, tags through `v1.0.0`, no `v1` branch. Description "Firebase for AI agents",
  homepage docs.julep.ai.
- PyPI `julep`: 2.21.0, 155 releases, last upload 2025-10-03, ~10–30 downloads/day
  (mirror-inclusive barely higher — bot noise). `2.0.0` and `2.1.0` exist, so those version
  numbers are unreclaimable.
- Docs: docs-site/ is fumadocs (Next.js static export) deployed via GitHub Pages
  (`.github/workflows/docs-pages.yml`). docs.julep.ai is a Mintlify site behind Vercel DNS
  (`cname.vercel-dns.com`).

## 1. Package rename (in this repo, verified before anything public)

- `git mv composable_agents/ julep/` (preserves blame), then sweep all imports and
  identifiers across package, tests, examples, scripts, infra manifests, `.ctx` prompts,
  docs, and CI workflows.
- `pyproject.toml`: `name = "julep"`, `version = "3.0.0rc1"`, URLs → julep-ai/julep,
  mypy `packages`/ruff excludes/package-data keys updated, and the self-referencing `dev`
  extra becomes `julep[test-no-temporal]`. The no-op `cli` extra (kept only for
  composable-agents back-compat) is dropped.
- Entry points: exactly one console script — `julep` → the current `ca` Typer porcelain
  (`run`/`lint`/`test`/`trace`/`deploy`/…). The argparse inspection CLI loses its console
  script but stays reachable as `python -m julep.cli`. `ca` and `composable-agents` scripts
  are removed.
- User-visible identifiers rename outright, no aliases (e.g. `ComposableAgentsError` →
  `JulepError`). Deploy-identity hashing includes package identifiers, so golden tests will
  churn — updated deliberately, not papered over (see the deploy-fn-shadows-module gotcha
  from PR #15).
- `__version__` continues to come from `importlib.metadata`, now resolving distribution
  `julep`.
- Gates: full pytest (~1710), `mypy --strict julep`, ruff, the temporal=off CI variant
  (its `test-no-temporal` extra reference updates too), plus a clean-venv wheel smoke test:
  `pip install dist/julep-*.whl`, `import julep`, `julep --help`.

## 2. Repo surgery (julep-ai/julep)

- Create `v1` branch at the current `dev` tip. Belt-and-braces: if a `main` branch exists,
  snapshot it (e.g. `v1-main`) before force-pushing.
- Push this repo's full history as the new `main`; switch the default branch `dev` → `main`;
  update branch protection to cover `main`.
- Existing tags (v0.x–v1.0.0) and the 82 old branches stay — v1 lineage, harmless.
- Repo description: replace "Firebase for AI agents" with the new positioning (§4);
  homepage stays docs.julep.ai.
- Bulk-close the 122 open issues and open PRs with a migration comment pointing at the
  `v1` branch and the announcement; pin a "Julep 3" announcement issue/discussion.
- This working copy's `origin` switches to `julep-ai/julep`.
- julep-ai/composable-agents: tombstone README ("now lives at julep-ai/julep"), then archive.

## 3. PyPI

- **Preflight (first, before anything irreversible):** confirm the julep-ai account owns the
  `julep` PyPI project and set up publishing (trusted publisher bound to julep-ai/julep, or
  an API token).
- Build sdist + wheel, `twine check`, publish `julep==3.0.0rc1`, then smoke test
  `pip install --pre julep` from a clean venv.
- Yank all 155 old SDK releases. PyPI has no official bulk-yank API — it is per-release via
  the web UI (a scriptable-but-unofficial endpoint exists). Fallback if bulk is painful:
  yank the 2.x releases pip would actually resolve; same effect on resolution.
- PyPI `composable-agents`: yank 1.0.0 and 1.1.0, update the project description to a
  pointer. No tombstone release — zero users.

## 4. README + docs-site overhaul

- **Positioning** (final wording to be settled during implementation review):
  *"Julep — durable, composable AI agents. Flows that crash and resume, retry safely, and
  explain every step."* Replaces the README title and the GitHub repo description.
- README: full rewrite — hero pitch, `pip install --pre julep` quickstart with renamed
  imports, feature tour, v1 pointer ("Looking for Julep v1? → `v1` branch /
  v1.docs.julep.ai").
- docs-site: rebrand site name and titles; every code sample and CLI invocation uses
  `julep`; add a "coming from v1" page (old search/blog links land on a different product).
- Hosting: stay on GitHub Pages (`docs-pages.yml` moves with the repo). Configure
  docs.julep.ai as the Pages custom domain on julep-ai/julep, flip DNS from Vercel/Mintlify
  to Pages, wait for the cert. Remap the Mintlify site to v1.docs.julep.ai. Custom 404 on
  the new site links to the v1 archive.

## 5. Cutover runbook (strict order)

1. Rename + overhaul lands in this repo; all gates green; wheel smoke-tested in a clean venv.
2. julep repo surgery: `v1` branch → push `main` → default-branch switch → protection.
3. PyPI: publish `julep==3.0.0rc1`; yank old `julep` releases; yank `composable-agents`.
4. Docs: deploy rebranded site; DNS cut docs.julep.ai → Pages; remap v1 docs.
5. Housekeeping: bulk-close issues/PRs, pinned announcement, repo description, archive
   composable-agents, switch local remotes.

## Risks

- **PyPI publishing rights on `julep`** is the one true unknown — verified in the preflight
  step before anything irreversible.
- DNS/cert propagation may leave docs briefly inconsistent (acceptable; no meaningful
  traffic).
- Commit-message `(#N)` autolinks point at old julep PRs — accepted cosmetic.
- Force-pushing `main` on a 6.6k-star repo is irreversible-ish for watchers' clones; the
  `v1` branch (created first) preserves everything.

## Non-goals

- The old JS/npm SDKs and other julep-ai v1 repos.
- The v1 hosted API product and its infrastructure.
- Deleting old branches on julep-ai/julep.
- Redirect maps for old docs deep-links (custom 404 + v1 archive link only).
- Compat shims/aliases for composable-agents imports or the `ca` CLI.
