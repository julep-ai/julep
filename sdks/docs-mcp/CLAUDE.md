# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **julep-docs-mcp** - an MCP (Model Context Protocol) server that provides documentation search capabilities for Julep AI (https://docs.julep.ai). It integrates with Mintlify's Trieve search infrastructure to enable intelligent documentation retrieval.

## Development Commands

```bash
# Install dependencies
npm install

# Run the MCP server
npm start

# Type check (if TypeScript source is available)
tsc --noEmit
```

## Architecture

### Core Components

1. **MCP Server** (`src/index.js`)
   - Initializes stdio-based MCP server
   - Registers search tool and dynamic endpoint tools
   - Main entry point for the application

2. **Search Integration** (`src/search.js`)
   - Fetches Mintlify configuration for "julep" subdomain
   - Uses Trieve SDK for full-text search with autocomplete
   - Returns structured results with titles, content snippets, and links

3. **Dynamic Tools System** (`src/tools/`)
   - Creates tools from endpoint configurations in `tools.json`
   - Supports various HTTP methods and authentication schemes
   - Handles environment variables for secure credentials

### Key Configuration

- **Subdomain**: "julep" (hardcoded)
- **Mintlify API**: https://leaves.mintlify.com
- **Search Provider**: Trieve (via Mintlify integration)
- **Transport**: stdio (standard MCP transport)

### Tool Definition Pattern

Tools are defined in `src/tools.json` and support:
- Multiple HTTP methods (GET, POST, etc.)
- Security parameters (headers, cookies, query params)
- Environment variable substitution for secrets
- Response content type specifications

### Error Handling

- Search errors return informative messages about connectivity/configuration issues
- Tool execution errors are propagated with context
- Missing environment variables for security parameters fail gracefully

## Important Notes

1. This is a compiled JavaScript project (from TypeScript) - edit source TypeScript files if available
2. The server communicates via stdio, making it suitable for integration with AI assistants
3. Search functionality depends on external Mintlify/Trieve services being available
4. All tools support environment variable injection for secure credential handling

## Testing

Currently no test suite is configured. When adding tests:
- Test search functionality with mock Mintlify/Trieve responses
- Verify tool creation and execution logic
- Ensure proper error handling for network failures