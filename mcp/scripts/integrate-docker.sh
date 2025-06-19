#!/bin/bash

# Script to verify MCP server integration with main Julep docker-compose

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/../.."
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
MCP_COMPOSE_FILE="$PROJECT_ROOT/mcp/docker-compose.yml"

echo "Verifying Julep Unified MCP Server integration..."

# Check if docker-compose.yml exists
if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
    echo "Error: docker-compose.yml not found at $DOCKER_COMPOSE_FILE"
    exit 1
fi

# Check if MCP is included in main docker-compose
if grep -q "./mcp/docker-compose.yml" "$DOCKER_COMPOSE_FILE"; then
    echo "✓ MCP service is already integrated in main docker-compose.yml"
else
    echo "✗ MCP service is not integrated in main docker-compose.yml"
    echo ""
    echo "To integrate, add the following line to the 'include:' section:"
    echo "  - ./mcp/docker-compose.yml"
fi

echo ""
echo "MCP Service Configuration:"
echo "=========================="
echo "Service name: mcp"
echo "Container name: mcp"
echo "HTTP port: 3000 (internal)"
echo "Gateway path: /mcp"
echo "Health check: /mcp/health"
echo ""
echo "Required environment variables:"
echo "- JULEP_API_KEY: API key for SDK authentication"
echo "- AGENTS_API_URL: Backend API URL (default: http://agents-api:8080)"
echo ""
echo "To start the MCP service:"
echo "  docker-compose up -d mcp"
echo ""
echo "To check logs:"
echo "  docker-compose logs -f mcp"
echo ""
echo "To test the service:"
echo "  curl http://localhost/mcp/health"