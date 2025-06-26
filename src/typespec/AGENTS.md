# AGENTS.md - typespec

This directory contains TypeSpec definitions for APIs and code generation.

Key Uses
- Bash commands:
  - cd typespec
  - poe codegen
- Core directories:
  - `agents/`, `tasks/`, `tools/`, `sessions/`, etc. define domain models.
- Code style guidelines:
  - Use discriminated unions with `kind_` property.
  - Apply mixins (HasId, HasTimestamps, HasMetadata) consistently.
- Testing instructions:
  - Validate specs: `tsp compile`
  - Regenerate OpenAPI models: `bash scripts/generate_openapi_code.sh`
- Repository etiquette:
  - Do NOT edit generated code in `autogen/`.
- Developer environment:
  - Ensure `@typespec/openapi3` plugin is installed.
- Unexpected behaviors:
  - Alias conflicts (e.g., `if_`) require manual resolution.

# TypeSpec Architecture Documentation

## Overview
TypeSpec is a structured language for defining API contracts that serves as the source of truth for the Julep API. It generates OpenAPI specifications which are used to create client SDKs, validate implementations, and generate server-side models.

## Core Structure
- TypeSpec definitions organized by domain resources
- Each domain has `models.tsp`, `endpoints.tsp`, and `main.tsp`
- Common components for reuse across domains
- Generates OpenAPI 3.0 YAML specifications

## Domain Resources
- **projects**: Organizational units for grouping related resources
- **agents**: AI agent definitions with instructions and configuration
- **tasks**: Workflow definitions with steps, conditionals, and tool integration
- **tools**: Capabilities that agents can use (functions, integrations, system resources)
- **sessions**: Conversation containers with context management
- **entries**: Message structure and history tracking
- **executions**: Task execution state tracking with transitions
- **docs**: Document storage and retrieval with vector search
- **files**: File storage and management
- **users**: User management and authentication
- **chat**: Interaction flow and model parameters

## Step Types
- **Tool-based**: ToolCallStep, PromptStep, EvaluateStep
- **Flow control**: IfElseStep, SwitchStep, ParallelStep, ForeachStep, MapReduceStep
- **Data manipulation**: GetStep, SetStep, LogStep
- **Terminal**: ReturnStep, ErrorStep, WaitForInputStep

## Scalar Types
- **Identifiers**: uuid, canonicalName, displayName, validPythonIdentifier
- **Expressions**: PyExpression (SimpleEval-compatible), JinjaTemplate
- **Pagination**: limit, offset, sortBy, sortDirection
- **Content**: mimeType, yaml, json, eventStream

## Tool Integrations
- **Search/Knowledge**: Wikipedia, Brave, arXiv, Algolia
- **Web Browsing**: BrowserBase, Spider, RemoteBrowser
- **Media Processing**: FFmpeg, Cloudinary, Unstructured, LlamaParse
- **Communication**: Email, Weather
- **System Tools**: Anthropic specialized tools (computer, text_editor, bash)

## API Patterns
- RESTful resource endpoints with consistent CRUD operations
- Parent-child resource relationships
- Discriminated union types with `kind_` property
- Rich expression support with Python evaluation
- Streaming responses for real-time interactions
- Authentication via API keys

## Integration Points
- Sessions contain Entries (conversation history)
- Chat uses Session context
- Executions run Tasks
- Tasks use Tools for capabilities
- Agents define available Tasks and Tools

## Code Generation Pipeline
1. TypeSpec definitions (.tsp files)
2. TypeSpec compiler (`tsp compile`)
3. OpenAPI specification (YAML)
4. Pydantic models via datamodel-codegen
5. Post-processing fixes
6. Schema extraction for specific models

## Key Concepts
- Discriminated unions for type safety
- Expression language for dynamic behavior
- Parent-child resource hierarchies
- Common mixins (HasId, HasTimestamps, HasMetadata)
- Tool composability for flexible agent capabilities
