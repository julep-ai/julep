# Julep Docs MCP Server

An MCP (Model Context Protocol) server that provides AI assistants with the ability to search and retrieve documentation from [Julep AI docs](https://docs.julep.ai).

## Overview

This MCP server integrates with Julep's documentation hosted on Mintlify, providing intelligent search capabilities through the Trieve search infrastructure. It enables AI assistants like Claude to access up-to-date Julep documentation and provide accurate information about the platform.

## Features

- **Documentation Search**: Full-text search across all Julep documentation
- **Structured Results**: Returns formatted results with titles, content snippets, and direct links
- **MCP Protocol**: Standard Model Context Protocol implementation for AI assistant integration
- **Dynamic Tool Creation**: Supports additional custom tools via configuration

## Installation

### Prerequisites

- Node.js >= 18.0.0
- npm or yarn

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd julep/sdks/docs-mcp

# Install dependencies
npm install
```

## Usage

### Running the Server

```bash
npm start
```

The server communicates via stdio (standard input/output), making it suitable for integration with MCP-compatible AI assistants.

### Integration with Claude Desktop

To use this MCP server with Claude Desktop, add the following to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "julep-docs": {
      "command": "node",
      "args": ["/path/to/julep/sdks/docs-mcp/src/index.js"],
      "cwd": "/path/to/julep/sdks/docs-mcp"
    }
  }
}
```

## Available Tools

### 1. Search Tool

Search through Julep documentation with intelligent ranking and snippets.

**Input Schema:**
```json
{
  "query": "your search query here"
}
```

**Example Response:**
```json
{
  "results": [
    {
      "title": "Getting Started with Julep",
      "content": "Julep is a platform for building AI agents...",
      "url": "https://docs.julep.ai/getting-started"
    }
  ]
}
```

### 2. Custom Tools

Additional tools can be configured by modifying `src/tools.json`. The system supports:
- Various HTTP methods (GET, POST, PUT, DELETE)
- Authentication via headers, cookies, or query parameters
- Environment variable substitution for secure credentials

## Architecture

```
src/
├── index.js          # Main server entry point
├── search.js         # Search functionality implementation
├── tools/            # Dynamic tool system
│   ├── index.js      # Tool loader and executor
│   └── helpers.js    # Utility functions
├── tools.json        # Custom tool configurations
└── config.readonly.js # Configuration constants
```

## Configuration

The server uses the following configuration:

- **Subdomain**: `julep` (hardcoded for Julep docs)
- **Mintlify API**: `https://leaves.mintlify.com`
- **Search Provider**: Trieve (via Mintlify integration)

## Development

### Adding Custom Tools

1. Edit `src/tools.json` to add new tool definitions
2. Define the endpoint, method, and parameters
3. Use environment variables for sensitive data:

```json
{
  "name": "custom_tool",
  "description": "Description of your tool",
  "endpoints": [
    {
      "method": "GET",
      "path": "/api/endpoint",
      "parameters": {
        "query": ["param1", "param2"]
      },
      "security": {
        "headers": {
          "Authorization": "Bearer ${API_KEY}"
        }
      }
    }
  ]
}
```

### Environment Variables

For tools with security requirements, set environment variables:

```bash
export API_KEY="your-api-key-here"
```

## Troubleshooting

### Common Issues

1. **Search returns no results**
   - Verify internet connectivity
   - Check if Mintlify/Trieve services are accessible
   - Ensure the search query is properly formatted

2. **Server fails to start**
   - Verify Node.js version >= 18.0.0
   - Check all dependencies are installed
   - Ensure no syntax errors in tools.json

3. **Custom tools not working**
   - Verify environment variables are set
   - Check endpoint URLs are correct
   - Validate JSON syntax in tools.json

## Contributing

When contributing to this project:

1. Follow the existing code style
2. Test search functionality after changes
3. Update tools.json documentation if adding new tools
4. Ensure Node.js 18+ compatibility

## License

[License information - check parent repository]

## Related Projects

- [Julep AI](https://julep.ai) - The main platform
- [Julep Documentation](https://docs.julep.ai) - Official documentation
- [MCP Specification](https://modelcontextprotocol.io) - Model Context Protocol docs