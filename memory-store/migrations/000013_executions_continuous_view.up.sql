BEGIN;

/*
 * CONTINUOUS AGGREGATES WITH STATE AGGREGATION (Complexity: 9/10)
 * This is a TimescaleDB feature that automatically maintains a real-time summary of the transitions table.
 * It uses special aggregation functions like state_agg() to track state changes and last() to get most recent values.
 * The view updates every 10 minutes and can serve both historical and real-time data (materialized_only = FALSE).
 */
-- create a function to convert transition_type to text (needed coz ::text is stable not immutable)
CREATE
OR REPLACE function to_text (transition_type) RETURNS text AS $$
    select $1
$$ STRICT IMMUTABLE LANGUAGE sql;

-- create a continuous view that aggregates the transitions table
CREATE MATERIALIZED VIEW IF NOT EXISTS latest_transitions
WITH
    (
        timescaledb.continuous,
        timescaledb.materialized_only = FALSE
    ) AS
SELECT
    time_bucket ('1 day', t.created_at) AS bucket,
    t.execution_id,
    last (t.transition_id, t.created_at) AS transition_id,
    count(*) AS total_transitions,
    state_agg (t.created_at, to_text (t.type)) AS state,
    max(t.created_at) AS created_at,
    last (t.type, t.created_at) AS type,
    last (t.step_label, t.created_at) AS step_label,
    last (t.current_step, t.created_at) AS current_step,
    last (t.next_step, t.created_at) AS next_step,
    last (t.output, t.created_at) AS output,
    last (t.task_token, t.created_at) AS task_token,
    last (t.metadata, t.created_at) AS metadata,
    last (e.task_id, e.created_at) AS task_id,
    last (e.task_version, e.created_at) AS task_version,
    last (w.step_definition, e.created_at) AS step_definition
FROM
    transitions t
    JOIN executions e ON t.execution_id = e.execution_id
    JOIN workflows w ON e.task_id = w.task_id
    AND e.task_version = w.version
    AND w.step_idx = (t.current_step).step_index
    AND w.name = (t.current_step).workflow_name
GROUP BY
    bucket,
    t.execution_id
WITH
    no data;

SELECT
    add_continuous_aggregate_policy (
        'latest_transitions',
        start_offset => NULL,
        end_offset => INTERVAL '10 minutes',
        schedule_interval => INTERVAL '10 minutes'
    );

-- Create a view that combines executions with their latest transitions
CREATE OR REPLACE VIEW latest_executions AS
SELECT
    e.developer_id,
    e.task_id,
    e.task_version,
    e.execution_id,
    e.input,
    e.metadata,
    e.created_at,
    coalesce(lt.created_at, e.created_at) AS updated_at,
    CASE
        WHEN lt.type::text IS NULL THEN 'queued'
        WHEN lt.type::text = 'init' THEN 'starting'
        WHEN lt.type::text = 'init_branch' THEN 'running'
        WHEN lt.type::text = 'wait' THEN 'awaiting_input'
        WHEN lt.type::text = 'resume' THEN 'running'
        WHEN lt.type::text = 'step' THEN 'running'
        WHEN lt.type::text = 'finish' THEN 'succeeded'
        WHEN lt.type::text = 'finish_branch' THEN 'running'
        WHEN lt.type::text = 'error' THEN 'failed'
        WHEN lt.type::text = 'cancelled' THEN 'cancelled'
        ELSE 'queued'
    END AS status,
    CASE
        WHEN lt.type::text = 'error' THEN lt.output ->> 'error'
        ELSE NULL
    END AS error,
    coalesce(lt.total_transitions, 0) AS total_transitions,
    coalesce(lt.output, '{}'::jsonb) AS output,
    lt.current_step,
    lt.next_step,
    lt.step_definition,
    lt.step_label,
    lt.task_token,
    lt.metadata AS transition_metadata
FROM
    executions e
    LEFT JOIN latest_transitions lt ON e.execution_id = lt.execution_id;

COMMIT;