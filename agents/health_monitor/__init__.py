"""
Health Monitor Agent for OsMEN Workspace Infrastructure

Continuously monitors MCP servers, services, queues, and pipelines.
Performs non-destructive fixes automatically and escalates destructive
fixes with checkpoint prompts.
"""

from .health_monitor_agent import HealthMonitorAgent

__all__ = ["HealthMonitorAgent"]
