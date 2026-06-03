# Invariant Test Map

This directory is the home for per-invariant conformance tests added after
Phase 0. The current files are stubs so later phases have stable targets.

| # | Spec invariant | Planned test file |
|---|---|---|
| 1 | Freeze isolation | `test_01_freeze_isolation.py` |
| 2 | Effects are authorized statically | `test_02_static_effect_authorization.py` |
| 3 | Staged plans choose composition, not effects | `test_03_staged_plan_binding.py` |
| 4 | Concurrency settles on success | `test_04_concurrency_success_settlement.py` |
| 5 | Sub is a one-way mirror | `test_05_sub_firewall.py` |
| 6 | History is the source of truth; projection is derived | `test_06_projection_derivation.py` |
| 7 | Pures are named, deterministic, and hash-checked | `test_07_pure_integrity.py` |
| 8 | Capabilities are deny-by-default where present | `test_08_capability_deny_default.py` |
| 9 | Agents speak a closed vocabulary under a bounded budget | `test_09_agent_budget_vocabulary.py` |
| 10 | Workflow code is deterministic | `test_10_workflow_determinism.py` |
