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
    CONSTRAINT pk_project_agents PRIMARY KEY (project_id, agent_id),
    CONSTRAINT fk_project_agents_project FOREIGN KEY (project_id) REFERENCES projects (project_id) ON DELETE RESTRICT,
    CONSTRAINT fk_project_agents_agent FOREIGN KEY (developer_id, agent_id) REFERENCES agents (developer_id, agent_id) ON DELETE CASCADE
);

-- Create project_users association table
CREATE TABLE IF NOT EXISTS project_users (
    project_id UUID NOT NULL,
    developer_id UUID NOT NULL,
    user_id UUID NOT NULL,
    CONSTRAINT pk_project_users PRIMARY KEY (project_id, user_id),
    CONSTRAINT fk_project_users_project FOREIGN KEY (project_id) REFERENCES projects (project_id) ON DELETE RESTRICT,
    CONSTRAINT fk_project_users_user FOREIGN KEY (developer_id, user_id) REFERENCES users (developer_id, user_id) ON DELETE CASCADE
);

-- Create project_files association table
CREATE TABLE IF NOT EXISTS project_files (
    project_id UUID NOT NULL,
    developer_id UUID NOT NULL,
    file_id UUID NOT NULL,
    CONSTRAINT pk_project_files PRIMARY KEY (project_id, file_id),
    CONSTRAINT fk_project_files_project FOREIGN KEY (project_id) REFERENCES projects (project_id) ON DELETE RESTRICT,
    CONSTRAINT fk_project_files_file FOREIGN KEY (developer_id, file_id) REFERENCES files (developer_id, file_id) ON DELETE CASCADE
);

-- Create project_sessions view
CREATE OR REPLACE VIEW project_sessions AS
WITH sessions_with_projects AS (
    -- Sessions with agent participants that are in projects
    SELECT DISTINCT
        s.session_id,
        s.developer_id,
        p.project_id
    FROM sessions s
    JOIN session_lookup sl ON s.session_id = sl.session_id AND sl.participant_type = 'agent'
    JOIN project_agents pa ON pa.developer_id = s.developer_id AND pa.agent_id = sl.participant_id
    JOIN projects p ON pa.project_id = p.project_id
    
    UNION
    
    -- Sessions with user participants that are in projects
    SELECT DISTINCT
        s.session_id,
        s.developer_id,
        p.project_id
    FROM sessions s
    JOIN session_lookup sl ON s.session_id = sl.session_id AND sl.participant_type = 'user'
    JOIN project_users pu ON pu.developer_id = s.developer_id AND pu.user_id = sl.participant_id
    JOIN projects p ON pu.project_id = p.project_id
)
SELECT
    s.session_id,
    s.developer_id,
    sp.project_id,
    p.canonical_name AS project_canonical_name,
    s.situation,
    s.system_template,
    s.metadata,
    s.render_templates,
    s.token_budget,
    s.context_overflow,
    s.forward_tool_calls,
    s.recall_options,
    s.created_at,
    s.updated_at
FROM sessions s
JOIN sessions_with_projects sp ON s.session_id = sp.session_id AND s.developer_id = sp.developer_id
JOIN projects p ON sp.project_id = p.project_id;

-- Create project_tasks view
CREATE OR REPLACE VIEW project_tasks AS
SELECT
    t.task_id,
    t.developer_id,
    p.project_id,
    p.canonical_name AS project_canonical_name,
    t.agent_id,
    t.canonical_name,
    t.name,
    t.description,
    t.input_schema,
    t.inherit_tools,
    t.metadata,
    t.created_at,
    t.updated_at,
    t.version
FROM tasks t
JOIN agents a ON t.developer_id = a.developer_id AND t.agent_id = a.agent_id
JOIN project_agents pa ON a.developer_id = pa.developer_id AND a.agent_id = pa.agent_id
JOIN projects p ON pa.project_id = p.project_id;

-- Create project_executions view
CREATE OR REPLACE VIEW project_executions AS
SELECT
    e.execution_id,
    e.developer_id,
    p.project_id,
    p.canonical_name AS project_canonical_name,
    e.task_id,
    e.task_version,
    e.input,
    e.metadata,
    e.created_at
FROM executions e
JOIN tasks t ON e.developer_id = t.developer_id AND e.task_id = t.task_id AND e.task_version = t.version
JOIN agents a ON t.developer_id = a.developer_id AND t.agent_id = a.agent_id
JOIN project_agents pa ON a.developer_id = pa.developer_id AND a.agent_id = pa.agent_id
JOIN projects p ON pa.project_id = p.project_id;

-- Create project_docs view
CREATE OR REPLACE VIEW project_docs AS
WITH doc_owner_groups AS (
    SELECT
        doc_id,
        developer_id,
        array_agg(owner_id) as owner_ids
    FROM doc_owners
    GROUP BY doc_id, developer_id
),
docs_with_projects AS (
    -- Docs owned by agents that are in projects
    SELECT DISTINCT
        d.doc_id,
        d.developer_id,
        p.project_id
    FROM docs d
    JOIN doc_owner_groups dog ON d.doc_id = dog.doc_id AND d.developer_id = dog.developer_id
    JOIN project_agents pa ON pa.developer_id = d.developer_id AND pa.agent_id = ANY(dog.owner_ids)
    JOIN projects p ON pa.project_id = p.project_id
    
    UNION
    
    -- Docs owned by users that are in projects
    SELECT DISTINCT
        d.doc_id,
        d.developer_id,
        p.project_id
    FROM docs d
    JOIN doc_owner_groups dog ON d.doc_id = dog.doc_id AND d.developer_id = dog.developer_id
    JOIN project_users pu ON pu.developer_id = d.developer_id AND pu.user_id = ANY(dog.owner_ids)
    JOIN projects p ON pu.project_id = p.project_id
)
SELECT
    d.doc_id,
    d.developer_id,
    dp.project_id,
    p.canonical_name AS project_canonical_name,
    d.title,
    d.content,
    d.metadata,
    d.created_at,
    d.updated_at,
    dog.owner_ids
FROM docs d
JOIN docs_with_projects dp ON d.doc_id = dp.doc_id AND d.developer_id = dp.developer_id
JOIN projects p ON dp.project_id = p.project_id
LEFT JOIN doc_owner_groups dog ON d.doc_id = dog.doc_id AND d.developer_id = dog.developer_id;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_projects_developer_id ON projects (developer_id);
CREATE INDEX IF NOT EXISTS idx_projects_metadata ON projects USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_project_agents_agent ON project_agents (developer_id, agent_id);
CREATE INDEX IF NOT EXISTS idx_project_users_user ON project_users (developer_id, user_id);
CREATE INDEX IF NOT EXISTS idx_project_files_file ON project_files (developer_id, file_id);

-- Create trigger to automatically update updated_at for projects
CREATE OR REPLACE TRIGGER trg_projects_updated_at BEFORE UPDATE 
ON projects FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Create function to create default project for new developers
CREATE OR REPLACE FUNCTION create_default_project()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO projects (
        project_id,
        developer_id,
        canonical_name,
        name,
        metadata
    ) VALUES (
        gen_random_uuid(),
        NEW.developer_id,
        'default',
        'Default Project',
        jsonb_build_object(
            'is_default', true,
            'description', 'Default project containing all existing resources'
        )
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to create default project on new developer
CREATE TRIGGER trg_create_default_project
AFTER INSERT ON developers
FOR EACH ROW
EXECUTE FUNCTION create_default_project();

-- Create function to prevent deletion of default projects
CREATE OR REPLACE FUNCTION prevent_default_project_deletion()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.canonical_name = 'default' THEN
        RAISE EXCEPTION 'Cannot delete default project';
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to prevent deletion of default projects
CREATE TRIGGER trg_prevent_default_project_deletion
BEFORE DELETE ON projects
FOR EACH ROW
EXECUTE FUNCTION prevent_default_project_deletion();

-- Add comments to tables
COMMENT ON TABLE projects IS 'Stores project configurations and metadata for developers';
COMMENT ON TABLE project_agents IS 'Associates agents with projects';
COMMENT ON TABLE project_users IS 'Associates users with projects';
COMMENT ON TABLE project_files IS 'Associates files with projects';

-- Create default project for each existing developer
INSERT INTO projects (project_id, developer_id, canonical_name, name, metadata)
SELECT 
    gen_random_uuid(),
    developer_id,
    'default',
    'Default Project',
    jsonb_build_object(
        'is_default', true,
        'description', 'Default project containing all existing resources'
    )
FROM developers
ON CONFLICT (developer_id, canonical_name) DO NOTHING;

-- Associate all existing agents with their developer's default project
INSERT INTO project_agents (project_id, developer_id, agent_id)
SELECT 
    p.project_id,
    a.developer_id,
    a.agent_id
FROM agents a
JOIN projects p ON a.developer_id = p.developer_id AND p.canonical_name = 'default'
ON CONFLICT (project_id, agent_id) DO NOTHING;

-- Associate all existing users with their developer's default project
INSERT INTO project_users (project_id, developer_id, user_id)
SELECT 
    p.project_id,
    u.developer_id,
    u.user_id
FROM users u
JOIN projects p ON u.developer_id = p.developer_id AND p.canonical_name = 'default'
ON CONFLICT (project_id, user_id) DO NOTHING;

-- Associate all existing files with their developer's default project
INSERT INTO project_files (project_id, developer_id, file_id)
SELECT 
    p.project_id,
    f.developer_id,
    f.file_id
FROM files f
JOIN projects p ON f.developer_id = p.developer_id AND p.canonical_name = 'default'
ON CONFLICT (project_id, file_id) DO NOTHING;

COMMIT; 