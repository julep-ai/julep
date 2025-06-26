-- Update existing null values to false
UPDATE sessions SET forward_tool_calls = false WHERE forward_tool_calls IS NULL;

-- Make the column not null
ALTER TABLE sessions ALTER COLUMN forward_tool_calls SET NOT NULL;

-- Add comment to explain the change
COMMENT ON COLUMN sessions.forward_tool_calls IS 'Whether to forward tool calls directly to the model. Default is false.'; 