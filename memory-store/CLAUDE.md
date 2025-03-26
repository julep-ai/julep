# Memory Store

## Overview
Memory-store is Julep's PostgreSQL-based persistent storage layer for agents, sessions, tasks, and related data. It uses TimescaleDB with advanced vector search capabilities for document storage and retrieval.

## Architecture
- **Database**: TimescaleDB (PostgreSQL extension) with vector search capabilities
- **Vector Search**: Uses pgvector, vectorscale and OpenAI embeddings for semantic search
- **Migrations**: Uses golang-migrate for schema management
- **Hypertables**: Time-series optimized tables for transitions and execution data

## Key Components

### Core Data Models
- `developers`: Root entity for multi-tenancy
- `users`: End-users who interact with agents
- `agents`: AI agent configurations with model settings and instructions
- `tools`: Functionality exposed to agents (API integrations, etc.)
- `tasks`: Workflow definitions for agent execution
- `workflows`: Step-by-step execution plans for tasks
- `sessions`: Conversation contexts for users and agents
- `executions`: Task execution instances
- `transitions`: State transitions in workflow execution (hypertable)
- `files`: Stored files for agent consumption
- `docs`: Knowledge base documents for agents with vector embeddings

### Search Capabilities
- **Vector Search**: Semantic similarity using OpenAI embeddings (1024 dimensions)
- **Text Search**: Full-text search with tsquery and trigram matching
- **Hybrid Search**: Combined vector and text search with configurable weights
- **Multiple Languages**: Support for various languages with specialized text configurations

### Schema Design Patterns
1. **Timescale Hypertables**: Time-partitioned tables for high-volume data
2. **Compound Keys**: (developer_id, entity_id) pattern for multi-tenancy 
3. **Primary Key Naming**: All primary keys use the pattern `{table_singular}_id` (e.g., `agent_id`, `developer_id`, `secret_id`)
4. **JSON Metadata**: Flexible metadata fields as JSONB type
5. **Triggers**: Automatic timestamp and validation management
6. **Domain Validation**: Constraints and triggers enforce data integrity
7. **Deferred Constraints**: Handles circular references between tools and tasks

## Search Implementation
- **Text-based**: Uses tsvector/tsquery with custom language configurations and unaccent
- **Vector-based**: Uses pgvector with DiskANN indexing for ANN (Approximate Nearest Neighbor) search
- **Hybrid Search**: Distribution-Based Score Fusion (DBSF) for combining text and vector scores
- **Document Processing**: Recursive chunking with smart separators to handle large documents

## Optimization Features
- **GIN Indexes**: For JSONB metadata and full-text search
- **Trigram Indexes**: For fuzzy text matching
- **Compression**: For large text fields and hypertables
- **Partitioning**: Time-based and hash-based for transitions table
- **Continuous Views**: For derived data like execution status

## Technical Details
1. **Connection String**: `postgres://postgres:PASSWORD@0.0.0.0:5432/postgres?sslmode=disable`
2. **Text Processing**: Uses unaccent, pg_trgm, and language-specific dictionaries
3. **Vectorization**: Uses TimescaleDB's pgai vectorizer-worker service
4. **Migration Path**: Sequential migrations for incremental schema updates
5. **State Machine**: Strict transition validation with defined state flows

## Docker Components
- `memory-store`: TimescaleDB container with vector extensions
- `vectorizer-worker`: Processes document embedding generation
- `migration`: Applies DB schema migrations

## Migration Patterns
- Migration numbers (000001 to 000032+) represent sequential schema evolution
- Each migration has reversible up/down scripts for safe deployments
- Progressive enhancement pattern with feature flags and backward compatibility