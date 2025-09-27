-- Drop the table (this will automatically drop associated indexes and triggers)
DROP TABLE IF EXISTS developers CASCADE;

-- Note: The update_updated_at_column() function is not dropped as it might be used by other tables
