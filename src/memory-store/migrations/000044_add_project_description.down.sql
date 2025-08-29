BEGIN;

-- Revert the create_default_project function to not include description
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

-- Remove description column from projects table
ALTER TABLE projects DROP COLUMN IF EXISTS description;

COMMIT; 