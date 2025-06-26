BEGIN;

-- Insert system developer with all zeros UUID
INSERT INTO developers (
    developer_id,
    email,
    active,
    tags,
    settings
) VALUES (
    '00000000-0000-0000-0000-000000000000',
    'system@internal.julep.ai',
    true,
    ARRAY['system', 'paid'],
    '{}'::jsonb
) ON CONFLICT (developer_id) DO NOTHING;

COMMIT;
