# AGENTS.md - scheduler

This directory contains the Temporal workflow engine configuration for distributed task execution.

Key Uses
- Bash commands:
  - cd scheduler
  - docker-compose --profile self-hosted-db up    # With local PostgreSQL
  - docker-compose --profile managed-db up        # With external database
  - docker-compose --profile temporal-ui up       # Web UI for monitoring
  - docker-compose --profile temporal-ui-public up # Public read-only UI
- Core files:
  - `docker-compose.yml` for Temporal services
  - `dynamicconfig/temporal-postgres.yaml` for runtime configuration
  - `cert/` directory for TLS certificates
- Configuration guidelines:
  - Set `TEMPORAL_POSTGRES_PASSWORD` for database authentication
  - Configure `TEMPORAL_ADDRESS` for service discovery
  - Adjust `dynamicconfig` for performance tuning
- Testing instructions:
  - Temporal UI: `http://localhost:9000` (full access)
  - Public UI: `http://localhost:9001` (read-only)
  - Health check: Connect to Temporal gRPC endpoint
- Repository etiquette:
  - Don't commit database passwords or certificates
  - Use external volumes for data persistence
- Developer environment:
  - Requires Docker and Docker Compose
  - PostgreSQL for workflow state persistence
- Unexpected behaviors:
  - Auto-setup includes database schema initialization
  - UI codec endpoint requires agents-api integration

# Scheduler Service

## Overview
The scheduler service provides distributed workflow orchestration using Temporal, enabling durable execution of complex, long-running tasks with built-in retry logic, state management, and fault tolerance.

## Architecture
- **Workflow Engine**: Temporal server with PostgreSQL persistence
- **UI Components**: Web interface for workflow monitoring
- **Database**: PostgreSQL for workflow state and history
- **Configuration**: Dynamic runtime configuration system

## Key Components

### Temporal Server
- **Image**: temporalio/auto-setup:1.25.2 with automatic schema setup
- **Features**: Workflow execution, activity coordination, timers
- **Persistence**: PostgreSQL-backed state storage
- **Metrics**: Prometheus endpoint on port 15000

### Temporal UI
- **Standard UI**: Full-featured workflow monitoring (port 9000)
- **Public UI**: Read-only interface for external access (port 9001)
- **Features**: Workflow visualization, execution history, debugging

### PostgreSQL Database
- **Purpose**: Workflow state and history persistence
- **Configuration**: High connection limit (1000) for concurrent workflows
- **Health Checks**: Automated readiness verification
- **Persistence**: External volume for data durability

## Environment Variables
- `TEMPORAL_POSTGRES_PASSWORD`: Database password (required)
- `TEMPORAL_POSTGRES_DB`: Database name (default: temporal)
- `TEMPORAL_POSTGRES_HOST`: Database host (default: temporal-db)
- `TEMPORAL_POSTGRES_USER`: Database user (default: temporal)
- `TEMPORAL_ADDRESS`: Temporal server address (default: temporal:7233)
- `TEMPORAL_LOG_LEVEL`: Logging verbosity (default: info)

### TLS Configuration
- `TEMPORAL_POSTGRES_TLS_ENABLED`: Enable database TLS
- `TEMPORAL_POSTGRES_TLS_DISABLE_HOST_VERIFICATION`: Skip hostname verification
- Certificate files in `/cert/` directory

## Deployment Profiles
1. **Self-hosted DB**: Complete local deployment with PostgreSQL
2. **Managed DB**: Use external PostgreSQL service
3. **Temporal UI**: Full-featured workflow monitoring interface
4. **Temporal UI Public**: Read-only public access interface

## Dynamic Configuration

### Performance Tuning
- **Matching RPS**: 600 requests per second (reduced from 1200)
- **Blob Size Limit**: 4MB maximum payload size
- **History Size Limit**: 100MB workflow history limit
- **History Count Limit**: 102400 events per workflow

### Concurrency Limits
- **Pending Activities**: 4000 maximum concurrent activities
- **Child Executions**: 4000 maximum nested workflows
- **Batch Operations**: 10000 executions per batch
- **Concurrent Batches**: 100 per namespace

## Workflow Features
- **Durable Execution**: Workflows survive system failures
- **Activity Retries**: Automatic retry with exponential backoff
- **Timers and Delays**: Built-in scheduling capabilities
- **Signal Handling**: External event processing
- **Child Workflows**: Nested workflow execution
- **Continue-as-New**: Long-running workflow optimization

## Monitoring & Observability
- **Prometheus Metrics**: Comprehensive workflow and system metrics
- **Workflow Visibility**: Real-time execution status
- **History Tracking**: Complete audit trail of workflow execution
- **Search Attributes**: Custom metadata for workflow queries

### UI Features
- **Workflow List**: Browse and filter workflows
- **Execution Details**: Step-by-step execution visualization
- **Task Queues**: Monitor worker capacity and utilization
- **Namespaces**: Multi-tenant workflow isolation
- **Cluster Information**: System health and configuration

## Integration Points
- **Agents API**: Executes workflows via Temporal client
- **Worker Processes**: Handle activity execution
- **Codec Endpoint**: Custom payload encoding/decoding
- **Monitoring**: Metrics collection via Prometheus

## Security Features
- **TLS Encryption**: Database and service communication
- **Namespace Isolation**: Multi-tenant security boundaries
- **Authentication**: Database credential management
- **Certificate Management**: Custom CA and client certificates

## Operational Procedures
- **Schema Management**: Automatic database schema setup
- **Backup/Restore**: PostgreSQL-based data backup
- **Scaling**: Horizontal scaling for high workflow volumes
- **Maintenance**: Rolling updates and configuration changes

## Development Features
- **Auto-setup**: Automatic database initialization
- **Local Development**: Self-contained deployment
- **Hot Configuration**: Dynamic config reload without restart
- **Debug Interface**: Detailed workflow execution logs

## Advanced Configuration
- **Custom Search Attributes**: Metadata indexing for queries
- **Archival**: Historical workflow data management
- **Rate Limiting**: Request throttling and load control
- **Multi-cluster**: Cross-region workflow replication

## Troubleshooting
- **Health Checks**: Database and service connectivity
- **Log Analysis**: Structured logging for debugging
- **Metrics Monitoring**: Performance and error tracking
- **UI Diagnostics**: Visual workflow execution analysis