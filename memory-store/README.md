### prototyping flow:

1. Install `migrate` (golang-migrate)
2. In a separate window, `docker compose up db vectorizer-worker` to start db instances
3. `cd memory-store` and `migrate -database "postgres://postgres:postgres@0.0.0.0:5432/postgres?sslmode=disable" -path  ./migrations up` to apply the migrations
4. `pip install --user -U pgcli`
5. `pgcli "postgres://postgres:postgres@localhost:5432/postgres"`

For creating a migration:
`migrate -database "postgres://postgres:postgres@0.0.0.0:5432/postgres?sslmode=disable" -path migrations create -ext sql -seq -dir migrations switch_to_hypercore`

### Usage table
New reference columns were added in migration `000042_usage_reference_fields`:
`execution_id`, `transition_id`, `session_id`, `entry_id`, and `provider`.
