# Julep hard-cutover rename inventory

This file is the source of truth for names retired by the Julep hard cutover. The CI guard reads
the tab-separated block below; keep one old-to-new mapping per line. `token` matches a literal name
with identifier boundaries, while `prefix` also rejects names that extend a retired prefix. The
guard never searches for the bare word `ca`.

<!-- rename-inventory:start -->
```tsv
category	match	old	new
package	token	julep.ca.cli	julep.cli.main
package	token	julep.ca	julep.cli
package	token	julep.cli.cli	julep.cli.main
corruption	token	julep.clis	julep.cas
corruption	token	julep.clipabilities	julep.capabilities
package	token	julep/ca/cli.py	julep/cli/main.py
package	token	julep/ca/	julep/cli/
package	token	julep/cli.py	julep/cli/artifact.py
package	token	tests/ca/	tests/cli/
import	token	from julep import ca	from julep import cli
class	token	CaConfig	JulepConfig
entry-point	token	julep.ca.cli:main	julep.cli.main:main
config	token	ca.toml	julep.toml
config	token	[tool.ca]	[tool.julep]
config	token	[tool.ca.	[tool.julep.
state	token	.ca/	.julep/
state	token	".ca"	".julep"
state	token	'.ca'	'.julep'
env-family	prefix	CA_	JULEP_
env-family	prefix	COMPOSABLE_	JULEP_
env	token	CA_BUNDLE_SIGNING_KEY	JULEP_BUNDLE_SIGNING_KEY
env	token	CA_BUNDLE_ALLOWED_SIGNERS	JULEP_BUNDLE_ALLOWED_SIGNERS
env	token	CA_BUNDLES	JULEP_BUNDLES
env	token	CA_BUNDLE_NATIVE_EXEC	JULEP_BUNDLE_NATIVE_EXEC
env	token	CA_PURE_NATIVE_DEPS	JULEP_PURE_NATIVE_DEPS
env	token	CA_WORKER_BUILD_ID	JULEP_WORKER_BUILD_ID
env	token	CA_WORKER_VERSIONING	JULEP_WORKER_VERSIONING
env	token	CA_BATCH_RESULT_TIMEOUT_S	JULEP_BATCH_RESULT_TIMEOUT_S
env	token	CA_ENV	JULEP_ENV
env	token	COMPOSABLE_AGENTS_SOURCE_CAPTURE	JULEP_SOURCE_CAPTURE
env	token	COMPOSABLE_NATIVE_VENV_CACHE_DIR	JULEP_NATIVE_VENV_CACHE_DIR
env	token	COMPOSABLE_WASM_FUEL	JULEP_WASM_FUEL
env	token	COMPOSABLE_WASM_CACHE_DIR	JULEP_WASM_CACHE_DIR
env	token	COMPOSABLE_WASM_EPOCH_MS	JULEP_WASM_EPOCH_MS
meta	token	__ca_meta__	__julep_meta__
meta	token	CA_META_KEY	JULEP_META_KEY
meta	token	_CA_META_KEY	_JULEP_META_KEY
meta	token	ca_meta	julep_meta
meta	token	_unwrap_ca_meta	_unwrap_julep_meta
meta	token	_with_ca_meta	_with_julep_meta
meta	token	test_interpreter_ca_meta.py	test_interpreter_julep_meta.py
durable-id	token	ca:	julep:
durable-id	token	ca-managed cron=	julep-managed cron=
resource	token	ca-worker-secrets	julep-worker-secrets
resource	token	ca-worker	julep-worker
resource	token	ca-staging	julep-staging
resource	prefix	ca-local-	julep-local-
resource	token	ca-dbos-pg	julep-dbos-pg
resource	prefix	ca-spike-	julep-spike-
resource	prefix	ca-e2e-	julep-e2e-
resource-prefix	prefix	ca-	julep-
dbos	token	ca_flow	julep_flow
dbos	token	ca_agent	julep_agent
otel+langfuse	token	ca.cid	julep.cid
otel+langfuse	token	ca.node	julep.node
otel	token	ca.cost	julep.cost
langfuse	token	ca.llm.attempts	julep.llm.attempts
wasm	token	composable-env	julep-env
wasm	prefix	composable-env-	julep-env-
wasm	prefix	composable_executor_	julep_executor_
wasm	token	composable-wasm-epoch	julep-wasm-epoch
sentinel	token	__CA_RESOLVE_BEGIN__	__JULEP_RESOLVE_BEGIN__
sentinel	token	__CA_RESOLVE_END__	__JULEP_RESOLVE_END__
transcript	token	__ca_summary__	__julep_summary__
dbos	token	__ca_policy_error__	__julep_policy_error__
native-venv	prefix	composable_native_venv_	julep_native_venv_
harness	token	_ca_repr_includes_cause	_julep_repr_includes_cause
```
<!-- rename-inventory:end -->

Intentional legacy spellings are limited to migration diagnostics in `julep/_env.py`,
`julep/cli/config.py`, and `julep/cli/doctor.py`, plus their focused config and doctor tests. The
guard applies category-specific exceptions for those files. It also narrowly permits the standard
certificate-authority filenames in `tooling/sandbox-k8s`. Changelogs are historical records and are
excluded from enforcement.
