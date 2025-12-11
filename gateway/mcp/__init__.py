"""
OsMEN Unified MCP Server
Model Context Protocol implementation with OpenTelemetry tracing

This package provides:
- stdio_server: Synchronous stdio-based MCP server for VS Code (lightweight, no dependencies)
- server: FastAPI-based HTTP MCP server (full features, requires FastAPI/uvicorn)
- tools: Tool registry with 40+ tools
- tracing: OpenTelemetry tracing support
"""

__version__ = "2.0.0"

# Lazy imports to avoid loading heavy dependencies unnecessarily
def __getattr__(name):
    """Lazy import of heavy modules"""
    if name == "MCPStdioServer":
        from .stdio_server import MCPStdioServer
        return MCPStdioServer
    elif name in ("MCPServer", "create_app"):
        from .server import MCPServer, create_app
        if name == "MCPServer":
            return MCPServer
        return create_app
    elif name in ("ToolCategory", "ToolDefinition", "ToolRegistry", "get_tool_registry"):
        from .tools import ToolCategory, ToolDefinition, ToolRegistry, get_tool_registry
        return {"ToolCategory": ToolCategory, "ToolDefinition": ToolDefinition, 
                "ToolRegistry": ToolRegistry, "get_tool_registry": get_tool_registry}[name]
    elif name in ("TracingManager", "TracingMiddleware", "get_tracer", "traced"):
        from .tracing import TracingManager, TracingMiddleware, get_tracer, traced
        return {"TracingManager": TracingManager, "TracingMiddleware": TracingMiddleware,
                "get_tracer": get_tracer, "traced": traced}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "MCPStdioServer",
    "MCPServer",
    "create_app",
    "ToolRegistry",
    "ToolDefinition",
    "ToolCategory",
    "get_tool_registry",
    "TracingMiddleware",
    "TracingManager",
    "get_tracer",
    "traced",
]
