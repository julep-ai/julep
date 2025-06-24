#!/bin/bash

# Build script for unified MCP server

echo "Building Julep Unified MCP Server..."

# Clean dist directory
rm -rf dist

# Build TypeScript
echo "Compiling TypeScript..."
npx tsc

# Make the output executable
chmod +x dist/index.js

# Copy necessary files
cp package.json dist/
cp README.md dist/ 2>/dev/null || true

echo "Build complete!"