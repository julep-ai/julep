BEGIN;

-- Create projects table
CREATE TABLE IF NOT EXISTS projects (
    project_id UUID NOT NULL,
    developer_id UUID NOT NULL,
    canonical_name CITEXT NOT NULL CONSTRAINT ct_projects_canonical_name_length CHECK (
        length(canonical_name) >= 1
        AND length(canonical_name) <= 255
    ),
    name TEXT NOT NULL CONSTRAINT ct_projects_name_length CHECK (
        length(name) >= 1
        AND length(name) <= 255
    ),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT pk_projects PRIMARY KEY (project_id),
    CONSTRAINT uq_projects_developer_canonical_name UNIQUE (developer_id, canonical_name),
    CONSTRAINT ct_projects_canonical_name_valid_identifier CHECK (canonical_name ~ '^[a-zA-Z][a-zA-Z0-9_]*$'),
    CONSTRAINT ct_projects_metadata_is_object CHECK (jsonb_typeof(metadata) = 'object'),
    CONSTRAINT fk_projects_developer FOREIGN KEY (developer_id) REFERENCES developers (developer_id)
);

-- Create project_agents association table
CREATE TABLE IF NOT EXISTS project_agents (
    project_id UUID NOT NULL,
    developer_id UUID NOT NULL,
    agent_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_project_agents PRIMARY KEY (project_id, agent_id),
    CONSTRAINT fk_project_agents_project FOREIGN KEY (project_id) REFERENCES projects (project_id) ON DELETE CASCADE,
    CONSTRAINT fk_project_agents_agent FOREIGN KEY (developer_id, agent_id) REFERENCES agents (developer_id, agent_id) ON DELETE CASCADE
);

-- Create project_users association table
CREATE TABLE IF NOT EXISTS project_users (
    project_id UUID NOT NULL,
    developer_id UUID NOT NULL,
    user_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_project_users PRIMARY KEY (project_id, user_id),
    CONSTRAINT fk_project_users_project FOREIGN KEY (project_id) REFERENCES projects (project_id) ON DELETE CASCADE,
    CONSTRAINT fk_project_users_user FOREIGN KEY (developer_id, user_id) REFERENCES users (developer_id, user_id) ON DELETE CASCADE
);

-- Create project_sessions association table
CREATE TABLE IF NOT EXISTS project_sessions (
    project_id UUID NOT NULL,
    developer_id UUID NOT NULL,
    session_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_project_sessions PRIMARY KEY (project_id, session_id),
    CONSTRAINT fk_project_sessions_project FOREIGN KEY (project_id) REFERENCES projects (project_id) ON DELETE CASCADE,
    CONSTRAINT fk_project_sessions_session FOREIGN KEY (developer_id, session_id) REFERENCES sessions (developer_id, session_id) ON DELETE CASCADE
);

-- Create project_tasks association table
CREATE TABLE IF NOT EXISTS project_tasks (
    project_id UUID NOT NULL,
    developer_id UUID NOT NULL,
    task_id UUID NOT NULL,
    task_version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_project_tasks PRIMARY KEY (project_id, task_id, task_version),
    CONSTRAINT fk_project_tasks_project FOREIGN KEY (project_id) REFERENCES projects (project_id) ON DELETE CASCADE,
    CONSTRAINT fk_project_tasks_task FOREIGN KEY (developer_id, task_id, task_version) REFERENCES tasks (developer_id, task_id, version) ON DELETE CASCADE
);

-- Create project_executions association table
CREATE TABLE IF NOT EXISTS project_executions (
    project_id UUID NOT NULL,
    developer_id UUID NOT NULL,
    execution_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_project_executions PRIMARY KEY (project_id, execution_id),
    CONSTRAINT fk_project_executions_project FOREIGN KEY (project_id) REFERENCES projects (project_id) ON DELETE CASCADE,
    CONSTRAINT fk_project_executions_execution FOREIGN KEY (execution_id) REFERENCES executions (execution_id) ON DELETE CASCADE
);

-- Create project_docs association table
CREATE TABLE IF NOT EXISTS project_docs (
    project_id UUID NOT NULL,
    developer_id UUID NOT NULL,
    doc_id UUID NOT NULL,
    doc_index INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_project_docs PRIMARY KEY (project_id, doc_id, doc_index),
    CONSTRAINT fk_project_docs_project FOREIGN KEY (project_id) REFERENCES projects (project_id) ON DELETE CASCADE,
    CONSTRAINT fk_project_docs_doc FOREIGN KEY (developer_id, doc_id, doc_index) REFERENCES docs (developer_id, doc_id, index) ON DELETE CASCADE
);

-- Create project_files association table
CREATE TABLE IF NOT EXISTS project_files (
    project_id UUID NOT NULL,
    developer_id UUID NOT NULL,
    file_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_project_files PRIMARY KEY (project_id, file_id),
    CONSTRAINT fk_project_files_project FOREIGN KEY (project_id) REFERENCES projects (project_id) ON DELETE CASCADE,
    CONSTRAINT fk_project_files_file FOREIGN KEY (developer_id, file_id) REFERENCES files (developer_id, file_id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_projects_developer_id ON projects (developer_id);
CREATE INDEX IF NOT EXISTS idx_projects_metadata ON projects USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_project_agents_agent ON project_agents (developer_id, agent_id);
CREATE INDEX IF NOT EXISTS idx_project_users_user ON project_users (developer_id, user_id);
CREATE INDEX IF NOT EXISTS idx_project_sessions_session ON project_sessions (developer_id, session_id);
CREATE INDEX IF NOT EXISTS idx_project_tasks_task ON project_tasks (developer_id, task_id, task_version);
CREATE INDEX IF NOT EXISTS idx_project_executions_execution ON project_executions (developer_id, execution_id);
CREATE INDEX IF NOT EXISTS idx_project_docs_doc ON project_docs (developer_id, doc_id, doc_index);
CREATE INDEX IF NOT EXISTS idx_project_files_file ON project_files (developer_id, file_id);

-- Create trigger to automatically update updated_at for projects
CREATE OR REPLACE TRIGGER trg_projects_updated_at BEFORE UPDATE 
ON projects FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Add comments to tables
COMMENT ON TABLE projects IS 'Stores project configurations and metadata for developers';
COMMENT ON TABLE project_agents IS 'Associates agents with projects';
COMMENT ON TABLE project_users IS 'Associates users with projects';
COMMENT ON TABLE project_sessions IS 'Associates sessions with projects';
COMMENT ON TABLE project_tasks IS 'Associates tasks with projects';
COMMENT ON TABLE project_executions IS 'Associates executions with projects';
COMMENT ON TABLE project_docs IS 'Associates docs with projects';
COMMENT ON TABLE project_files IS 'Associates files with projects';

COMMIT; 