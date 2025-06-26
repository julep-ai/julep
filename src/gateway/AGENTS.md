# AGENTS.md - gateway

This directory contains the API gateway service using Traefik for routing and middleware.

Key Uses
- Bash commands:
  - cd gateway
  - docker-compose up gateway
- Core files:
  - `docker-compose.yml` for container deployment
  - `traefik.yml.template` for Traefik configuration template
  - `entrypoint.sh` for container initialization
  - `Dockerfile` for custom Traefik image
- Configuration guidelines:
  - Set `JWT_SHARED_KEY` for authentication
  - Configure `AGENTS_API_URL` for backend routing
  - Set SSL/TLS environment variables for HTTPS
- Testing instructions:
  - Health check: `curl http://localhost:80/api/healthz`
  - API docs: `curl http://localhost:80/api/docs`
- Repository etiquette:
  - Don't commit JWT keys or certificates to version control
- Developer environment:
  - Requires Docker and Docker Compose
  - LetsEncrypt volume for SSL certificates
- Unexpected behaviors:
  - Routes have priority ordering for path matching
  - JWT plugin requires custom Traefik build

# Gateway Service

## Overview
The gateway service provides a unified entry point for the Julep platform using Traefik as a reverse proxy. It handles routing, authentication, CORS, SSL termination, and load balancing for all platform services.

## Architecture
- **Proxy Engine**: Traefik reverse proxy with dynamic configuration
- **Authentication**: JWT-based authentication middleware
- **SSL/TLS**: Let's Encrypt automatic certificate management
- **Load Balancing**: Service discovery and health checking

## Key Components

### Traefik Configuration
- **Routers**: Route definition and rule matching
- **Middlewares**: Request/response processing pipeline
- **Services**: Backend service configuration
- **Entrypoints**: Port and protocol listeners

### Routing Rules
- `/api/*` → agents-api service (with JWT auth)
- `/api/temporal/*` → agents-api internal endpoints
- `/api/docs` → API documentation (no auth)
- `/api/healthz` → Health check endpoint
- `/tasks-ui/*` → Temporal UI service
- `/v1/graphql` → Hasura GraphQL endpoint
- `/` → Redirect to API documentation

### Middleware Chain
1. **CORS Headers**: Cross-origin resource sharing
2. **JWT Authentication**: Token validation and user identification
3. **Header Injection**: API key and developer headers
4. **Path Stripping**: Clean URLs for backend services

## Environment Variables
- `JWT_SHARED_KEY`: Shared secret for JWT validation (required)
- `AGENTS_API_URL`: Backend API service URL (default: http://agents-api-multi-tenant:8080)
- `TEMPORAL_UI_PUBLIC_URL`: Temporal UI service URL
- `HASURA_URL`: Hasura GraphQL service URL
- `AGENTS_API_KEY`: API key for backend authentication
- `TRAEFIK_LOG_LEVEL`: Logging verbosity (default: INFO)
- `GATEWAY_PORT`: Gateway listening port (default: 80)

## Security Features
- JWT token validation with HS512 algorithm
- API key injection for backend services
- CORS policy enforcement
- SSL/TLS termination with automatic certificates
- Request rate limiting and health checks

## Service Discovery
- **Agents API**: Main platform API with authentication
- **Temporal UI**: Workflow monitoring interface
- **Hasura**: GraphQL API for data access
- **Internal APIs**: System-level endpoints

## SSL/TLS Configuration
- Let's Encrypt ACME challenge for automatic certificates
- Certificate storage in persistent volume
- HTTPS redirect and HSTS headers
- Configurable domains and certificate resolvers

## Monitoring & Observability
- Health check endpoints on all routes
- Access logs with request/response details
- Metrics endpoint (localhost:8082) for Prometheus
- Service health checking and automatic failover

## Development Features
- File watching for configuration reloads
- Debug logging for troubleshooting
- Local development without SSL
- Hot reload for template changes

## Custom Plugins
- **JWT Plugin**: Custom authentication middleware
- **Header Manipulation**: Dynamic header injection
- **Path Rewriting**: URL transformation for backends

## Integration Points
- Frontend applications connect via gateway
- Backend services receive authenticated requests
- Monitoring systems scrape metrics
- SSL certificates managed automatically