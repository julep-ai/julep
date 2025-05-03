BEGIN;

-- Create continuous aggregate for monthly cost per developer
CREATE MATERIALIZED VIEW usage_cost_monthly
WITH (timescaledb.continuous) AS
SELECT
    developer_id,
    time_bucket('1 month', created_at) AS bucket_start,
    SUM(cost) FILTER (WHERE NOT custom_api_used) AS monthly_cost
FROM usage
WHERE created_at < NOW()
GROUP BY developer_id, bucket_start
WITH NO DATA;

-- Create index for efficient querying
CREATE INDEX IF NOT EXISTS idx_usage_cost_monthly_developer 
ON usage_cost_monthly (developer_id, bucket_start DESC);

-- Back-fill historical data
REFRESH MATERIALIZED VIEW CONCURRENTLY usage_cost_monthly;

-- Set up continuous aggregate policy to refresh every minute
SELECT add_continuous_aggregate_policy(
    'usage_cost_monthly',
    start_offset => INTERVAL '1 month',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute'
);

-- Create view that joins with developers table for easy querying
CREATE OR REPLACE VIEW developer_cost_monthly AS
SELECT 
    m.bucket_start,
    d.developer_id,
    d.active,
    d.tags,
    m.monthly_cost
FROM usage_cost_monthly AS m
JOIN developers AS d USING (developer_id);

COMMENT ON MATERIALIZED VIEW usage_cost_monthly IS 'Continuous aggregate tracking monthly costs per developer, excluding custom API usage';
COMMENT ON VIEW developer_cost_monthly IS 'View combining monthly costs with developer metadata';

COMMIT; 