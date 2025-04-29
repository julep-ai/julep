BEGIN;

-- Drop triggers
DROP TRIGGER IF EXISTS trg_prevent_default_project_deletion ON projects;
DROP TRIGGER IF EXISTS trg_create_default_project ON developers;

-- Drop functions
DROP FUNCTION IF EXISTS prevent_default_project_deletion();
DROP FUNCTION IF EXISTS create_default_project();

-- Drop views
DROP VIEW IF EXISTS project_docs;
DROP VIEW IF EXISTS project_executions;
DROP VIEW IF EXISTS project_tasks;
DROP VIEW IF EXISTS project_sessions;

-- Drop indexes
DROP INDEX IF EXISTS idx_project_files_file;
DROP INDEX IF EXISTS idx_project_users_user;
DROP INDEX IF EXISTS idx_project_agents_agent;
DROP INDEX IF EXISTS idx_projects_metadata;
DROP INDEX IF EXISTS idx_projects_developer_id;

-- Drop association tables
DROP TABLE IF EXISTS project_files;
DROP TABLE IF EXISTS project_users;
DROP TABLE IF EXISTS project_agents;

-- Drop main table
DROP TABLE IF EXISTS projects;

COMMIT; 