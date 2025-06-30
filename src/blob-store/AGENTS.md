# AGENTS.md - blob-store

This directory contains the blob storage service configuration using SeaweedFS for S3-compatible object storage.

Key Uses
- Bash commands:
  - cd blob-store
  - docker-compose up seaweedfs
  - docker-compose -f docker-compose-ha.yml up  # High availability mode
- Core files:
  - `docker-compose.yml` for single-instance deployment
  - `docker-compose-ha.yml` for high-availability deployment
  - `entrypoint.sh` for container initialization
  - `s3.json.template` for S3 API configuration
- Configuration guidelines:
  - Set `S3_ACCESS_KEY` and `S3_SECRET_KEY` environment variables
  - Use `DEBUG=true` for troubleshooting (prints config in logs)
- Testing instructions:
  - Health check: `curl http://localhost:9333/cluster/healthz`
  - S3 API test: `curl http://localhost:8333/`
- Repository etiquette:
  - Don't commit actual S3 credentials to version control
- Developer environment:
  - Requires Docker and Docker Compose
- Unexpected behaviors:
  - SeaweedFS data persists in named Docker volume `seaweedfs_data`

# Blob Store Service

## Overview
The blob-store service provides S3-compatible object storage using SeaweedFS, serving as the file storage backend for the Julep platform. It handles file uploads, downloads, and storage for agents, tasks, and user content.

## Architecture
- **Storage Engine**: SeaweedFS distributed file system
- **API Interface**: S3-compatible REST API
- **Data Persistence**: Docker volume-backed storage
- **Deployment**: Containerized with Docker Compose

## Key Components

### SeaweedFS Services
- **Master**: Cluster coordination and metadata (port 9333)
- **Volume**: Data storage and replication (port 28080) 
- **Filer**: File system interface (port 8888)
- **S3 Gateway**: S3-compatible API (port 8333)

### Configuration Files
- `s3.json.template`: S3 API configuration template
- `entrypoint.sh`: Container startup script with validation
- `docker-compose.yml`: Single-instance deployment
- `docker-compose-ha.yml`: High-availability deployment

## Storage Features
- S3-compatible API for seamless integration
- Distributed storage with automatic replication
- Horizontal scaling support
- Built-in data integrity and consistency
- Metrics endpoint for monitoring (port 9321)

## Environment Variables
- `S3_ACCESS_KEY`: S3 API access key (required)
- `S3_SECRET_KEY`: S3 API secret key (required)
- `DEBUG`: Enable debug logging (optional, default: false)
- `TAG`: Docker image tag (optional, default: dev)

## API Endpoints
- `http://localhost:8333/`: S3-compatible API
- `http://localhost:9333/cluster/healthz`: Health check
- `http://localhost:8888/`: Filer web interface
- `http://localhost:9321/metrics`: Prometheus metrics

## Deployment Modes
1. **Single Instance**: Basic deployment for development
2. **High Availability**: Multi-node deployment for production
3. **External Volume**: Persistent data storage across container restarts

## Integration Points
- Used by `agents-api` for file storage via S3 client
- Integrates with file upload/download endpoints
- Supports large payload storage for Temporal workflows
- Provides persistent storage for agent knowledge bases

## Monitoring
- Health checks via HTTP endpoints
- Prometheus metrics for storage and performance monitoring
- Docker container health checks with automatic restart
- Volume usage and replication status monitoring