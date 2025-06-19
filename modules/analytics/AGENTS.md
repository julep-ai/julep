# AGENTS.md - analytics

This directory contains the Metabase analytics service for the Julep platform.

Key Uses
- Bash commands:
  - cd analytics
  - docker compose up analytics
  - docker buildx bake analytics
- Core files:
  - `docker-compose.yml` for service deployment
  - `Dockerfile` for Metabase container
  - `README.md` for detailed documentation
- Configuration guidelines:
  - Set `MEMORY_STORE_PASSWORD` for database access
  - Configure `JULEP_HOST` for proper URL generation
  - Uses same PostgreSQL instance as agents-api
- Testing instructions:
  - Health check: `curl http://localhost:3001/api/health`
  - Access dashboard: `http://localhost:3001` or `https://<host>/analytics`
- Repository etiquette:
  - Don't commit Metabase database files
  - Keep sensitive configuration in environment variables
- Developer environment:
  - Requires Docker and Docker Compose
  - Connects to memory-store PostgreSQL service
- Unexpected behaviors:
  - First run shows setup wizard (this is normal)
  - Metabase creates its own database for metadata

# Analytics Service

## Overview
The analytics service provides business intelligence capabilities using Metabase, allowing users to create dashboards, run queries, and analyze data from the Julep platform's PostgreSQL database.

## Architecture
- **Analytics Engine**: Metabase (open-source BI tool)
- **Database**: Shared PostgreSQL instance with agents-api
- **Routing**: Exposed via Traefik at `/analytics` path
- **Authentication**: Metabase's built-in user management

## Key Components

### Metabase Configuration
- **Application Database**: Stores Metabase metadata in PostgreSQL
- **Data Source**: Connects to Julep's main PostgreSQL database
- **Site URL**: Configured for proper link generation
- **SSL**: Handled by Traefik gateway

### Environment Variables
- `MEMORY_STORE_PASSWORD`: PostgreSQL password
- `JULEP_HOST`: Host domain for URL configuration
- `TAG`: Docker image tag for versioning

## Integration Points
- **PostgreSQL**: Direct connection to memory-store service
- **Traefik Gateway**: Reverse proxy with SSL termination
- **Docker Network**: Shares julep-network with other services

## Security Features
- User authentication via Metabase
- SSL/TLS via Traefik
- Database credentials in environment variables
- Network isolation via Docker

## Development Workflow
1. Build image: `docker buildx bake analytics`
2. Deploy service: `docker compose up -d analytics`
3. Access dashboard: Navigate to `/analytics`
4. Complete setup wizard on first run
5. Connect to Julep database

## Monitoring
- Health endpoint at `/api/health`
- Container health checks every 30s
- Logs available via Docker

## AIDEV-NOTE: Metabase service for Julep analytics and reporting