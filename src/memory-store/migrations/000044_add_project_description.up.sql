BEGIN;

-- Add description column to projects table
ALTER TABLE projects 
ADD COLUMN description TEXT DEFAULT NULL 
CONSTRAINT chk_projects_description_length CHECK (
    description IS NULL
    OR length(description) <= 1000
);

-- Add comment to the description column
COMMENT ON COLUMN projects.description IS 'Optional description of the project';

-- Update the create_default_project function to include description
CREATE OR REPLACE FUNCTION create_default_project()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO projects (
        project_id,
        developer_id,
        canonical_name,
        name,
        description,
        metadata
    ) VALUES (
        gen_random_uuid(),
        NEW.developer_id,
        'default',
        'Default Project',
        'Default project containing all existing resources',
        jsonb_build_object(
            'is_default', true
        )
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMIT; 