#!/bin/bash

# Setup script for all supported MCP clients

echo "Julep Unified MCP Server - Client Setup Helper"
echo "=============================================="
echo ""

# Check if API key is set
if [ -z "$JULEP_API_KEY" ]; then
    echo "Warning: JULEP_API_KEY environment variable not set"
    echo "SDK tools will not be available without authentication"
    echo ""
fi

# Function to generate config for a client
generate_config() {
    local client=$1
    local output_file=$2
    
    echo "Generating config for $client..."
    
    if [ -n "$JULEP_API_KEY" ]; then
        npx tsx src/index.ts --generate-config "$client" --api-key "$JULEP_API_KEY" > "$output_file"
    else
        npx tsx src/index.ts --generate-config "$client" > "$output_file"
    fi
    
    echo "Config saved to: $output_file"
}

# Claude Desktop
if [[ "$OSTYPE" == "darwin"* ]]; then
    CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    CLAUDE_CONFIG_DIR="$APPDATA/Claude"
else
    CLAUDE_CONFIG_DIR="$HOME/.config/Claude"
fi

echo "1. Claude Desktop"
echo "   Config location: $CLAUDE_CONFIG_DIR/claude_desktop_config.json"
read -p "   Generate config? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    mkdir -p "$CLAUDE_CONFIG_DIR"
    generate_config "claude" "$CLAUDE_CONFIG_DIR/claude_desktop_config.json"
fi
echo ""

# Cursor
echo "2. Cursor"
echo "   Config location: .cursor/mcp.json (in project root)"
read -p "   Generate config? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    mkdir -p .cursor
    generate_config "cursor" ".cursor/mcp.json"
fi
echo ""

# VS Code
echo "3. VS Code (GitHub Copilot)"
echo "   Config location: .vscode/mcp.json (in project root)"
read -p "   Generate config? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    mkdir -p .vscode
    generate_config "vscode" ".vscode/mcp.json"
fi
echo ""

# Windsurf
echo "4. Windsurf"
echo "   Config location: .windsurf/mcp.json (in project root)"
read -p "   Generate config? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    mkdir -p .windsurf
    generate_config "windsurf" ".windsurf/mcp.json"
fi
echo ""

# Cline
echo "5. Cline"
echo "   Config location: ~/Documents/Cline/MCP/julep-mcp.json"
read -p "   Generate config? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    mkdir -p "$HOME/Documents/Cline/MCP"
    generate_config "cline" "$HOME/Documents/Cline/MCP/julep-mcp.json"
fi
echo ""

# Show summary
echo "Setup Complete!"
echo "==============="
echo ""
echo "To use the MCP server:"
echo "1. For stdio clients: Restart the application after config generation"
echo "2. For web clients: Deploy the Cloudflare Worker for OAuth support"
echo "3. Test connection: julep-mcp --list"
echo ""
echo "For client-specific help: julep-mcp --list-clients"