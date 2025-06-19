#!/bin/bash

# Test script for Julep Unified MCP Server

echo "Testing Julep Unified MCP Server..."
echo "================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test 1: List tools without authentication
echo -e "\n1. Testing tool listing without API key..."
npx tsx src/index.ts --list > /tmp/test-no-auth.txt 2>&1
if grep -q "Documentation Tools" /tmp/test-no-auth.txt; then
    echo -e "${GREEN}✓ Documentation tools listed successfully${NC}"
else
    echo -e "${RED}✗ Failed to list documentation tools${NC}"
    cat /tmp/test-no-auth.txt
fi

# Test 2: List tools with authentication
echo -e "\n2. Testing tool listing with API key..."
if [ -n "$JULEP_API_KEY" ]; then
    JULEP_API_KEY=$JULEP_API_KEY npx tsx src/index.ts --list > /tmp/test-with-auth.txt 2>&1
    if grep -q "SDK Tools" /tmp/test-with-auth.txt; then
        echo -e "${GREEN}✓ SDK tools listed successfully with authentication${NC}"
    else
        echo -e "${RED}✗ Failed to list SDK tools${NC}"
        cat /tmp/test-with-auth.txt
    fi
else
    echo -e "${RED}✗ Skipping authenticated test - JULEP_API_KEY not set${NC}"
fi

# Test 3: Test stdio transport
echo -e "\n3. Testing stdio transport initialization..."
timeout 2s npx tsx src/index.ts 2>&1 | grep -q "MCP Server running on stdio"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Stdio transport initialized successfully${NC}"
else
    echo -e "${RED}✗ Failed to initialize stdio transport${NC}"
fi

echo -e "\n================================="
echo "Test complete!"

# Cleanup
rm -f /tmp/test-no-auth.txt /tmp/test-with-auth.txt