# Julep Deployment Configurations

This directory contains various Docker Compose configurations for deploying Julep in different scenarios. Each configuration is tailored to specific use cases and deployment requirements.

## Available Configurations

### 1. Single-Tenant Mode with CPU Embeddings & Managed DB
- **File:** `docker-compose.single-tenant-cpu-managed.yml`
- **Description:** Deploys Julep in single-tenant mode using CPU-based embedding services with managed Temporal and LiteLLM databases.
- **Suitable for:** Development, testing, or small-scale deployments prioritizing simplicity and cost-effectiveness.

### 2. Multi-Tenant Mode with CPU Embeddings & Managed DB
- **File:** `docker-compose.multi-tenant-cpu-managed.yml`
- **Description:** Deploys Julep in multi-tenant mode using CPU-based embedding services with managed Temporal and LiteLLM databases.
- **Suitable for:** Multi-tenant environments requiring manageable complexity with efficient resource usage.

### 3. Single-Tenant Mode with GPU Embeddings & Managed DB
- **File:** `docker-compose.single-tenant-gpu-managed.yml`
- **Description:** Deploys Julep in single-tenant mode using GPU-based embedding services with managed Temporal and LiteLLM databases.
- **Suitable for:** Single-tenant deployments needing enhanced performance through GPU-powered embeddings.

### 4. Multi-Tenant Mode with GPU Embeddings & Managed DB
- **File:** `docker-compose.multi-tenant-gpu-managed.yml`
- **Description:** Deploys Julep in multi-tenant mode using GPU-based embedding services with managed Temporal and LiteLLM databases.
- **Suitable for:** Large-scale multi-tenant deployments demanding high-performance embeddings.

### 5. Single-Tenant Mode with CPU Embeddings & Self-Hosted DB
- **File:** `docker-compose.single-tenant-cpu-selfhosted.yml`
- **Description:** Deploys Julep in single-tenant mode using CPU-based embedding services with self-hosted Temporal and LiteLLM databases.
- **Suitable for:** Deployments where controlling the database infrastructure is preferred over managed services.

### 6. Multi-Tenant Mode with CPU Embeddings & Self-Hosted DB
- **File:** `docker-compose.multi-tenant-cpu-selfhosted.yml`
- **Description:** Deploys Julep in multi-tenant mode using CPU-based embedding services with self-hosted Temporal and LiteLLM databases.
- **Suitable for:** Multi-tenant deployments with greater control over database services, ideal for organizations with specific compliance or customization needs.

### 7. Single-Tenant Mode with GPU Embeddings & Self-Hosted DB
- **File:** `docker-compose.single-tenant-gpu-selfhosted.yml`
- **Description:** Deploys Julep in single-tenant mode using GPU-based embedding services with self-hosted Temporal and LiteLLM databases.
- **Suitable for:** High-performance single-tenant deployments that require self-managed databases for specialized configurations.

### 8. Multi-Tenant Mode with GPU Embeddings & Self-Hosted DB
- **File:** `docker-compose.multi-tenant-gpu-selfhosted.yml`
- **Description:** Deploys Julep in multi-tenant mode using GPU-based embedding services with self-hosted Temporal and LiteLLM databases.
- **Suitable for:** High-performance, multi-tenant deployments that require full control over both embedding services and database infrastructure.

## Configuration Components

Each configuration file combines the following components:

- **Tenancy Mode:** Single-tenant or Multi-tenant
- **Embedding Service:** CPU-based or GPU-based
- **Database Management:** Managed or Self-hosted

## Additional Services

- **Temporal UI:** Available as an optional add-on for all configurations to provide a web-based interface for monitoring Temporal workflows.

## Choosing a Configuration

Select the configuration that best matches your deployment requirements, considering factors such as:

- Number of tenants
- Performance needs
- Infrastructure control preferences
- Scalability requirements
- Development vs. Production environment

Refer to the individual Docker Compose files for detailed service configurations and environment variable requirements.