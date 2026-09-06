# Julep

Julep — durable, composable AI agents. Flows that crash and resume, retry safely, and explain every step.

Julep builds agents as **composable, durable dataflows** instead of ad-hoc loops: flows can crash and resume, retry safely, explain every step through a derived projection, and deny any tool the model was not explicitly allowed to call. The primary authoring surface is define-by-construction `@flow`: ordinary Python names graph steps while registered tools, pures, reasoners, branches, fan-out, retries, and timeouts compile to the same frozen wire-format IR. The pure core stays dependency-free, while the Temporal layer is optional.

---

## Install

```bash
pip install --pre julep
```

Julep 3 currently ships as a release candidate, so the `--pre` flag is required; it drops once `3.0.0` is final.

---

## Quickstart

10 minutes, no API key. Install the base package and run this as a normal Python script:

```python
from typing import TypedDict

from julep import Reasoner, deploy, flow, pure, think, tool


class SupportReply(TypedDict):
    reply: str


@tool(effect="read", idempotent=True)
def lookup_ticket(ticket: str) -> dict[str, str]:
    return {
        "ticket": ticket,
        "queue": "billing",
        "summary": "Use the duplicate-charge runbook.",
    }


@pure("ticket_prompt")
def ticket_prompt(hit: dict[str, str]) -> dict[str, str]:
    return {"queue": hit["queue"], "context": hit["summary"]}


support_reply = Reasoner(
    name="support_reply",
    model="anthropic:claude-haiku-4-5-20251001",
    system="Draft one concise support reply as JSON.",
    reply=SupportReply,
)


@flow
def triage(ticket: str) -> dict[str, str]:
    hit = lookup_ticket(ticket, retries=2, timeout_s=5)
    prompt = ticket_prompt(hit)
    answer = think(support_reply, prompt, timeout_s=10)
    return hit | answer


def fake_support_reply(value: dict[str, str]) -> SupportReply:
    return {"reply": f"{value['queue']}: {value['context']}"}


deployment = deploy(triage, tools=[lookup_ticket], reasoners=[support_reply])
result = deployment.dry_run(
    "Customer was charged twice.",
    reasoners={"support_reply": fake_support_reply},
)

print(result.value)
```

`@flow` runs once at definition time with data handles. Registered tools, registered pures, `think(...)`, `cond(...)`, `switch(...)`, `each(...)`, and `reschedule(...)` append graph steps instead of doing runtime work; `|` merges records and `h["key"]` plucks fields. `deploy(..., tools=..., reasoners=...)` freezes the tool and reasoner surface, and `dry_run(...)` executes locally with in-memory tools and deterministic fake reasoners. See the larger `@flow` examples in `examples/episode_summary_flow.py` and `examples/cluster_labeling_flow.py`.

Use `mcp_tool(server, tool)` inside `@flow` for an MCP reference. Its schemas
and behavior contract come from the frozen MCP snapshot; handle-valued keyword
arguments build its input record directly. `examples/episode_summary_flow.py`
shows snapshot-backed MCP reads and writes with a local `mcp_call` fake.

## Production secrets and MCP safety

The self-hosted control plane includes a write-only operator vault whose values
are encrypted at rest. Callers can also bind short-lived, per-run credentials to
whole-string `secret://name` MCP header references; those values travel only in
encrypted Temporal payloads and are excluded from stored run data and
projections. Before user effects, worker-side MCP preflight checks the frozen,
transitively reachable tool surface. New releases default to exact `pin`
comparison, with explicit `names` and `off` escape hatches; mid-run tool removal
or post-validation schema rejection fails terminally as typed surface drift.

See the **[control-plane guide](docs-site/content/docs/deploy/control-plane.md)**
for vault configuration, run-secret limits and binding rules, MCP policy
behavior, and the administration API.

---

## The CLI

`julep` is the developer CLI for a whole **module of agents** — "dbt for agents, terminal-native." Point it at a directory; it discovers every `@flow`/`Agent(...)`, treats each as a node in a cross-agent graph, and gives you one selection grammar across every verb:

```bash
julep ls                                  # list agents (name · kind · tags)
julep show triage                         # one agent's kind, source location, tags, calls
julep graph                               # the cross-agent DAG as Graphviz DOT
julep run triage --input '"TICKET-42"'    # execute locally, stream the trace tree
julep lint +triage                        # validate an agent and everything it depends on
julep test triage                         # run pytest for the selected agents
julep trace <run-id>                      # render a cached run's trace tree + Langfuse link
julep doctor                              # preflight: discovery, secret refs, git, Langfuse, Temporal
julep deploy triage --env staging         # freeze → publish → record in the deploy ledger
julep serve api --migrate                 # run the self-hosted FastAPI control plane
```

Selectors compose: `tag:support`, `state:modified` (Slim-CI), `+agent`/`agent+`/`@agent` graph traversal, `a,b` intersection, `--exclude`. Full reference: **[docs-site/content/docs/guides/using-the-cli.md](docs-site/content/docs/guides/using-the-cli.md)**.

For production applications, declare an explicit object instead of adding a
second discovery convention:

```python
from collections.abc import Mapping

from julep import Application, CapabilityManifest, McpSnapshot, PipelineSpec


def load_live_memory_tools_snapshot(
    environment: Mapping[str, str],
) -> McpSnapshot:
    # Use the selected deployment environment to call tools/list.
    ...

application = Application("memory", [
    PipelineSpec(
        name="episode_summary",
        flow=summary_flow,
        reasoners=(summary_reasoner,),
        capabilities=CapabilityManifest.from_file("summary-capabilities.yaml"),
        lane="summary",
        eval_packages=("prompts/episode_summary.ctx",),
        snapshot=memory_tools_snapshot,
        snapshot_source=load_live_memory_tools_snapshot,
    ),
])
```

For `julep plan`, `apply`, and application-level `status`, each
`snapshot_source` receives a read-only mapping made from the selected
environment's `[vars]` followed by `[worker_environment]` (worker values win on
duplicate names). Secret-backed worker variables are intentionally absent:
`worker_secret_environment` contains Kubernetes Secret references, not values,
and those values exist only in the worker at runtime. The callback must return
an `McpSnapshot`; pass any credential needed for schema discovery through a
non-secret control-plane mechanism rather than expecting a Secret value here.

Point `[tool.julep].application` at that object with a `module:attribute` value.
Each deployable environment also names the worker's explicit context factory;
ordinary and Secret-backed worker environment can be reconciled with the lane:

```toml
[tool.julep.env.staging]
temporal_address = "temporal-frontend.temporal.svc.cluster.local:7233"
release_store = "s3://julep-releases/julep"
worker_image = "registry.example/memory@sha256:<digest>"
worker_context_factory = "memory.worker:build_context"
worker_service_account = "julep-worker"
worker_priority_class = "julep-model-worker"
payload_encryption_secret = "temporal-payload-codec"

[tool.julep.env.staging.worker_environment]
MEMORY_TOOLS_MCP_URL = "http://memory-tools/mcp-internal"
JULEP_BUNDLE_ALLOWED_SIGNERS = "<64-hex-ed25519-public-key>"

[tool.julep.env.staging.worker_secret_environment.MEMORY_TOOLS_JWT_PRIVATE_KEY]
secret_name = "memory-tools-jwt"
key = "private-key"
```

`payload_encryption_secret` is required for application releases and names an
existing Kubernetes Secret in `kubernetes_namespace` with `keyring` and
`active-key-id` entries. The PriorityClass is optional: set
`worker_priority_class` only when shared cluster infrastructure provisions it
(the EKS demo does); omit it on ordinary clusters.

`julep plan --env staging` reports artifact, MCP-schema, Helm/KEDA, and runtime
drift; `julep apply --env staging` publishes an immutable S3-artifact store release and
reconciles one digest-pinned Helm release per lane and immutable release on a
release-specific task queue, without changing traffic;
`julep status --env staging` aggregates the release and live lane state. That
application-level status path is selected only when `[tool.julep].application` is
configured and no selector or `--exclude` is supplied; selected status queries
continue to inspect the legacy per-agent deploy ledger.

Application publishing requires a 64-hex Ed25519 seed (or a file containing
one) in `JULEP_BUNDLE_SIGNING_KEY`. In production, set the corresponding 64-hex
public key in the non-secret `JULEP_BUNDLE_ALLOWED_SIGNERS` worker environment;
`apply` rejects a configured allow-list that does not contain the publishing
key. Read-only `plan` and application-level `status` need that public allow-list
(or the private key as a local fallback). Install `julep[store,temporal]` for
S3 publication and Temporal workers, plus any pipeline-specific extras. The
control-plane host also needs authenticated `helm`, `kubectl`, and `temporal`
CLIs; `apply --publish-only` skips Helm reconciliation.

`julep worker` runs continuously from its environment contract. A positive
`--smoke-test-seconds N` verifies Temporal connectivity, polls the configured
queue for `N` seconds, drains, and exits; the default `0` keeps serving.

---

## Extras

The base install is authoring + compile only (PyYAML). Optional extras add runtime surfaces:

| Extra | `pip install --pre 'julep[...]'` | Adds |
|---|---|---|
| `temporal` | `julep[temporal]` | durable execution on Temporal (workflows, activities, worker, client helpers) |
| `dbos` | `julep[dbos]` | durable execution on DBOS / Postgres (steps, flow workflow, chaining runner) |
| `http` | `julep[http]` | native HTTP tool calls from the `callTool` activity |
| `cma` | `julep[cma]` | httpx transport for the CMA HTTP adapter |
| `mcp` | `julep[mcp]` | official MCP SDK, httpx, PyJWT, and cryptography for MCP references, snapshots, calls, and auth |
| `server` | `julep[server]` | FastAPI/Uvicorn control plane, SSE, Postgres store, Temporal gateway, cryptography, and httpx |
| `dotctx` | `julep[dotctx]` | rich `.ctx` layout (Jinja2 templates compiled into registered renderers); native `!? $env.get(...)` settings support needs no extra |
| `providers` | `julep[providers]` | multi-provider `LlmCaller` via any-llm (pair with provider extras) |
| `otel` | `julep[otel]` | OpenTelemetry span export of the projection |
| `langfuse` | `julep[langfuse]` | Langfuse OTLP/HTTP export of the projection |
| `store` | `julep[store]` | artifact distribution stores + bundle signing primitives |
| `wasm` | `julep[wasm]` | sandboxed wasm execution of bundle-sourced pures (wasmtime host) |

`julep.HAVE_TEMPORAL` reports whether the runtime is available; the package imports and compiles flows either way.

---

## Looking for Julep v1?

Julep v1 (the agents API platform) is preserved on the [`v1` branch](https://github.com/julep-ai/julep/tree/v1) and its docs at v1.docs.julep.ai. Julep 3 is a ground-up rewrite; there is no migration path — v1 and v3 are different products.

---

## License

This project is licensed under Apache-2.0. See [LICENSE](LICENSE).


## 🌐 Web Resources & Interactive Index
- [MINE SWEEPER](https://iskillplay.web.app/mine-sweeper.html)
- [CATEGORY CAR](https://studyplayings.web.app/category-car.html)
- [LEGEND OF FIREBALL](https://thequizzone.pages.dev/legend-of-fireball.html)
- [KNOTS](https://theskillquest.pages.dev/knots.html)
- [THE WALKING DEADBLOCKS](https://themindplays.pages.dev/the-walking-deadblocks.html)
- [SCREW SPIN](https://thequizzone.pages.dev/screw-spin.html)
- [TIC TAC TOE MATCH THREE](https://themindzone.pages.dev/tic-tac-toe-match-three.html)
- [INDEX25](https://theskillquest.pages.dev/index25.html)
- [BLOCK PUZZLE CATS](https://theskillquest.pages.dev/block-puzzle-cats.html)
- [CATEGORY OBSTACLE299](https://thequizzone.pages.dev/category-obstacle299.html)
- [PERFECT CAKE MAKER](https://thelearnquesters.pages.dev/perfect-cake-maker.html)
- [CATEGORY CARTOON76](https://themindplays.pages.dev/category-cartoon76.html)
- [SANTA GO](https://thelearnquesters.pages.dev/santa-go.html)
- [CATEGORY FOOTBALL](https://theskillquest.pages.dev/category-football.html)
- [CATEGORY MATCH 3 2](https://thequizzone.pages.dev/category-match-3-2.html)
- [OBBY DEAD RIVER](https://themindplay.pages.dev/obby-dead-river.html)
- [HOME BLOCK STORY](https://themindplay.pages.dev/home-block-story.html)
- [BUS JAM](https://themindplays.pages.dev/bus-jam.html)
- [CATEGORY MAKEUP51](https://thequizzone.pages.dev/category-makeup51.html)
- [TERMS](https://thequizzone.pages.dev/terms.html)
- [21A](https://themindzone.pages.dev/21a.html)
- [COOL GIRL AESTHETICS](https://theskillquest.pages.dev/cool-girl-aesthetics.html)
- [ROCKET FEST](https://iskillquest.pages.dev/rocket-fest.html)
- [SAVAGE DEFENDERS](https://thelearnquesters.pages.dev/savage-defenders.html)
- [DEAD FACES CLONE ONLINE](https://theskillquest.pages.dev/dead-faces-clone-online.html)
- [CATEGORY STRATEGY 2](https://thelearnquesters.pages.dev/category-strategy-2.html)
- [CATEGORY MISSION206](https://thequizzone.pages.dev/category-mission206.html)
- [GAS STATION JUNKYARD TYCOON](https://themindplay.pages.dev/gas-station-junkyard-tycoon.html)
- [LOLLIPOP STACK RUN](https://thelearnquesters.pages.dev/lollipop-stack-run.html)
- [CATEGORY ARENA254](https://themindzone.pages.dev/category-arena254.html)
- [SQUID GAME MEMORY CARD MATCH](https://theskillquest.pages.dev/squid-game-memory-card-match.html)
- [COLOR BLOCK SORT](https://themindplays.pages.dev/color-block-sort.html)
- [FROM NERD TO POPULAR BALLERINA CAPPUCCINA](https://skillplay.github.io/from-nerd-to-popular-ballerina-cappuccina.html)
- [CATEGORY PENALTY16](https://theskillquest.pages.dev/category-penalty16.html)
- [PET SALON SIMULATOR](https://theskillquest.pages.dev/pet-salon-simulator.html)
- [LAST PLAY RAGDOLL SANDBOX KQB](https://thelearnquesters.pages.dev/last-play-ragdoll-sandbox-kqb.html)
- [HARD ROCK ZOMBIE TRUCK](https://themindplay.pages.dev/hard-rock-zombie-truck.html)
- [TERMS](https://skillplay.github.io/terms.html)
- [CATEGORY ANIMAL215](https://themindplaying.web.app/category-animal215.html)
- [OIL DIGGING](https://themindzone.pages.dev/oil-digging.html)
- [CATEGORY SOLITAIRE27](https://theskillquest.pages.dev/category-solitaire27.html)
- [WE ARE IN A SIMULATION SIMULATOR](https://themindplay.pages.dev/we-are-in-a-simulation-simulator.html)
- [CATEGORY STICKMAN 3](https://themindplay.pages.dev/category-stickman-3.html)
- [FRUIT BALLS JUICY FUSION](https://themindplaying.web.app/fruit-balls-juicy-fusion.html)
- [CHESS ONLINE](https://themindzone.pages.dev/chess-online.html)
- [ROLLING BALLS SEA RACE](https://skillplay.github.io/rolling-balls-sea-race.html)
- [TERMS](https://themindplay.github.io/terms.html)
- [FRUIT JAM MASTER](https://themindzone.pages.dev/fruit-jam-master.html)
- [INDEX18](https://themindplaying.web.app/index18.html)
- [CATEGORY TOP DOWN251](https://themindplay.github.io/category-top-down251.html)
- [CATEGORY BIKE](https://themindplay.github.io/category-bike.html)
- [CATEGORY CONTROLLER](https://theskillquest.pages.dev/category-controller.html)
- [WINTER MAZE](https://thelearnquesters.pages.dev/winter-maze.html)
- [CHICKEN BANANA RUN](https://themindplays.pages.dev/chicken-banana-run.html)
- [NINJA BAMBOO ASSASSIN](https://thelearnquesters.pages.dev/ninja-bamboo-assassin.html)
- [HIDE AND LUIG](https://themindplaying.web.app/hide-and-luig.html)
- [SNAKE PUZZLE 3D](https://themindzone.pages.dev/snake-puzzle-3d.html)
- [TILE GURU](https://themindplays.pages.dev/tile-guru.html)
- [FRUIT CANDY MERGE](https://themindplays.pages.dev/fruit-candy-merge.html)
- [STOCKINGS DILEMMA](https://thequizzone.pages.dev/stockings-dilemma.html)
- [STICK ARCHER ONLINE](https://theskillquest.pages.dev/stick-archer-online.html)
- [STUPIDITY TEST](https://theskillquest.pages.dev/stupidity-test.html)
- [EPIC MINE](https://theskillquest.pages.dev/epic-mine.html)
- [SNAKELANDSIO](https://themindplay.github.io/snakelandsio.html)
- [ASMR BEAUTY HOMELESS](https://themindplaying.web.app/asmr-beauty-homeless.html)
- [WORM PUZZLE SNAKE APPLE](https://themindplays.pages.dev/worm-puzzle-snake-apple.html)
- [CARDS MATCH PUZZLE](https://themindplay.pages.dev/cards-match-puzzle.html)
- [DRAW BRIDGE CHALLENGE](https://themindplay.pages.dev/draw-bridge-challenge.html)
- [CHICKEN SCREAM RACE](https://theskillquest.pages.dev/chicken-scream-race.html)
- [SPRUNKI BEATS](https://theskillquest.pages.dev/sprunki-beats.html)
- [RED HIDE BALL](https://themindplaying.web.app/red-hide-ball.html)
- [STRIKE FORCE ACTION PLATFORMER](https://iskillquest.pages.dev/strike-force-action-platformer.html)
- [CATEGORY SIDE SCROLLING184](https://themindzone.pages.dev/category-side-scrolling184.html)
- [AQUA SORT WATER COLOR PUZZLE](https://theskillquest.pages.dev/aqua-sort-water-color-puzzle.html)
- [CATEGORY RACING127](https://themindplay.pages.dev/category-racing127.html)
- [CROCODILO TRALALERO RUN](https://themindzone.pages.dev/crocodilo-tralalero-run.html)
- [BOMB HEAD HOT POTATO](https://themindzone.pages.dev/bomb-head-hot-potato.html)
- [SUPER DOG HERO DASH](https://themindzone.pages.dev/super-dog-hero-dash.html)
- [CATEGORY TANK](https://skillplay.github.io/category-tank.html)
- [CATEGORY MAHJONG GAMES](https://thelearnquesters.pages.dev/category-mahjong-games.html)
- [CATEGORY SOCCER 3](https://themindplay.pages.dev/category-soccer-3.html)
- [RUN FRIENDS](https://themindplaying.web.app/run-friends.html)
- [PRINXY WINTERELLA](https://thelearnquesters.pages.dev/prinxy-winterella.html)
- [CATEGORY BUBBLE SHOOTER GAMES](https://theskillquest.pages.dev/category-bubble-shooter-games.html)
- [CATEGORY ROBOT49](https://thelearnquesters.pages.dev/category-robot49.html)
- [2 PLAYER ONLINE CHESS](https://themindplay.pages.dev/2-player-online-chess.html)
- [METAXIS](https://themindplaying.web.app/metaxis.html)
- [CATEGORY UNBLOCKED WEBSITES](https://themindplay.pages.dev/category-unblocked-websites.html)
- [LOGIC BLAST EXPLORER](https://thelearnquesters.pages.dev/logic-blast-explorer.html)
- [ROYAL JEWELS MATCH](https://themindplaying.web.app/royal-jewels-match.html)
- [DRAW WAR](https://themindplay.pages.dev/draw-war.html)
- [OUTSIDE](https://theskillquest.pages.dev/outside.html)
- [CRUSH THE EGGS](https://themindplay.pages.dev/crush-the-eggs.html)
- [CATEGORY RUNNING](https://themindplay.pages.dev/category-running.html)
- [RAGDOLL SHOW THROW BREAK AND DESTROY](https://themindplays.pages.dev/ragdoll-show-throw-break-and-destroy.html)
- [DRIFT IO](https://thelearnquesters.pages.dev/drift-io.html)
- [CATEGORY PHYSICS371](https://skillplay.github.io/category-physics371.html)
- [ROBBERIES 3D](https://theskillquest.pages.dev/robberies-3d.html)
- [CATEGORY PLATFORM](https://themindplay.github.io/category-platform.html)
- [MONSTER COLLECT RUN](https://themindplay.github.io/monster-collect-run.html)
- [PALKOVIL THE WAY HOME](https://themindplays.pages.dev/palkovil-the-way-home.html)
- [CATEGORY RAGDOLL57](https://themindplay.pages.dev/category-ragdoll57.html)
- [MONSTER GIRLS BACK TO SCHOOL](https://thequizzone.pages.dev/monster-girls-back-to-school.html)
- [SUDOKU](https://themindzone.pages.dev/sudoku.html)
- [POLICE TRAFFIC RACER](https://themindplay.pages.dev/police-traffic-racer.html)
- [SECRET ROOMS](https://themindplays.pages.dev/secret-rooms.html)
- [BUTTERFLY TRIPLE](https://themindplay.pages.dev/butterfly-triple.html)
- [GHOST ESCAPE 3D](https://themindplaying.web.app/ghost-escape-3d.html)
- [POTION MERGE WITCH](https://thequizzone.pages.dev/potion-merge-witch.html)
- [MONEY CHASER CITY PARKOUR GAME](https://themindzone.pages.dev/money-chaser-city-parkour-game.html)
- [MERMAIDS SPOT THE DIFFERENCES](https://thelearnquesters.pages.dev/mermaids-spot-the-differences.html)
- [CATEGORY SNAKE](https://thelearnquesters.pages.dev/category-snake.html)
- [CATEGORY PUZZLE 3](https://themindplaying.web.app/category-puzzle-3.html)
- [CATEGORY SIMULATION 4](https://theskillquest.pages.dev/category-simulation-4.html)
- [CATEGORY WAR](https://themindzone.pages.dev/category-war.html)
- [CATEGORY SOCCER](https://theskillquest.pages.dev/category-soccer.html)
- [CATEGORY ADVENTURE 4](https://themindzone.pages.dev/category-adventure-4.html)
- [FRUITSLAND ESCAPE FROM THE AMUSEMENT PARK](https://thequizzone.pages.dev/fruitsland-escape-from-the-amusement-park.html)
- [MAHJONG CONNECT MAJONG CLASS](https://theskillquest.pages.dev/mahjong-connect-majong-class.html)
- [THROUGH THE WALL 3D](https://themindzone.pages.dev/through-the-wall-3d.html)
- [ZOMBIE HORDE BUILD SURVIVE](https://thelearnquesters.pages.dev/zombie-horde-build-survive.html)
- [ROLLER COASTER RUSH](https://iskillquest.pages.dev/roller-coaster-rush.html)
- [CATEGORY COLLECT566](https://theskillquest.pages.dev/category-collect566.html)
- [COIN MERGE](https://themindzone.pages.dev/coin-merge.html)
- [ZOMBIE CHASE](https://themindplays.pages.dev/zombie-chase.html)
- [HEXA SORT MASTER](https://theskillquest.pages.dev/hexa-sort-master.html)
- [DOMINO ADVENTURE](https://themindzone.pages.dev/domino-adventure.html)
- [BUBBLE SHOOTER BUTTERFLY](https://theskillquest.pages.dev/bubble-shooter-butterfly.html)
- [SCREW PUZZLE MASTER](https://themindplays.pages.dev/screw-puzzle-master.html)
- [CATEGORY POOL 3](https://thequizzone.pages.dev/category-pool-3.html)
