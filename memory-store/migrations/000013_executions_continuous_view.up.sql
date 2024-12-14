BEGIN;

-- create a function to convert transition_type to text (needed coz ::text is stable not immutable)
create or replace function to_text(transition_type)
RETURNS text AS
$$
    select $1
$$ STRICT IMMUTABLE LANGUAGE sql;

-- create a continuous view that aggregates the transitions table
create materialized view if not exists latest_transitions
with
    (
        timescaledb.continuous,
        timescaledb.materialized_only = false
    ) as
select
    time_bucket ('1 day', created_at) as bucket,
    execution_id,
    count(*) as total_transitions,
    state_agg (created_at, to_text (type)) as state,
    max(created_at) as created_at,
    last (type, created_at) as type,
    last (step_definition, created_at) as step_definition,
    last (step_label, created_at) as step_label,
    last (current_step, created_at) as current_step,
    last (next_step, created_at) as next_step,
    last (output, created_at) as output,
    last (task_token, created_at) as task_token,
    last (metadata, created_at) as metadata
from
    transitions
group by
    bucket,
    execution_id
with no data;

SELECT
    add_continuous_aggregate_policy (
        'latest_transitions',
        start_offset => NULL,
        end_offset => INTERVAL '10 minutes',
        schedule_interval => INTERVAL '10 minutes'
    );

-- Create a view that combines executions with their latest transitions
create or replace view latest_executions as
SELECT
    e.developer_id,
    e.task_id,
    e.task_version,
    e.execution_id,
    e.input,
    e.metadata,
    e.created_at,
    lt.created_at as updated_at,
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
    END as status,
    lt.output,
    -- Extract error from output if type is 'error'
    CASE
        WHEN lt.type::text = 'error' THEN lt.output ->> 'error'
        ELSE NULL
    END as error,
    lt.total_transitions,
    lt.current_step,
    lt.next_step,
    lt.step_definition,
    lt.step_label,
    lt.task_token,
    lt.metadata as transition_metadata
FROM
    executions e,
    latest_transitions lt
WHERE
    e.execution_id = lt.execution_id;

COMMIT;