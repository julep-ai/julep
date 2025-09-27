-- Remove the not null constraint
ALTER TABLE sessions ALTER COLUMN forward_tool_calls DROP NOT NULL;

-- Remove the comment
COMMENT ON COLUMN sessions.forward_tool_calls IS NULL; 