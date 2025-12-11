#!/usr/bin/env python3
"""
DEPRECATED: This file is replaced by gateway/mcp/server.py

Use the new unified MCP server:
    python -m gateway.mcp.server

Or import:
    from gateway.mcp import create_app, MCPServer

This file is kept for backward compatibility during migration.
"""

import warnings

warnings.warn(
    "gateway/mcp_server.py is deprecated. Use gateway.mcp.server instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from new location for compatibility
from gateway.mcp.server import MCPServer, app, create_app
from gateway.mcp.tools import ToolDefinition, ToolRegistry

__all__ = ["app", "create_app", "MCPServer", "ToolRegistry", "ToolDefinition"]

if __name__ == "__main__":
    print("⚠️  DEPRECATED: Use 'python -m gateway.mcp.server' instead")
    import uvicorn

    from gateway.mcp.server import app

    uvicorn.run(app, host="0.0.0.0", port=8081)
    uvicorn.run(app, host="0.0.0.0", port=8081)
