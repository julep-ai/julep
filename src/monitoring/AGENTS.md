# AGENTS.md - monitoring

This directory contains monitoring and observability stack using Prometheus, Grafana, and Portainer.

Key Uses
- Bash commands:
  - cd monitoring
  - docker-compose --profile multi-tenant up  # Full monitoring stack
  - docker-compose --profile monitor up       # Portainer only
- Core files:
  - `docker-compose.yml` for monitoring services
  - `prometheus/config/prometheus.yml` for metrics collection
  - `grafana/provisioning/` for dashboards and data sources
  - `grafana/dashboard.yaml` for dashboard configuration
- Configuration guidelines:
  - Set `GRAFANA_ADMIN_PASSWORD` for secure access
  - Configure Prometheus targets in `prometheus.yml`
  - Add custom dashboards to `grafana/provisioning/dashboards/`
- Testing instructions:
  - Grafana UI: `http://localhost:3000` (admin/password)
  - Portainer UI: `http://localhost:8383` (admin/password)
  - Prometheus targets: Check service discovery and health
- Repository etiquette:
  - Don't commit admin passwords to version control
  - Use external volumes for data persistence
- Developer environment:
  - Requires Docker and Docker Compose
  - External volumes for persistent data storage
- Unexpected behaviors:
  - Grafana provisions dashboards automatically on startup
  - Prometheus scrapes require service network connectivity

# Monitoring Service

## Overview
The monitoring service provides comprehensive observability for the Julep platform using Prometheus for metrics collection, Grafana for visualization, and Portainer for container management. It enables real-time monitoring, alerting, and performance analysis.

## Architecture
- **Metrics Collection**: Prometheus with multi-target scraping
- **Visualization**: Grafana with pre-configured dashboards
- **Container Management**: Portainer for Docker monitoring
- **Data Persistence**: External volumes for metric storage

## Key Components

### Prometheus
- **Purpose**: Metrics collection and time-series database
- **Targets**: Agents API, Worker, Temporal services
- **Scrape Interval**: 5-second collection frequency
- **Storage**: External volume for metric persistence

### Grafana
- **Purpose**: Metrics visualization and dashboarding
- **Port**: 3000 (HTTP interface)
- **Authentication**: Configurable admin credentials
- **Provisioning**: Automatic dashboard and datasource setup

### Portainer
- **Purpose**: Docker container management and monitoring
- **Port**: 8383 (localhost only)
- **Access**: Web-based container management interface
- **Security**: Admin credentials required

## Pre-configured Dashboards

### Temporal Monitoring
- **Advanced Visibility**: Detailed workflow metrics
- **Cluster Monitoring**: Kubernetes-specific dashboards
- **History Service**: Historical data analysis
- **Matching Service**: Task matching performance
- **Worker Service**: Worker node monitoring

### Service-specific Dashboards
- **Server General**: Overall server performance
- **SDK General**: Client SDK metrics
- **SDK Java**: Java-specific SDK monitoring
- **Frontend Service**: UI service performance
- **Requests Metrics**: API request analysis
- **Queries Metrics**: Database query performance

## Environment Variables
- `GRAFANA_ADMIN_PASSWORD`: Admin password for Grafana (default: julep_grafana_admin)
- `GRAFANA_ADMIN_USER`: Admin username for Grafana (default: admin)
- `PORTAINER_ADMIN_USER`: Admin username for Portainer
- `PORTAINER_ADMIN_PASSWORD`: Admin password for Portainer

## Deployment Profiles
1. **Multi-tenant**: Full monitoring stack with Prometheus and Grafana
2. **Monitor**: Portainer-only deployment for container management

## Metrics Collection

### Scrape Targets
- **Agents API**: Main API service metrics (port 8080)
- **Worker**: Background worker metrics (port 14000)  
- **Temporal**: Workflow engine metrics (port 15000)

### Metrics Categories
- **Request Metrics**: HTTP request rates, latencies, errors
- **System Metrics**: CPU, memory, disk usage
- **Application Metrics**: Custom business logic metrics
- **Database Metrics**: Query performance and connection pools

## Data Persistence
- **Prometheus Data**: External volume `prometheus_data`
- **Grafana Data**: External volume `grafana_data`
- **Portainer Data**: External volume `portainer_data`

## Alerting Configuration
- **Alertmanagers**: Configurable alert routing
- **Evaluation Interval**: 5-second rule evaluation
- **Notification Channels**: Email, Slack, webhooks
- **Alert Rules**: Custom alerting conditions

## Dashboard Features
- **Real-time Metrics**: Live data visualization
- **Historical Analysis**: Time-based trend analysis
- **Multi-service Views**: Cross-service correlation
- **Custom Queries**: PromQL query interface
- **Export/Import**: Dashboard portability

## Security Features
- **Authentication**: Admin credential protection
- **Network Isolation**: Service-specific network access
- **Read-only Access**: Optional viewer accounts
- **Data Encryption**: Transport-level security

## Integration Points
- **Agents API**: Exposes `/metrics` endpoint for Prometheus
- **Temporal**: Provides workflow and activity metrics
- **Worker Services**: Background job monitoring
- **Infrastructure**: System-level resource monitoring

## Operational Procedures
- **Health Checks**: Automated service health monitoring
- **Data Retention**: Configurable metric retention policies
- **Backup/Restore**: Volume-based data backup
- **Scaling**: Horizontal scaling for high-volume metrics

## Troubleshooting
- **Service Discovery**: Check Prometheus targets page
- **Dashboard Loading**: Verify Grafana provisioning logs
- **Data Missing**: Confirm scrape target connectivity
- **Performance**: Monitor Prometheus resource usage