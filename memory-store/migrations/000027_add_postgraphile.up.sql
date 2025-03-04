BEGIN;

SELECT decompress_chunk(c, true) 
FROM show_chunks('transitions') c;

SELECT decompress_chunk(c, true) 
FROM show_chunks('entries') c;

CREATE SCHEMA IF NOT EXISTS postgraphile_auth;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO
$do$
BEGIN
   IF EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'postgraphile') THEN

      RAISE NOTICE 'Role "postgraphile" already exists. Skipping.';
   ELSE
      CREATE ROLE postgraphile;
   END IF;
END
$do$;

DO
$do$
BEGIN
   IF EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'no_access_role') THEN

      RAISE NOTICE 'Role "no_access_role" already exists. Skipping.';
   ELSE
      CREATE ROLE no_access_role;
   END IF;
END
$do$;

DO $$
BEGIN
    -- Check if the type already exists
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type t
        JOIN pg_namespace n ON t.typnamespace = n.oid
        WHERE t.typname = 'jwt_token'
    ) THEN
        -- Create the type if it does not exist
        CREATE TYPE jwt_token AS (
            role text,
            exp integer,
            developer_id UUID
        );
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS postgraphile_auth.users(
    developer_id UUID NOT NULL,
    email TEXT NOT NULL CONSTRAINT ct_developers_email_format CHECK (
        email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    ),
    password_hash text
);

GRANT SELECT ON postgraphile_auth.users TO no_access_role;
GRANT SELECT ON postgraphile_auth.users TO postgraphile;

CREATE OR REPLACE FUNCTION current_developer_id() returns UUID as $$
  select nullif(current_setting('jwt.claims.developer_id', true), '')::UUID;
$$ language sql stable;

CREATE POLICY access_users
  ON postgraphile_auth.users
  FOR SELECT
  TO postgraphile
  USING (developer_id = current_developer_id());

CREATE OR REPLACE FUNCTION authenticate(
  email text,
  password text
)
returns jwt_token
as $$
declare
  account postgraphile_auth.users;
begin
  select a.* into account
    from postgraphile_auth.users as a
    where a.email = authenticate.email;

  if account.password_hash = crypt(password, account.password_hash) then
    return (
      'postgraphile',
      extract(epoch from now() + interval '7 days'),
      account.developer_id
    )::jwt_token;
  else
    return null;
  end if;
end;
$$ language plpgsql strict security definer;

GRANT EXECUTE ON FUNCTION authenticate(text, text) TO no_access_role, postgraphile;

CREATE OR REPLACE FUNCTION current_developer_id_by_transition_id(p_transition_id UUID)
RETURNS UUID AS $$
DECLARE
    v_developer_id UUID;
BEGIN
    SELECT e.developer_id
    INTO v_developer_id
    FROM transitions t
    JOIN executions e ON t.execution_id = e.execution_id
    WHERE t.transition_id = p_transition_id;

    RETURN v_developer_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION current_developer_id_by_execution_id(p_execution_id UUID)
RETURNS UUID AS $$
DECLARE
    v_developer_id UUID;
BEGIN
    SELECT developer_id
    INTO v_developer_id
    FROM executions
    WHERE execution_id = p_execution_id;

    RETURN v_developer_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION current_developer_id_by_session_id(p_session_id UUID)
RETURNS UUID AS $$
DECLARE
    v_developer_id UUID;
BEGIN
    SELECT developer_id
    INTO v_developer_id
    FROM sessions
    WHERE session_id = p_session_id;

    RETURN v_developer_id;
END;
$$ LANGUAGE plpgsql;

GRANT ALL ON ALL TABLES IN SCHEMA public TO postgraphile;

DO $$
BEGIN
    BEGIN
        ALTER TABLE entries
        SET
            (timescaledb.compress = FALSE);
    EXCEPTION
        WHEN others THEN
            RAISE NOTICE 'An error occurred during unsetting entries.compress: %, %', SQLSTATE, SQLERRM;
    END;
END $$;

DO $$
BEGIN
    BEGIN
        ALTER TABLE transitions
        SET
            (timescaledb.compress = FALSE);
    EXCEPTION
        WHEN others THEN
            RAISE NOTICE 'An error occurred during unsetting transitions.compress: %, %', SQLSTATE, SQLERRM;
    END;
END $$;

ALTER TABLE developers ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE files ENABLE ROW LEVEL SECURITY;
ALTER TABLE file_owners ENABLE ROW LEVEL SECURITY;
ALTER TABLE docs ENABLE ROW LEVEL SECURITY;
ALTER TABLE doc_owners ENABLE ROW LEVEL SECURITY;
ALTER TABLE tools ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_lookup ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE transitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE temporal_executions_lookup ENABLE ROW LEVEL SECURITY;
ALTER TABLE entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE entry_relations ENABLE ROW LEVEL SECURITY;

CREATE POLICY access_developers_policy
  ON developers
  FOR ALL
  TO postgraphile
  USING (developer_id = current_developer_id())
  WITH CHECK (developer_id = current_developer_id());

CREATE POLICY access_agents_policy
  ON agents
  FOR ALL
  TO postgraphile
  USING (developer_id = current_developer_id())
  WITH CHECK (developer_id = current_developer_id());

CREATE POLICY access_users_policy
  ON users
  FOR ALL
  TO postgraphile
  USING (developer_id = current_developer_id())
  WITH CHECK (developer_id = current_developer_id());

CREATE POLICY access_files_policy
  ON files
  FOR ALL
  TO postgraphile
  USING (developer_id = current_developer_id())
  WITH CHECK (developer_id = current_developer_id());

CREATE POLICY access_file_owners_policy
  ON file_owners
  FOR ALL
  TO postgraphile
  USING (developer_id = current_developer_id())
  WITH CHECK (developer_id = current_developer_id());

CREATE POLICY access_docs_policy
  ON docs
  FOR ALL
  TO postgraphile
  USING (developer_id = current_developer_id())
  WITH CHECK (developer_id = current_developer_id());

CREATE POLICY access_doc_owners_policy
  ON doc_owners
  FOR ALL
  TO postgraphile
  USING (developer_id = current_developer_id())
  WITH CHECK (developer_id = current_developer_id());

CREATE POLICY access_tools_policy
  ON tools
  FOR ALL
  TO postgraphile
  USING (developer_id = current_developer_id())
  WITH CHECK (developer_id = current_developer_id());

CREATE POLICY access_sessions_policy
  ON sessions
  FOR ALL
  TO postgraphile
  USING (developer_id = current_developer_id())
  WITH CHECK (developer_id = current_developer_id());

CREATE POLICY access_session_lookup_policy
  ON session_lookup
  FOR ALL
  TO postgraphile
  USING (developer_id = current_developer_id())
  WITH CHECK (developer_id = current_developer_id());

CREATE POLICY access_tasks_policy
  ON tasks
  FOR ALL
  TO postgraphile
  USING (developer_id = current_developer_id())
  WITH CHECK (developer_id = current_developer_id());

CREATE POLICY access_workflows_policy
  ON workflows
  FOR ALL
  TO postgraphile
  USING (developer_id = current_developer_id())
  WITH CHECK (developer_id = current_developer_id());

CREATE POLICY access_executions_policy
  ON executions
  FOR ALL
  TO postgraphile
  USING (developer_id = current_developer_id())
  WITH CHECK (developer_id = current_developer_id());

CREATE POLICY access_transitions_policy
  ON transitions
  FOR ALL
  TO postgraphile
  USING (transition_id = current_developer_id_by_transition_id(transition_id))
  WITH CHECK (transition_id = current_developer_id_by_transition_id(transition_id));

CREATE POLICY access_temporal_executions_lookup_policy
  ON temporal_executions_lookup
  FOR ALL
  TO postgraphile
  USING (execution_id = current_developer_id_by_execution_id(execution_id))
  WITH CHECK (execution_id = current_developer_id_by_execution_id(execution_id));

CREATE POLICY access_entries_policy
  ON entries
  FOR ALL
  TO postgraphile
  USING (session_id = current_developer_id_by_session_id(session_id))
  WITH CHECK (session_id = current_developer_id_by_session_id(session_id));

CREATE POLICY access_entry_relations_policy
  ON entry_relations
  FOR ALL
  TO postgraphile
  USING (session_id = current_developer_id_by_session_id(session_id))
  WITH CHECK (session_id = current_developer_id_by_session_id(session_id));

DO $$
BEGIN
    BEGIN
        ALTER TABLE entries
            SET (
                timescaledb.compress = TRUE,
                timescaledb.compress_segmentby = 'session_id',
                timescaledb.compress_orderby = 'created_at DESC, entry_id DESC'
            );
    EXCEPTION
        WHEN others THEN
            RAISE NOTICE 'An error occurred during entries.compress: %, %', SQLSTATE, SQLERRM;
    END;
END $$;

DO $$
BEGIN
    BEGIN
        ALTER TABLE transitions
        SET
            (
                timescaledb.compress = TRUE,
                timescaledb.compress_segmentby = 'execution_id',
                timescaledb.compress_orderby = 'created_at DESC, transition_id DESC'
            );
    EXCEPTION
        WHEN others THEN
            RAISE NOTICE 'An error occurred during transitions.compress: %, %', SQLSTATE, SQLERRM;
    END;
END $$;

COMMIT;