---- Transitions

-- Drop new indices
DO $$
BEGIN
  DROP index if exists idx_transitions_execution_id;

  DROP index if exists idx_executions_created_at_covering;

  DROP index if exists idx_transitions_created_at;
END $$;

-- Temporarily disable compression (for unique index creation)
ALTER TABLE transitions SET (timescaledb.compress = false);

-- Restore old indices
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_transitions_metadata') THEN
        CREATE INDEX idx_transitions_metadata ON transitions USING GIN (metadata);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_transitions_label') THEN
        CREATE UNIQUE INDEX idx_transitions_label ON transitions USING btree (execution_id, step_label, created_at DESC)
        WHERE (step_label IS NOT NULL);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_transitions_next') THEN
        CREATE UNIQUE INDEX idx_transitions_next ON transitions USING btree (execution_id, next_step, created_at DESC)
        WHERE (next_step IS NOT NULL);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_transitions_current') THEN
        CREATE UNIQUE INDEX idx_transitions_current ON transitions USING btree (execution_id, current_step, created_at DESC);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'transitions_created_at_idx') THEN
        CREATE INDEX transitions_created_at_idx ON transitions USING btree (created_at DESC);
    END IF;
END $$;

-- Re-enable compression
ALTER TABLE transitions SET (timescaledb.compress = true);

---- Entries

-- Drop new indices
DO $$
BEGIN
    DROP index if exists idx_entries_session_id;

    DROP index if exists idx_entries_created_at;

    DROP index if exists idx_sessions_created_at_covering;
END $$;

-- Restore old indices
DO $$
BEGIN
    CREATE INDEX IF NOT EXISTS idx_entries_by_session ON entries (session_id DESC);

    CREATE INDEX IF NOT EXISTS entries_created_at_idx ON entries USING btree (created_at DESC);
END $$;
