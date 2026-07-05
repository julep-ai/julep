# P1(b) CAS Bundle Round Trip Learnings

Reproduce:

```bash
uv run python spikes/cas_bundle/runner.py
```

The spike stores run artifacts under `spikes/cas_bundle/.cas/`, which is ignored by the local
`.gitignore`.

## Final Bundle Manifest Shape

The P1 runner uses canonical JSON and stores the manifest itself in the CAS. The digest from the
latest run was:

```text
fbffa1ffee6c05e840aaed8febe06beaca6593d4e1cb51c5bcbec3a2505d5d64
```

Real manifest JSON from that run:

```json
{
  "artifactComponents": "8d90700c10d82627f8139e7d7b514cc0a9f1e5bc3616fdebd8332fdbd86e860e",
  "artifactHash": "sha256:8d90700c10d82627f8139e7d7b514cc0a9f1e5bc3616fdebd8332fdbd86e860e",
  "flow": "8a8d04b6cda2a83595d164b0369d40e3902b836cb6b3317d919f6bfbbd103261",
  "pures": [
    {
      "abi": "python-source/json-v1",
      "name": "cas.normalize_input.v1",
      "source": "aaeedfb2aff9aaef2900a7ad1024b5451fe2dbd5dd368318fe6f05e6eec96935",
      "sourceHash": "pure:aaeedfb2aff9aaef"
    },
    {
      "abi": "python-source/json-v1",
      "name": "cas.render_summary.v1",
      "source": "5d2ec7b9a63caa7bd8e3fa687b13b8d1bdaa1f8577fad19b8737caa72436e3b9",
      "sourceHash": "pure:5d2ec7b9a63caa7b"
    }
  ],
  "signature": null
}
```

P1 added two practical lookup fields to the requested draft:

- `flow`: full CAS digest for canonical `flowJson`.
- `artifactComponents`: full CAS digest for the canonical artifact envelope used to verify
  `artifactHash` and the published `pureSourceHashes` pins in the worker.

The fixed fields are present: `artifactHash`, per-pure `name` / `sourceHash` / `source` / `abi`,
and `signature: null`. `envHash` is absent in P1.

Hash namespaces used in the manifest:

- CAS addresses are full sha256 hex over blob bytes.
- Registry pins are `pure:` plus the first 16 hex chars of sha256 over exact source text.

`abi = "python-source/json-v1"` means the source blob is Python source for a decorated pure whose
call boundary is JSON-compatible values in and JSON-compatible values out.

## pureRuntimeRefs Envelope

Real envelope JSON from the run:

```json
{
  "cas.normalize_input.v1": {
    "abi": "python-source/json-v1",
    "bundleHash": "fbffa1ffee6c05e840aaed8febe06beaca6593d4e1cb51c5bcbec3a2505d5d64",
    "executorTier": "wasm",
    "sourceHash": "pure:aaeedfb2aff9aaef"
  },
  "cas.render_summary.v1": {
    "abi": "python-source/json-v1",
    "bundleHash": "fbffa1ffee6c05e840aaed8febe06beaca6593d4e1cb51c5bcbec3a2505d5d64",
    "executorTier": "wasm",
    "sourceHash": "pure:5d2ec7b9a63caa7b"
  }
}
```

`envHash` is absent when unset.

## B1 Confirmation: Artifact Envelope Join

`julep/deploy.py:229-249` builds `Deployment.artifact_components`. It includes
`flowJson`, `manifestJson`, `pureSourceHashes`, `reasoners`, `capabilities`, `executionPolicy`, and
`frameworkVersion`. `rendererSourceHashes` is the existing absent-when-unset precedent:
`deploy.py:246-248` computes renderer hashes and only adds the key when the dict is non-empty.

`julep/deploy.py:251-255` hashes the envelope with:

```python
payload = canonical_json(self.artifact_components)
digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
return f"sha256:{digest}"
```

The spike simulates P2 with:

```python
def join_pure_runtime_refs(components, refs):
    joined = dict(components)
    if refs:
        joined["pureRuntimeRefs"] = refs
    return joined
```

Byte-identity proof from the runner:

```text
deployment.artifact_hash = sha256:8d90700c10d82627f8139e7d7b514cc0a9f1e5bc3616fdebd8332fdbd86e860e
refs absent            = sha256:8d90700c10d82627f8139e7d7b514cc0a9f1e5bc3616fdebd8332fdbd86e860e
refs empty             = sha256:8d90700c10d82627f8139e7d7b514cc0a9f1e5bc3616fdebd8332fdbd86e860e
refs present           = sha256:ef4e28d348fa69ecfeba181de4b83f046ef439a03f29b5304cb2f38aea3352cc
```

Conclusion: `pureRuntimeRefs` can join `artifact_components` with zero impact when absent or empty,
and it changes identity when present.

## Registration From Source Finding

`julep/registry.py:50-52` defines registry hashes as `pure:` plus the first 16 hex chars
of sha256 over text. `registry.py:55-61` calls `inspect.getsource(fn)` and silently falls back to
`f"{fn.__module__}.{fn.__qualname__}"` on `OSError` or `TypeError`. That fallback is dangerous for
bundled code: functions created by plain `exec(source)` usually do not have inspectable source, so
the registry would install a stable-looking but wrong hash instead of crashing.

Another subtlety: authoring-side `inspect.getsource(fn)` includes decorator lines. The shipped
source blob must be exactly that decorated function block. It does not include imports, so the
worker's synthetic module provides the `pure` decorator binding while keeping the source bytes
unchanged.

Mechanisms evaluated:

- Linecache shim, implemented in `source_registration.py`: populate `linecache.cache` for a
  synthetic filename, compile the exact shipped decorated source under that filename, and exec it.
  The normal `@pure` -> `register_pure` path then calls unchanged `inspect.getsource(fn)` and
  computes the same source hash. This proved the round trip without framework edits.
- Direct source-hash install: a future API could hash shipped text directly and install
  `PureEntry(name, fn, source_hash)`. This avoids inspect/linecache magic and is the cleaner
  production API, but it needs explicit collision semantics in the registry.

Recommended P2 API:

```python
Registry.register_pure_from_source(name: str, source: str) -> PureEntry
```

Semantics:

- Hash exactly the shipped source text with the existing registry namespace
  (`pure:` + sha256(source)[:16]).
- Execute/register the function in a synthetic module with a minimal safe globals surface.
- If the name is already registered, compare source hashes. Same hash is OK; different hash is an
  error. This matches the plan rule: baked-vs-bundled hashes must agree; error, not precedence.
- Return the installed or existing `PureEntry`.

The shim entry point today is `julep/purity.py:87-88`, which forwards to
`DEFAULT_REGISTRY.register_pure`. The underlying collision behavior is
`julep/registry.py:88-93`: same name with a different function object is rejected
before comparing source hashes, so P2 needs a source-aware method rather than reusing that method
unchanged for bundled pures.

## Round-Trip Proof Transcript

Actual runner output:

```json
{
  "artifactHash": "sha256:8d90700c10d82627f8139e7d7b514cc0a9f1e5bc3616fdebd8332fdbd86e860e",
  "artifactHashProof": {
    "absentRefs": "sha256:8d90700c10d82627f8139e7d7b514cc0a9f1e5bc3616fdebd8332fdbd86e860e",
    "emptyRefs": "sha256:8d90700c10d82627f8139e7d7b514cc0a9f1e5bc3616fdebd8332fdbd86e860e",
    "presentRefs": "sha256:ef4e28d348fa69ecfeba181de4b83f046ef439a03f29b5304cb2f38aea3352cc"
  },
  "bakedOutput": {
    "summary": "Ada:16/3",
    "tags": "cas,spike"
  },
  "casDir": "spikes/cas_bundle/.cas",
  "flowDigest": "8a8d04b6cda2a83595d164b0369d40e3902b836cb6b3317d919f6bfbbd103261",
  "manifestDigest": "fbffa1ffee6c05e840aaed8febe06beaca6593d4e1cb51c5bcbec3a2505d5d64",
  "pureRuntimeRefs": {
    "cas.normalize_input.v1": {
      "abi": "python-source/json-v1",
      "bundleHash": "fbffa1ffee6c05e840aaed8febe06beaca6593d4e1cb51c5bcbec3a2505d5d64",
      "executorTier": "wasm",
      "sourceHash": "pure:aaeedfb2aff9aaef"
    },
    "cas.render_summary.v1": {
      "abi": "python-source/json-v1",
      "bundleHash": "fbffa1ffee6c05e840aaed8febe06beaca6593d4e1cb51c5bcbec3a2505d5d64",
      "executorTier": "wasm",
      "sourceHash": "pure:5d2ec7b9a63caa7b"
    }
  },
  "pureSourceDigests": {
    "cas.normalize_input.v1": "aaeedfb2aff9aaef2900a7ad1024b5451fe2dbd5dd368318fe6f05e6eec96935",
    "cas.render_summary.v1": "5d2ec7b9a63caa7bd8e3fa687b13b8d1bdaa1f8577fad19b8737caa72436e3b9"
  },
  "pureSourceHashes": {
    "cas.normalize_input.v1": "pure:aaeedfb2aff9aaef",
    "cas.render_summary.v1": "pure:5d2ec7b9a63caa7b"
  },
  "status": "PASS",
  "workerDidNotImportAuthoringFlow": true,
  "workerOutput": {
    "summary": "Ada:16/3",
    "tags": "cas,spike"
  },
  "workerVerifiedPures": {
    "cas.normalize_input.v1": "pure:aaeedfb2aff9aaef",
    "cas.render_summary.v1": "pure:5d2ec7b9a63caa7b"
  }
}
```

The worker is launched as a fresh subprocess via `sys.executable` by `runner.py`. It imports the
spike CAS helper (`cas`), registration helper (`source_registration`), and the framework runtime
APIs needed to deserialize and interpret the flow. It does not import `authoring_flow` or the
authoring-side bundle helper. `worker_main.py` asserts no module ending in `authoring_flow` is
present in `sys.modules` before registration and again after interpretation.

## P2 Integration Points

- `julep/deploy.py:229-249`: add `pureRuntimeRefs` to
  `Deployment.artifact_components` using the same absent-when-unset pattern as
  `rendererSourceHashes`.
- `julep/deploy.py:251-255`: artifact identity is SHA-256 over
  `canonical_json(self.artifact_components)`, so no separate hash path is needed after the join.
- `julep/registry.py:55-61`: current `_source_hash` inspect fallback can silently hash
  module/qualname for exec-created functions; P2 should avoid this for source bundles.
- `julep/registry.py:88-93`: current `register_pure` rejects same-name/different-fn
  before comparing hashes; P2 needs source-aware collision behavior.
- `julep/purity.py:87-88`: add a shim forwarding to the new registry API, for example
  `register_pure_from_source(name: str, source: str) -> PureEntry`.
- `julep/execution/harness.py:159-174`: add bundle reference data to `FlowInput`
  alongside `flow_json`, `manifest_json`, and `pinned_pures`.
- `julep/execution/harness.py:565-576`: carry the bundle reference through
  `FlowWorkflow` `continue_as_new`.
- `julep/execution/harness.py:842-858` and `harness.py:861-875`: carry the bundle
  reference through both `AgentWorkflow` `continue_as_new` sites.
- `julep/execution/effects.py:467-481`: `resolveSubflow` currently returns only
  `flowJson`, `manifestJson`, and `pinnedPures`; P2 should return the bundle reference there too.
