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
    execution_id
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
    lt.created_at AS updated_at,
    -- Map transition types to status using CASE statement
    CASE lt.type::text
        WHEN 'init' THEN 'starting'
        WHEN 'init_branch' THEN 'running'
        WHEN 'wait' THEN 'awaiting_input'
        WHEN 'resume' THEN 'running'
        WHEN 'step' THEN 'running'
        WHEN 'finish' THEN 'succeeded'
        WHEN 'finish_branch' THEN 'running'
        WHEN 'error' THEN 'failed'
        WHEN 'cancelled' THEN 'cancelled'
        ELSE 'queued'
    END AS status,
    lt.output,
    -- Extract error from output if type is 'error'
    CASE
        WHEN lt.type::text = 'error' THEN lt.output ->> 'error'
        ELSE NULL
    END AS error,
    lt.total_transitions,
    lt.current_step,
    lt.next_step,
    lt.step_definition,
    lt.step_label,
    lt.task_token,
    lt.metadata AS transition_metadata
FROM
    executions e,
    latest_transitions lt
WHERE
    e.execution_id = lt.execution_id;

COMMIT;