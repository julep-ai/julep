# Use the official Metabase image
FROM metabase/metabase:latest

# Install PostgreSQL client for database initialization
USER root

# Check if we're on Alpine (apk) or Debian/Ubuntu (apt-get) and install postgresql-client accordingly  
RUN if command -v apk > /dev/null; then \
        apk add --no-cache postgresql-client; \
    elif command -v apt-get > /dev/null; then \
        apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*; \
    elif command -v yum > /dev/null; then \
        yum install -y postgresql; \
    else \
        echo "No supported package manager found"; exit 1; \
    fi

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