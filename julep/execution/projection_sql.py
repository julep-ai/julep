"""Host-applied SQL for the durable projection execution store.

The execution store owns its own schema and migration ledger.  This module is
deliberately dependency-free: callers provide a one-argument ``execute``
callable (normally ``cursor.execute``), and importing it never imports a
Postgres driver or opens a connection.
"""

from __future__ import annotations

from textwrap import indent
from typing import Callable

CREATE_SCHEMA_MIGRATIONS_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version integer PRIMARY KEY,
    applied_at double precision NOT NULL
)
"""

CREATE_RUNS_SQL = """
CREATE TABLE IF NOT EXISTS runs (
    run_id text PRIMARY KEY,
    idempotency_key text UNIQUE,
    workflow_id text,
    temporal_run_id text,
    session_id text,
    release_hash text,
    pipeline text,
    application text,
    status text NOT NULL CHECK (status IN (
        'submitting',
        'accepted',
        'start_failed',
        'running',
        'completed',
        'failed',
        'canceled',
        'terminated'
    )),
    principal jsonb,
    input_ref text,
    result_ref text,
    error text,
    started_at double precision,
    finished_at double precision
)
"""

CREATE_PROJECTION_EVENTS_SQL = """
CREATE TABLE IF NOT EXISTS projection_events (
    workflow_id text NOT NULL,
    segment_seq integer NOT NULL,
    event_id text NOT NULL,
    run_id text NOT NULL,
    seq bigserial,
    type text NOT NULL,
    node text NOT NULL,
    cid text NOT NULL,
    ts double precision NOT NULL,
    causes jsonb NOT NULL DEFAULT '[]'::jsonb,
    value_ref text,
    shape text,
    cost double precision,
    error text,
    attrs jsonb NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (workflow_id, segment_seq, event_id)
)
"""

CREATE_PROJECTION_EVENTS_RUN_SEQ_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS projection_events_run_seq_idx
ON projection_events (run_id, seq)
"""

CREATE_PROJECTION_VALUES_SQL = """
CREATE TABLE IF NOT EXISTS projection_values (
    value_ref text PRIMARY KEY,
    payload jsonb,
    byte_len integer NOT NULL,
    oversize boolean NOT NULL DEFAULT false,
    created_at double precision NOT NULL
)
"""

CREATE_RELEASES_SQL = """
CREATE TABLE IF NOT EXISTS releases (
    release_hash text PRIMARY KEY,
    application text,
    manifest jsonb NOT NULL,
    created_at double precision NOT NULL
)
"""

CREATE_DEPLOYMENTS_SQL = """
CREATE TABLE IF NOT EXISTS deployments (
    lane text PRIMARY KEY,
    release_hash text NOT NULL,
    activated_at double precision NOT NULL,
    activated_by text
)
"""

CREATE_RUNS_STARTED_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS runs_started_run_id_idx
ON runs (started_at DESC NULLS LAST, run_id DESC)
"""

CREATE_RUNS_STATUS_STARTED_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS runs_status_started_run_id_idx
ON runs (status, started_at DESC NULLS LAST, run_id DESC)
"""

CREATE_RELEASES_CREATED_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS releases_created_release_hash_idx
ON releases (created_at DESC, release_hash DESC)
"""


MIGRATIONS: tuple[tuple[int, str], ...] = (
    (1, CREATE_RUNS_SQL),
    (
        2,
        CREATE_PROJECTION_EVENTS_SQL
        + ";\n"
        + CREATE_PROJECTION_EVENTS_RUN_SEQ_INDEX_SQL,
    ),
    (3, CREATE_PROJECTION_VALUES_SQL),
    (4, CREATE_RELEASES_SQL),
    (5, CREATE_DEPLOYMENTS_SQL),
    (6, CREATE_RUNS_STARTED_INDEX_SQL),
    (7, CREATE_RUNS_STATUS_STARTED_INDEX_SQL),
    (8, CREATE_RELEASES_CREATED_INDEX_SQL),
)


def _migration_statement(version: int, sql: str) -> str:
    """Wrap one migration and its ledger write in one Postgres statement."""
    body = indent(sql.strip() + ";", " " * 8)
    return f"""
DO $julep_projection_migration$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM schema_migrations WHERE version = {version}
    ) THEN
{body}
        INSERT INTO schema_migrations (version, applied_at)
        VALUES ({version}, EXTRACT(EPOCH FROM clock_timestamp()))
        ON CONFLICT (version) DO NOTHING;
    END IF;
END
$julep_projection_migration$
"""


def apply_projection_schema(execute: Callable[[str], None]) -> None:
    """Apply every not-yet-recorded projection migration in version order."""
    execute(CREATE_SCHEMA_MIGRATIONS_SQL)
    for version, sql in MIGRATIONS:
        execute(_migration_statement(version, sql))
