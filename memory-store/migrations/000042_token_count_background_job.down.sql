BEGIN;

DROP FUNCTION IF EXISTS optimized_update_token_count_after;
-- Optionally drop any background job registered manually
-- SELECT remove_job(job_id) FROM timescaledb_information.jobs WHERE job_name = 'refresh_entry_token_counts';

COMMIT;
