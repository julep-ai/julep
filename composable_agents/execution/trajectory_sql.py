"""Host-applied SQL for the trajectory plane.

The trajectory store class is only the dependency-free seam. Production hosts
apply these statements with their own migration system; importing this module
does not auto-migrate and does not require a database driver.
"""

from __future__ import annotations

from typing import Callable

CREATE_TRAJECTORY_RUNS_SQL = """
CREATE TABLE IF NOT EXISTS trajectory_runs (
    run_id text PRIMARY KEY,
    root_run_id text NOT NULL,
    parent_run_id text,
    backend text NOT NULL,
    session_id text NOT NULL,
    segment_seq integer NOT NULL,
    controller text,
    flow_ref text,
    status text NOT NULL,
    policy jsonb,
    started_ts double precision NOT NULL,
    finished_ts double precision,
    logical_seq integer NOT NULL
)
"""

CREATE_TRAJECTORY_STEPS_SQL = """
CREATE TABLE IF NOT EXISTS trajectory_steps (
    step_id text PRIMARY KEY,
    run_id text NOT NULL,
    root_run_id text NOT NULL,
    cid text NOT NULL,
    node_id text NOT NULL,
    op text NOT NULL,
    kind text NOT NULL,
    causes text[] NOT NULL DEFAULT '{}',
    status text NOT NULL,
    input_ref text,
    output_ref text,
    error text,
    cost double precision,
    attrs jsonb NOT NULL DEFAULT '{}'::jsonb,
    logical_seq integer NOT NULL
)
"""

CREATE_TRAJECTORY_VALUES_SQL = """
CREATE TABLE IF NOT EXISTS trajectory_values (
    ref text NOT NULL,
    root_run_id text NOT NULL,
    step_id text NOT NULL,
    kind text NOT NULL,
    size integer,
    PRIMARY KEY (ref, step_id, kind)
)
"""

CREATE_TRAJECTORY_STEPS_ROOT_RUN_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS trajectory_steps_root_run_id_idx
ON trajectory_steps (root_run_id)
"""

CREATE_TRAJECTORY_RUNS_PARENT_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS trajectory_runs_parent_run_id_idx
ON trajectory_runs (parent_run_id)
"""

CREATE_TRAJECTORY_STEPS_RUN_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS trajectory_steps_run_id_idx
ON trajectory_steps (run_id)
"""

CREATE_TRAJECTORY_RUNS_ROOT_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS trajectory_runs_root_run_id_idx
ON trajectory_runs (root_run_id)
"""

TRAJECTORY_DDL: tuple[str, ...] = (
    CREATE_TRAJECTORY_RUNS_SQL,
    CREATE_TRAJECTORY_STEPS_SQL,
    CREATE_TRAJECTORY_VALUES_SQL,
    CREATE_TRAJECTORY_STEPS_ROOT_RUN_INDEX_SQL,
    CREATE_TRAJECTORY_RUNS_PARENT_INDEX_SQL,
    CREATE_TRAJECTORY_STEPS_RUN_INDEX_SQL,
    CREATE_TRAJECTORY_RUNS_ROOT_INDEX_SQL,
)


def apply_trajectory_schema(execute: Callable[[str], None]) -> None:
    for stmt in TRAJECTORY_DDL:
        execute(stmt)
