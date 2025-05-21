-- Hasura init migration for executions and transitions tables
-- This mirrors the schema used in memory-store

CREATE TABLE IF NOT EXISTS public.executions (
  id uuid PRIMARY KEY,
  developer_id uuid NOT NULL,
  task_id uuid NOT NULL,
  task_version integer NOT NULL,
  input jsonb,
  metadata jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.transitions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  execution_id uuid NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
  type text NOT NULL,
  step_label text,
  output jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS transitions_execution_created_idx ON public.transitions(execution_id, created_at);
