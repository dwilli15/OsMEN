"""
DEPRECATED: MCP Server for YOLO-OPS

This file is replaced by the unified MCP server at gateway/mcp/server.py

Use the new unified MCP server:
    python -m gateway.mcp.server

All YOLO-OPS tools are now available in the unified tool registry.

This file is kept for backward compatibility during migration.
"""

import warnings

warnings.warn(
    "integrations/yolo/mcp_yolo_server.py is deprecated. Use gateway.mcp.server instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from new location for compatibility
from gateway.mcp.server import MCPServer, app, create_app
from gateway.mcp.tools import ToolRegistry, get_tool_registry

__all__ = ["MCPServer", "app", "create_app", "ToolRegistry", "get_tool_registry"]


def run_server(port: int = 8082):
    """Run the MCP server (deprecated - use gateway.mcp.server)"""
    print("⚠️  DEPRECATED: Use 'python -m gateway.mcp.server' instead")
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    import os

    run_server(int(os.getenv("MCP_PORT", "8082")))
