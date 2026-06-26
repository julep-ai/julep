# Docs-site consolidation — design & migration manifest

**Date:** 2026-06-26
**Goal:** Fold the existing `docs/` tree and the 16 generated `docs/matrix/` docs into a single,
well-organized Fumadocs site under `docs-site/`. Practical-first; theory quarantined in `internals/`.

## Reader profile

A Python developer who already builds agents and understands scaling challenges. They want to ship,
not read design rationale. The `start` / `guides` / `deploy` / `reference` sections must carry **zero
theory** — everything theoretical lives in `internals/`, reachable but off the main path.

## Decisions (locked with the user)

- **Format:** Fumadocs (Next.js + MDX) site in `docs-site/`, adapting jaunt's working scaffold
  (fumadocs-ui/core 16.5.0, fumadocs-mdx 14.2.6, next 16, tailwind 4, static `output: 'export'`).
- **Depth:** *Port + light edit.* Move existing/matrix content into MDX, fix links, merge where
  multiple sources map to one page, light prose cleanup. **No full rewrite.**
- **Existing docs:** Fold in, then `git rm` the superseded files. Delete `docs/matrix/` after folding.
- **Kept at root:** `README.md` and `CONTRIBUTING.md` (GitHub/PyPI front doors) — links repointed.
- **Prose quality:** apply jaunt's `natural-writing` rules (cut significance-inflation, AI vocabulary,
  trailing analysis; prefer plain `is`/`are`). Light touch only — do not rewrite working docs.

## Information architecture (approved)

```
content/docs/
  index.mdx          docs overview / map                (handwritten landing)
  start/             GET RUNNING — tutorial path, no theory
  guides/            HOW-TO — task-oriented
  deploy/            SHIP & SCALE — runtimes + operations
  reference/         LOOK IT UP — API + CLI + cheatsheet
  concepts/          UNDERSTAND IT — practical mental model
  internals/         THEORY — design rationale, the SPEC, the calculus
  development/        CONTRIBUTE
```

Top-level nav order: `index, start, guides, deploy, reference, concepts, internals, development`.

## Page manifest

Each content page is ported by one writer. `+` = merge multiple sources into one deduplicated page.
Landing pages (`*/index.mdx`, `meta.json`) are handwritten during scaffold.

| Destination (under `content/docs/`) | Source(s) | Notes |
|---|---|---|
| `start/install.mdx` | `docs/getting-started.md` (Install) + `README.md` install | extras table |
| `start/first-agent.mdx` | `docs/getting-started.md` (first agent → reading result → keyless → dev mode) | |
| `start/first-flow.mdx` | `README.md` quickstart + `docs/matrix/flow-frontend/readme.md` + `docs/AUTHORING.md` intro | the `@flow` triage tutorial |
| `start/next-steps.mdx` | `docs/getting-started.md` "Climb the ladder" + `docs/examples.md` pointers | link ladder |
| `guides/authoring-flows.mdx` | `docs/AUTHORING.md` + `docs/matrix/flow-frontend/readme.md` | the `@flow` surfaces |
| `guides/sessions.mdx` | `docs/sessions.md` + `docs/matrix/sessions/readme.md` | |
| `guides/capabilities-and-safety.mdx` | `docs/capabilities-and-safety.md` | |
| `guides/providers-and-resilience.mdx` | `docs/provider-resilience.md` + `docs/getting-started.md` (multi-provider) | |
| `guides/using-the-cli.mdx` | `docs/cli.md` + `docs/matrix/ca-cli/readme.md` + `docs/matrix/ca-cli/runbook.md` | task-flows incl. deploy/status/drift/trace |
| `guides/gotchas.mdx` | `docs/gotchas.md` + `docs/matrix/flow-frontend/runbook.md` | traps + flow troubleshooting |
| `guides/examples.mdx` | `docs/examples.md` | runnable examples index |
| `deploy/temporal.mdx` | `docs/deploy-temporal.md` | |
| `deploy/kubernetes.mdx` | `docs/deploy-kubernetes.md` | KEDA scaling |
| `deploy/dbos.mdx` | `docs/deploy-dbos.md` | |
| `deploy/operations.mdx` | `docs/matrix/composable-agents/runbook.md` + `docs/matrix/sessions/runbook.md` + `docs/temporal-ui-access.md` | worker ops · session ops · Temporal UI |
| `reference/python-api.mdx` | `docs/matrix/composable-agents/reference.md` | |
| `reference/flow-api.mdx` | `docs/matrix/flow-frontend/reference.md` | |
| `reference/sessions-api.mdx` | `docs/matrix/sessions/reference.md` | |
| `reference/ca-cli.mdx` | `docs/matrix/ca-cli/reference.md` | |
| `reference/cheatsheet.mdx` | `docs/cheatsheet.md` | |
| `concepts/model.mdx` | `docs/concepts.md` | typed flows, frozen IR, shapes, capabilities, projection |
| `concepts/architecture.mdx` | `docs/matrix/{composable-agents,flow-frontend,sessions,ca-cli}/architecture.md` | 4 subsections, system → flow → sessions → cli |
| `concepts/dispatch-boundary.mdx` | `docs/dispatch-boundary.md` | |
| `internals/specification.mdx` | `docs/SPEC.md` | normative |
| `internals/typed-flow-calculus.mdx` | `docs/design/typed-flow.md` + `docs/design/algebra.hs` | embed the `.hs` as a fenced block |
| `internals/durable-session-store.mdx` | `docs/design/durable-session-store.md` | |
| `internals/agent-loop-as-turn.mdx` | `docs/design/agent-loop-as-turn.md` | |
| `internals/agent-transcripts.mdx` | `docs/design/agent-transcripts.md` | |
| `internals/cma-runtime.mdx` | `docs/design/cma-runtime.md` | |
| `internals/prompt-fragments.mdx` | `docs/design/prompt-fragments.md` | |
| `internals/dotctx-format.mdx` | `docs/design/dotctx-rich-format.md` | |
| `internals/run-principal.mdx` | `docs/design/run-principal.md` | |
| `development/contributing.mdx` | `CONTRIBUTING.md` | keep root copy too |
| `development/team-guide.mdx` | `docs/team-guide.md` | |

34 ported pages + 8 section landings + docs home.

## MDX + link conventions (every porter must follow)

1. **Frontmatter** on every page:
   ```
   ---
   title: <Title Case page title>
   description: <one sentence, <=160 chars>
   ---
   ```
   The H1 is rendered from `title`; do **not** also start the body with an `#` H1.
2. **MDX safety:** MDX parses `{` as JS and `<...>` as JSX. In prose, wrap type hints / generics /
   comparisons in backticks (`` `dict[str, Any] | None` ``, `` `max < 5` ``) or escape (`\<`, `\{`).
   Code fences are safe — leave code as-is. Verify the page would compile as MDX.
3. **Internal links → absolute site routes.** Rewrite per this map:
   - `getting-started.md` → `/docs/start/first-agent`; install → `/docs/start/install`
   - `AUTHORING.md` → `/docs/guides/authoring-flows`
   - `sessions.md` → `/docs/guides/sessions`
   - `capabilities-and-safety.md` → `/docs/guides/capabilities-and-safety`
   - `provider-resilience.md` → `/docs/guides/providers-and-resilience`
   - `cli.md` → `/docs/guides/using-the-cli`
   - `gotchas.md` → `/docs/guides/gotchas`
   - `examples.md` → `/docs/guides/examples`
   - `cheatsheet.md` → `/docs/reference/cheatsheet`
   - `concepts.md` → `/docs/concepts/model`
   - `dispatch-boundary.md` → `/docs/concepts/dispatch-boundary`
   - `deploy-temporal.md` → `/docs/deploy/temporal`; `deploy-kubernetes.md` → `/docs/deploy/kubernetes`; `deploy-dbos.md` → `/docs/deploy/dbos`
   - `temporal-ui-access.md` → `/docs/deploy/operations`
   - `SPEC.md` → `/docs/internals/specification`
   - `design/typed-flow.md` & `design/algebra.hs` → `/docs/internals/typed-flow-calculus`
   - `design/durable-session-store.md` → `/docs/internals/durable-session-store`
   - `design/agent-loop-as-turn.md` → `/docs/internals/agent-loop-as-turn`
   - `design/agent-transcripts.md` → `/docs/internals/agent-transcripts`
   - `design/cma-runtime.md` → `/docs/internals/cma-runtime`
   - `design/prompt-fragments.md` → `/docs/internals/prompt-fragments`
   - `design/dotctx-rich-format.md` → `/docs/internals/dotctx-format`
   - `design/run-principal.md` → `/docs/internals/run-principal`
   - `team-guide.md` → `/docs/development/team-guide`; `CONTRIBUTING.md` → `/docs/development/contributing`
   - `docs/matrix/*` → drop the link or point at the merged destination above
4. **Links to source code** (`composable_agents/...`, `examples/...`, `tests/...`,
   `pyproject.toml`): link to `https://github.com/julep-ai/julep-v2/blob/main/<path>`.
5. **Last line** of every page: `{/* ported-by ca-docs-site: <section>/<page> */}` (MDX comment).
6. Keep all runnable code examples verbatim. Do not invent APIs.

## Scaffold (handwritten, deterministic)

Copy + rebrand jaunt's `docs-site/` config and app shell:
`source.config.ts`, `next.config.mjs`, `mdx-components.tsx`, `postcss.config.mjs`, `tsconfig.json`,
`lib/source.ts`, `lib/layout.shared.tsx`, `app/**`, `app/global.css`, `package.json`.
Rebrand: title "Composable Agents", GitHub `https://github.com/julep-ai/julep-v2`, home-page copy,
`NEXT_PUBLIC_GITHUB_*` to this repo, `docs-site/content/docs/` path in the "Edit on GitHub" link.

## Build & verify

```bash
cd docs-site
npm install
npm run build          # next build, static export to out/
npm run types:check    # fumadocs-mdx + next typegen + tsc --noEmit
```
Then: every internal link resolves to a real page; spot-check symbol/flag refs against the repo
(reuse the matrix verifier approach); the practical sections contain no design-rationale prose.

## Retirement (after build is green)

`git rm` the folded sources: `docs/*.md` (the flat files), `docs/design/*`, `docs/matrix/`, `docs/README.md`.
**Keep:** `README.md`, `CONTRIBUTING.md` (root), `docs/superpowers/` (process artifacts).
Repoint `README.md`'s docs links and `docs/README.md`-style index references at `docs-site/` /
the published site. (No git commit/push unless the user asks.)

{/* design artifact — not part of the published site */}
