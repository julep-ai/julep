### prototyping flow:

1. Install `migrate` (golang-migrate)
2. In a separate window, `docker compose up db vectorizer-worker` to start db instances
3. `cd memory-store` and `migrate -database "postgres://postgres:postgres@0.0.0.0:5432/postgres?sslmode=disable" -path  ./migrations up` to apply the migrations
4. `pip install --user -U pgcli`
5. `pgcli "postgres://postgres:postgres@localhost:5432/postgres"`
