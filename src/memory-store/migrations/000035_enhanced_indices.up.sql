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

  CREATE INDEX if not exists idx_transitions_created_at ON transitions USING btree (created_at DESC);

  CREATE INDEX if not exists idx_executions_created_at_covering
    ON executions (created_at DESC)
    INCLUDE (execution_id);
END $$;

---- Entries

-- Drop old indices
DO $$
BEGIN
  DROP index if exists idx_entries_by_session;
  DROP index if exists entries_created_at_idx;
END $$;

-- Create new indices
DO $$
BEGIN
  CREATE INDEX if not exists idx_entries_session_id ON entries (created_at DESC, session_id DESC);
  
  CREATE INDEX if not exists idx_entries_created_at ON entries (created_at DESC);

  CREATE INDEX if not exists idx_sessions_created_at_covering 
    ON sessions (created_at DESC)
    INCLUDE (session_id);
END $$;