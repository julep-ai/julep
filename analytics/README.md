# Julep Analytics Service

This service provides a Metabase analytics dashboard for the Julep platform, allowing users to visualize and analyze data from the PostgreSQL database.

## Overview

The analytics service uses Metabase, an open-source business intelligence tool, to provide:
- Interactive dashboards and visualizations
- SQL query interface for data exploration
- Scheduled reports and alerts
- User access management

## Architecture

- **Service**: Metabase (latest version)
- **Database**: Connects to the same PostgreSQL instance as agents-api
- **Routing**: Exposed via Traefik gateway at `/analytics`
- **SSL**: Automatically handled by Traefik with Let's Encrypt

## Configuration

### Environment Variables

- `MEMORY_STORE_PASSWORD`: Password for PostgreSQL connection (default: `julep_secure_password`)
- `JULEP_HOST`: Host domain for the analytics URL (default: `localhost`)
- `TAG`: Docker image tag (default: `dev`)

### Database Connection

Metabase connects to the PostgreSQL database with:
- Host: `memory-store`
- Port: `5432`
- Database: `postgres` (for Julep data), `metabase` (for Metabase metadata)
- Username: `postgres`
- Password: Value of `MEMORY_STORE_PASSWORD`

## Deployment

### Using Docker Compose

```bash
# Deploy with other services
docker compose --profile multi-tenant up -d

# Deploy only analytics
docker compose -f analytics/docker-compose.yml up -d
```

### Building the Image

```bash
# Using docker-bake
docker buildx bake analytics

# Using docker build
docker build -t julepai/analytics:dev analytics/
```

## Access

Once deployed, the analytics dashboard is available at:
- Local: `http://localhost:3001`
- Via Gateway: `https://<JULEP_HOST>/analytics`

### Initial Setup

1. Navigate to the analytics URL
2. Create an admin account
3. Connect to the Julep database:
   - Database Type: PostgreSQL
   - Host: `memory-store`
   - Port: `5432`
   - Database: `postgres`
   - Username: `postgres`
   - Password: (use `MEMORY_STORE_PASSWORD` value)

## Security

- Authentication is handled by Metabase's built-in user management
- SSL/TLS is provided by Traefik gateway
- Database credentials are managed via environment variables
- CORS headers are configured in Traefik

## Monitoring

Health check endpoint: `http://analytics:3000/api/health`

## Development

### Local Development

```bash
# Run Metabase locally
docker run -d -p 3000:3000 \
  -e MB_DB_TYPE=postgres \
  -e MB_DB_HOST=localhost \
  -e MB_DB_PORT=5432 \
  -e MB_DB_DBNAME=metabase \
  -e MB_DB_USER=postgres \
  -e MB_DB_PASS=your_password \
  --name metabase metabase/metabase
```

### Customization

To customize Metabase:
1. Modify environment variables in `docker-compose.yml`
2. Add custom plugins or themes via Dockerfile
3. Configure additional settings via Metabase admin panel

## Troubleshooting

### Common Issues

1. **Cannot connect to database**
   - Verify PostgreSQL is running
   - Check network connectivity between containers
   - Confirm credentials are correct

2. **Analytics not accessible via gateway**
   - Check Traefik configuration
   - Verify analytics service is healthy
   - Review gateway logs

3. **Metabase setup wizard appears**
   - This is normal on first run
   - Complete the setup to initialize Metabase

## AIDEV-NOTE: Analytics service integrated with existing Julep infrastructure