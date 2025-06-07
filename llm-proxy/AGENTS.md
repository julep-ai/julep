# AGENTS.md - llm-proxy

This directory contains the LLM proxy service using LiteLLM for unified model access.

Key Uses
- Bash commands:
  - cd llm-proxy
  - docker-compose --profile self-hosted-db up  # With local database
  - docker-compose --profile managed-db up      # With external database
- Core files:
  - `docker-compose.yml` for service deployment
  - `litellm-config.yaml` for model configuration
  - `.keys/` directory for API key files (gitignored)
- Configuration guidelines:
  - Set API keys for each model provider via environment variables
  - Configure `LITELLM_MASTER_KEY` for proxy authentication
  - Set database and Redis URLs for persistence and caching
- Testing instructions:
  - Health check: `curl http://localhost:4000/health`
  - Model list: `curl http://localhost:4000/models`
  - Chat completion: `curl -X POST http://localhost:4000/chat/completions`
- Repository etiquette:
  - Don't commit API keys or secrets to version control
  - Store keys in `.keys/` directory or environment variables
- Developer environment:
  - Requires Docker and Docker Compose
  - Optional: PostgreSQL and Redis services
- Unexpected behaviors:
  - Model routing uses simple-shuffle strategy
  - Caching enabled by default with Redis backend

# LLM Proxy Service

## Overview
The LLM proxy service provides unified access to multiple Large Language Model providers through a single OpenAI-compatible API using LiteLLM. It handles model routing, caching, rate limiting, and request/response transformation.

## Architecture
- **Proxy Engine**: LiteLLM with OpenAI-compatible API
- **Model Router**: Load balancing across multiple providers
- **Caching Layer**: Redis-based response caching
- **Database**: PostgreSQL for logging and analytics
- **Workers**: Multi-worker deployment for performance

## Key Components

### LiteLLM Configuration
- **Model List**: Centralized model definitions and routing
- **Router Settings**: Load balancing and fallback strategies
- **Cache Settings**: Redis configuration for response caching
- **General Settings**: Authentication and database configuration

### Supported Providers
1. **OpenAI**: GPT-4, GPT-4 Turbo, GPT-4o, o1, o3 models
2. **Anthropic**: Claude 3.5 Sonnet, Claude 3 Opus/Sonnet/Haiku
3. **Google**: Gemini 1.5 Pro, Gemini 2.0 Flash, Gemini 2.5 Pro Preview
4. **Groq**: Llama 3.1 70B/8B models
5. **OpenRouter**: Mistral, Qwen, DeepSeek, Meta Llama models
6. **Cerebras**: Llama 3.1/3.3/4 Scout models
7. **Voyage**: Embedding models
8. **Local Models**: Text embeddings inference service

### Model Categories
- **Paid Models**: Premium models requiring API keys and billing
- **Free Models**: Models with free tiers or no cost
- **Embedding Models**: Text embedding and vector generation

## Environment Variables
- `LITELLM_MASTER_KEY`: Master authentication key for the proxy
- `DATABASE_URL`: PostgreSQL connection string for logging
- `REDIS_URL`: Redis connection string for caching
- **Provider API Keys**:
  - `OPENAI_API_KEY`
  - `ANTHROPIC_API_KEY`
  - `GEMINI_API_KEY`
  - `GROQ_API_KEY`
  - `OPENROUTER_API_KEY`
  - `VOYAGE_API_KEY`
  - `CEREBRAS_API_KEY`
  - And others for additional providers

## Deployment Profiles
1. **Self-hosted DB**: Complete local deployment with PostgreSQL and Redis
2. **Managed DB**: Use external database and Redis services
3. **Development**: File watching for configuration hot reload

## API Features
- **OpenAI Compatibility**: Drop-in replacement for OpenAI API
- **Model Routing**: Automatic selection and load balancing
- **Response Caching**: Redis-based caching with configurable TTL
- **Request Logging**: Comprehensive logging to database
- **Error Handling**: Automatic retries and fallback routing
- **Rate Limiting**: Per-user and per-model rate limits

### Router Configuration
- **Strategy**: Simple shuffle for load distribution
- **Retries**: 3 attempts with exponential backoff
- **Fallback**: Automatic failover to alternative models
- **Health Checks**: Model availability monitoring

### Caching System
- **Backend**: Redis with namespace separation
- **Key Strategy**: Request content and parameters
- **TTL**: Configurable cache expiration
- **Namespace**: `litellm_caching` for organization

## Performance Features
- **Multi-worker**: 8 workers for concurrent request handling
- **Connection Pooling**: Database and Redis connection reuse
- **Async Processing**: Non-blocking request handling
- **Resource Limits**: Memory and CPU constraints

## Monitoring & Observability
- Health check endpoints for service monitoring
- Request/response logging to PostgreSQL
- Performance metrics and analytics
- Model usage tracking and billing
- Error rates and latency monitoring

## Integration Points
- **Agents API**: Primary consumer for model requests
- **Chat Service**: Real-time conversation handling
- **Task Execution**: Model calls during workflow steps
- **Embedding Service**: Vector generation for document search

## Security Features
- Master key authentication for API access
- Per-user API key management
- Request validation and sanitization
- Rate limiting and abuse prevention
- Audit logging for compliance

## Development Tools
- Configuration hot reload during development
- Debug logging for troubleshooting
- Model testing endpoints
- Performance profiling capabilities