# CLAUDE.md - documentation

This directory contains the project documentation, guides, cookbooks, and asset files.

Key Uses
- Bash commands:
  - (No build commands; docs are static markdown.)
- Core directories:
  - `concepts/`, `guides/`, `cookbooks/`, `tutorials/`, `assets/`.
- Style guidelines:
  - Markdown formatted for readability; wrap at 96 chars.
  - Use Google-style code blocks with language tags.
- Testing instructions:
  - Manually verify links and code samples.
- Repository etiquette:
  - Update `CHANGELOG.md` and navigation `SUMMARY.md` for doc changes.
- Developer environment:
  - Preview docs using any local static site generator if desired.
- Unexpected behaviors:
  - Ensure images in `assets/` render correctly in all output formats.

# Julep Documentation Structure

## Core Purpose
- Julep: Platform for building AI agents with memory, context retention, and complex task execution
- Main Components: Agents, Tasks, Sessions, Tools, Documents, Users
- Architecture: Client-side SDK + Server-side execution engine + Integrations system

## Key System Concepts

### Agents
- Definition: Configured LLM instances with specific personas and capabilities
- Components: Instructions, metadata, tools, docs
- Configuration: Name, model, system template, default settings
- Use: Power sessions and tasks as conversational or autonomous entities

### Tasks
- Definition: Multi-step workflows (similar to GitHub Actions)
- Step Types: Prompt, Evaluate, Tool Call, If-else, Foreach, Map-reduce, etc.
- Execution: Run by agents, maintain state, handle complex logic
- Input/Output: Schema-validated, supports Python expressions with $ syntax

### Sessions
- Definition: Stateful conversation contexts between users and agents
- Use: Real-time interaction, history tracking, continuous dialogue
- Features: Pausing, resuming, maintaining context across interactions

### Tools
- Types:
  - User-defined functions: Custom functions requiring client execution
  - System tools: Built-in operations for accessing Julep APIs
  - Integration tools: Pre-built connectors to external services
  - API Call tools: Direct HTTP requests to external endpoints
- Integration Categories: Communication, Search, Media processing, Web automation

### Technical Architecture
- API Layer: RESTful endpoints, authentication, rate limiting
- Task Engine: Distributed processing, state management, parallel execution
- Document Store: Vector database for semantic search, document indexing
- Security: API key auth, data encryption, access controls

## Documentation Navigation
- Introduction: Basic concepts, installation, quickstart
- Core Concepts: Detailed explanations of each main component
- Tutorials: Practical examples and walkthroughs
- Advanced: Architecture details, agentic patterns, complex workflows
- Integrations: Descriptions of supported external tools and services
- SDKs: Python and Node.js client libraries

## Developer Workflows
- CLI Usage: Project structure, commands, configuration
- Project Management: Initialization, synchronization, execution
- Templates: Available starter templates for common use cases
- Development Flow: Edit locally, sync to server, run and monitor

## Integration Categories
- Communication & Data: Email, Weather API
- Media & File Processing: LlamaParse, FFmpeg, Cloudinary, Unstructured
- Search: Arxiv, Algolia, Brave, Wikipedia
- Web & Browser: BrowserBase, Spider, Remote Browser

## Development Resources
- Discord Community: https://discord.gg/p4c7ehs4vD
- GitHub Repo: https://github.com/julep-ai/julep
- Documentation Site: https://julep.ai/docs
- Support Email: developers@julep.ai