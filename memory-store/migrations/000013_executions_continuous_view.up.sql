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
    time_bucket ('1 day', created_at) AS bucket,
    execution_id,
    transition_id,
    count(*) AS total_transitions,
    state_agg (created_at, to_text (type)) AS state,
    max(created_at) AS created_at,
    last (type, created_at) AS type,
    last (step_definition, created_at) AS step_definition,
    last (step_label, created_at) AS step_label,
    last (current_step, created_at) AS current_step,
    last (next_step, created_at) AS next_step,
    last (output, created_at) AS output,
    last (task_token, created_at) AS task_token,
    last (metadata, created_at) AS metadata
FROM
    transitions
GROUP BY
    bucket,
    execution_id,
    transition_id
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