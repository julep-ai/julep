BEGIN;

SELECT
    remove_compression_policy ('entries');

SELECT
    remove_compression_policy ('transitions');

ALTER TABLE entries
SET
    (timescaledb.compress = FALSE);

ALTER TABLE transitions
SET
    (timescaledb.compress = FALSE);

COMMIT;
