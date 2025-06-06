# Use the official Metabase image
FROM metabase/metabase:latest

# Install PostgreSQL client for database initialization
USER root
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# Copy initialization scripts
COPY init-metabase-db.sh /app/init-metabase-db.sh
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/init-metabase-db.sh /app/entrypoint.sh

# Switch back to metabase user
USER metabase

# AIDEV-NOTE: Custom image with database initialization support

# Expose the default Metabase port
EXPOSE 3000

# Use custom entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Metabase will use environment variables for configuration
# MB_DB_TYPE, MB_DB_HOST, MB_DB_PORT, MB_DB_DBNAME, MB_DB_USER, MB_DB_PASS