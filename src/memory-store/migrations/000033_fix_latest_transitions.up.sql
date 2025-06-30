BEGIN;

/*
 * FIX FOR LATEST_TRANSITIONS CONTINUOUS AGGREGATE
 * 
 * This migration fixes an issue with the latest_transitions continuous aggregate view
 * where the join on the workflows table was causing empty rows when transitions were of
 * type 'finish' or 'error' since there's no step definition available for these states.
 * 
 * We remove the join on the workflows table and the step_definition column from the view.
 */

-- Drop existing continuous aggregate policy
DO $$
BEGIN
    BEGIN
        SELECT remove_continuous_aggregate_policy('latest_transitions');
    EXCEPTION
        WHEN others THEN
            RAISE NOTICE 'An error occurred during remove_continuous_aggregate_policy(latest_transitions): %, %', SQLSTATE, SQLERRM;
    END;
END $$;

-- Drop the existing views
DROP VIEW IF EXISTS latest_executions;
DROP MATERIALIZED VIEW IF EXISTS latest_transitions;

-- Create a continuous view that aggregates the transitions table without the workflows join
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
    count(*) AS transition_count,
    max(t.created_at) AS created_at,
    last (t.type, t.created_at) AS type,
    last (t.step_label, t.created_at) AS step_label,
    last (t.current_step, t.created_at) AS current_step,
    last (t.next_step, t.created_at) AS next_step,
    last (t.output, t.created_at) AS output,
    last (t.task_token, t.created_at) AS task_token,
    last (t.metadata, t.created_at) AS metadata,
    last (e.task_id, e.created_at) AS task_id,
    last (e.task_version, e.created_at) AS task_version
FROM
    transitions t
    JOIN executions e ON t.execution_id = e.execution_id
GROUP BY
    bucket,
    t.execution_id
WITH
    no data;

-- Add the continuous aggregate policy
SELECT
    add_continuous_aggregate_policy (
        'latest_transitions',
        start_offset => NULL,
        end_offset => INTERVAL '10 minutes',
        schedule_interval => INTERVAL '10 minutes'
    );

-- Recreate the latest_executions view without step_definition
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
    coalesce(lt.transition_count, 0) AS transition_count,
    coalesce(lt.output, '{}'::jsonb) AS output,
    lt.current_step,
    lt.next_step,
    lt.step_label,
    lt.task_token,
    lt.metadata AS transition_metadata
FROM
    executions e
    LEFT JOIN latest_transitions lt ON e.execution_id = lt.execution_id;

COMMIT;