---- Transitions

-- Drop old indices
DO $$
BEGIN
  DROP index if exists idx_transitions_label;

  DROP index if exists idx_transitions_metadata;

  DROP index if exists idx_transitions_next;

  DROP index if exists idx_transitions_current;
  
  DROP index if exists transitions_created_at_idx;
END $$;

-- Create new indices
DO $$
BEGIN
  CREATE INDEX if not exists 
    idx_transitions_execution_id ON transitions USING btree (created_at DESC, execution_id DESC);

  CREATE INDEX IF NOT EXISTS idx_executions_created_at_covering
    ON executions (created_at DESC)
    INCLUDE (execution_id);

  CREATE INDEX if not exists idx_transitions_created_at ON transitions USING btree (created_at DESC);
END $$;
