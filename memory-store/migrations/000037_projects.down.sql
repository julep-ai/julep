BEGIN;

-- Drop all association tables first (because they reference projects)
DROP TABLE IF EXISTS project_agents;
DROP TABLE IF EXISTS project_users;
DROP TABLE IF EXISTS project_sessions;
DROP TABLE IF EXISTS project_tasks;
DROP TABLE IF EXISTS project_executions;
DROP TABLE IF EXISTS project_docs;
DROP TABLE IF EXISTS project_files;

-- Drop projects table
DROP TABLE IF EXISTS projects;

COMMIT; 