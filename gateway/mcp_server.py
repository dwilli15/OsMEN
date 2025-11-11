#!/usr/bin/env python3
"""
Model Context Protocol (MCP) Server
Provides standardized context protocol for LLM agents
"""

import json
import logging
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from tools.obsidian.obsidian_integration import ObsidianIntegration
from tools.simplewall.simplewall_integration import SimplewallIntegration
from tools.sysinternals.sysinternals_integration import SysinternalsIntegration
from tools.ffmpeg.ffmpeg_integration import FFmpegIntegration
from tools.productivity.productivity_monitor import ProductivityMonitor
from agents.innovation_agent.innovation_agent import InnovationAgent

logger = logging.getLogger(__name__)


class ToolDefinition(BaseModel):
    """MCP Tool Definition"""
    name: str
    description: str
    parameters: Dict[str, Any]


class ToolCallRequest(BaseModel):
    """MCP Tool Call Request"""
    tool: str
    parameters: Dict[str, Any]


class ToolCallResponse(BaseModel):
    """MCP Tool Call Response"""
    tool: str
    result: Any
    success: bool
    error: Optional[str] = None


class MCPServer:
    """Model Context Protocol Server for tool integration"""
    
    def __init__(self):
        self.obsidian = ObsidianIntegration()
        self.simplewall = SimplewallIntegration()
        self.sysinternals = SysinternalsIntegration()
        self.ffmpeg = FFmpegIntegration()
        self.productivity = ProductivityMonitor()
        self.innovation = InnovationAgent()
        
        # Register available tools
        self.tools = self._register_tools()
    
    def _register_tools(self) -> Dict[str, ToolDefinition]:
        """Register all available tools"""
        tools = {}
        
        # Obsidian tools
        tools['obsidian_create_note'] = ToolDefinition(
            name='obsidian_create_note',
            description='Create a new note in Obsidian vault',
            parameters={
                'title': {'type': 'string', 'required': True},
                'content': {'type': 'string', 'required': True},
                'tags': {'type': 'array', 'items': {'type': 'string'}},
                'folder': {'type': 'string'}
            }
        )
        
        tools['obsidian_read_note'] = ToolDefinition(
            name='obsidian_read_note',
            description='Read a note from Obsidian vault',
            parameters={
                'note_path': {'type': 'string', 'required': True}
            }
        )
        
        tools['obsidian_search'] = ToolDefinition(
            name='obsidian_search',
            description='Search notes in Obsidian vault',
            parameters={
                'query': {'type': 'string', 'required': True}
            }
        )
        
        tools['obsidian_list_notes'] = ToolDefinition(
            name='obsidian_list_notes',
            description='List all notes in Obsidian vault',
            parameters={
                'folder': {'type': 'string'}
            }
        )
        
        # Simplewall tools
        tools['simplewall_block_domain'] = ToolDefinition(
            name='simplewall_block_domain',
            description='Block a domain using Simplewall',
            parameters={
                'domain': {'type': 'string', 'required': True}
            }
        )
        
        tools['simplewall_get_rules'] = ToolDefinition(
            name='simplewall_get_rules',
            description='Get current firewall rules',
            parameters={}
        )
        
        # Sysinternals tools
        tools['sysinternals_run_autoruns'] = ToolDefinition(
            name='sysinternals_run_autoruns',
            description='Run Autoruns to analyze startup programs',
            parameters={
                'output_file': {'type': 'string'}
            }
        )
        
        tools['sysinternals_analyze_health'] = ToolDefinition(
            name='sysinternals_analyze_health',
            description='Analyze system health using Sysinternals',
            parameters={}
        )
        
        # FFmpeg tools
        tools['ffmpeg_get_media_info'] = ToolDefinition(
            name='ffmpeg_get_media_info',
            description='Get information about a media file',
            parameters={
                'file_path': {'type': 'string', 'required': True}
            }
        )
        
        tools['ffmpeg_convert_video'] = ToolDefinition(
            name='ffmpeg_convert_video',
            description='Convert video to different format',
            parameters={
                'input_file': {'type': 'string', 'required': True},
                'output_file': {'type': 'string', 'required': True},
                'codec': {'type': 'string'}
            }
        )
        
        # Productivity Monitor tools
        tools['productivity_start_session'] = ToolDefinition(
            name='productivity_start_session',
            description='Start a focus session',
            parameters={
                'session_type': {'type': 'string', 'default': 'pomodoro'},
                'duration': {'type': 'integer', 'default': 25}
            }
        )
        
        tools['productivity_end_session'] = ToolDefinition(
            name='productivity_end_session',
            description='End a focus session',
            parameters={
                'session_id': {'type': 'integer', 'required': True},
                'productivity_score': {'type': 'integer', 'default': 7},
                'distractions': {'type': 'integer', 'default': 0},
                'notes': {'type': 'string', 'default': ''}
            }
        )
        
        tools['productivity_daily_summary'] = ToolDefinition(
            name='productivity_daily_summary',
            description='Get daily productivity summary',
            parameters={
                'date': {'type': 'string'}
            }
        )
        
        tools['productivity_weekly_trends'] = ToolDefinition(
            name='productivity_weekly_trends',
            description='Get weekly productivity trends',
            parameters={}
        )
        
        # Innovation Agent tools
        tools['innovation_weekly_scan'] = ToolDefinition(
            name='innovation_weekly_scan',
            description='Run weekly innovation scan',
            parameters={}
        )
        
        tools['innovation_generate_digest'] = ToolDefinition(
            name='innovation_generate_digest',
            description='Generate innovation digest',
            parameters={
                'innovations': {'type': 'array'}
            }
        )
        
        return tools
    
    def list_tools(self) -> List[ToolDefinition]:
        """List all available tools"""
        return list(self.tools.values())
    
    def call_tool(self, request: ToolCallRequest) -> ToolCallResponse:
        """Execute a tool call"""
        tool_name = request.tool
        params = request.parameters
        
        try:
            # Obsidian tools
            if tool_name == 'obsidian_create_note':
                result = self.obsidian.create_note(**params)
            elif tool_name == 'obsidian_read_note':
                result = self.obsidian.read_note(**params)
            elif tool_name == 'obsidian_search':
                result = self.obsidian.search_notes(**params)
            elif tool_name == 'obsidian_list_notes':
                result = self.obsidian.list_notes(**params)
            
            # Simplewall tools
            elif tool_name == 'simplewall_block_domain':
                result = self.simplewall.block_domain(**params)
            elif tool_name == 'simplewall_get_rules':
                result = self.simplewall.get_rules()
            
            # Sysinternals tools
            elif tool_name == 'sysinternals_run_autoruns':
                result = self.sysinternals.run_autoruns(**params)
            elif tool_name == 'sysinternals_analyze_health':
                result = self.sysinternals.analyze_system_health()
            
            # FFmpeg tools
            elif tool_name == 'ffmpeg_get_media_info':
                result = self.ffmpeg.get_media_info(**params)
            elif tool_name == 'ffmpeg_convert_video':
                result = self.ffmpeg.convert_video(**params)
            
            # Productivity Monitor tools
            elif tool_name == 'productivity_start_session':
                result = self.productivity.start_focus_session(**params)
            elif tool_name == 'productivity_end_session':
                result = self.productivity.end_focus_session(**params)
            elif tool_name == 'productivity_daily_summary':
                result = self.productivity.get_daily_summary(**params)
            elif tool_name == 'productivity_weekly_trends':
                result = self.productivity.get_weekly_trends()
            
            # Innovation Agent tools
            elif tool_name == 'innovation_weekly_scan':
                import asyncio
                result = asyncio.run(self.innovation.weekly_scan())
            elif tool_name == 'innovation_generate_digest':
                import asyncio
                result = asyncio.run(self.innovation.generate_weekly_digest(**params))
            
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            return ToolCallResponse(
                tool=tool_name,
                result=result,
                success=True
            )
        
        except Exception as e:
            logger.error(f"Tool call failed: {tool_name}, error: {str(e)}")
            return ToolCallResponse(
                tool=tool_name,
                result=None,
                success=False,
                error=str(e)
            )
    
    def get_context(self, query: str) -> Dict[str, Any]:
        """Get relevant context for a query (MCP context retrieval)"""
        context = {
            'query': query,
            'tools_available': len(self.tools),
            'integrations': {
                'obsidian': bool(self.obsidian.vault_path),
                'simplewall': True,
                'sysinternals': True,
                'ffmpeg': True
            }
        }
        
        # Search Obsidian for relevant notes if available
        if self.obsidian.vault_path:
            relevant_notes = self.obsidian.search_notes(query)
            context['relevant_knowledge'] = relevant_notes[:5]
        
        return context


# FastAPI app for MCP
app = FastAPI(
    title="OsMEN MCP Server",
    description="Model Context Protocol Server for tool integration",
    version="1.0.0"
)

mcp_server = MCPServer()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "OsMEN MCP Server",
        "version": "1.0.0",
        "protocol": "MCP",
        "tools_available": len(mcp_server.tools)
    }


@app.get("/tools", response_model=List[ToolDefinition])
async def list_tools():
    """List all available tools"""
    return mcp_server.list_tools()


@app.post("/tools/call", response_model=ToolCallResponse)
async def call_tool(request: ToolCallRequest):
    """Execute a tool call"""
    return mcp_server.call_tool(request)


@app.post("/context")
async def get_context(query: str):
    """Get relevant context for a query"""
    return mcp_server.get_context(query)


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
