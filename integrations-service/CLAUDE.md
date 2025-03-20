# Integrations Service Architecture

## Overview
The integrations-service is a FastAPI-based microservice that provides a unified API for executing various external integrations. It serves as a bridge between the Julep platform and third-party services, APIs, and tools.

## Key Components

### Core Framework
- `web.py` - FastAPI application setup with router registration
- `providers.py` - Registry of all available integration providers
- `models/base_models.py` - Core models defining provider structure
- `utils/execute_integration.py` - Unified execution framework for all integrations

### Provider Model
- `BaseProvider` - Core model defining integration interface
- `BaseProviderMethod` - Defines methods (operations) available on a provider
- `ProviderInfo` - Metadata about the integration (URL, docs, icon)
- Each provider has setup, arguments, methods, and outputs

### Integration Types
1. Web Services
   - `brave` - Brave search engine integration
   - `algolia` - Algolia search service
   - `wikipedia` - Wikipedia content retrieval
   - `arxiv` - arXiv research papers search

2. Browser/UI Automation
   - `browserbase` - Cloud browser infrastructure
   - `remote_browser` - Remote browser control via Playwright
   - `spider` - Web scraping/crawling

3. Media Processing
   - `ffmpeg` - Video/audio processing
   - `cloudinary` - Cloud media management
   - `llama_parse` - Document parsing
   - `unstructured` - Document parsing/extraction

4. Communications
   - `email` - Email sending capabilities
   - `weather` - Weather information

### API Structure
- `/execute/{provider}` - Execute default method for a provider
- `/execute/{provider}/{method}` - Execute specific method on a provider
- `/integrations` - List all available integrations
- `/integrations/{provider}` - Get provider details
- `/integrations/{provider}/tool` - Get provider as OpenAI tool format

## Integration Patterns
1. **Provider Registration**
   - Define in `providers.py` with setup, methods, arguments
   - Register in `available_providers` dictionary

2. **Method Implementation** 
   - Each provider has method implementations in `utils/integrations/`
   - Methods use `@beartype` for type validation and `@retry` for resilience
   - Async execution with consistent error handling

3. **Dynamic Loading**
   - Provider modules loaded using `importlib` based on provider name
   - Methods called via `getattr` to match the requested operation

4. **OpenAI Tool Conversion**
   - Integrations can be converted to OpenAI tool format
   - Function schemas automatically generated from Pydantic models

## Type Hierarchies
- `ExecutionSetup` - Union of all provider setup types
- `ExecutionArguments` - Union of all method argument types
- `ExecutionResponse` - Union of all possible response types

## Security Patterns
- Environment variables for sensitive configuration
- API keys not hardcoded (fallback to env vars)
- API key validation and service-appropriate authentication

## Error Handling
- Consistent error format via custom exception handlers
- Retry mechanisms with exponential backoff
- Structured error responses with `ExecutionError`

## Testing
- Mock implementations in `tests/mocks/`
- Provider execution tests in `test_provider_execution.py`
- Provider definition tests in `test_providers.py`