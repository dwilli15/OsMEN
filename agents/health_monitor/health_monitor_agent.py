#!/usr/bin/env python3
"""
Health Monitor Agent for OsMEN

Provides continuous health monitoring, auto-repair, and escalation
for all workspace infrastructure components.

Features:
- Heartbeat monitoring for all nodes and MCP servers
- Non-destructive auto-fixes (restart, cache clear, port rebind)
- Destructive fix protocols with checkpoint prompts
- Health status dashboard integration
- Comprehensive logging and reporting
"""

import asyncio
import json
import logging
import os
import shutil
import socket
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import aiohttp

    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    RESTARTING = "restarting"


class FixType(Enum):
    """Types of fixes"""

    NON_DESTRUCTIVE = "non_destructive"
    DESTRUCTIVE = "destructive"


@dataclass
class HealthCheckResult:
    """Result of a health check"""

    node_id: str
    node_name: str
    status: HealthStatus
    latency_ms: Optional[float] = None
    error_message: Optional[str] = None
    last_check: str = field(default_factory=lambda: datetime.now().isoformat())
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FixAction:
    """A proposed or executed fix action"""

    fix_id: str
    node_id: str
    fix_type: FixType
    action: str
    description: str
    requires_approval: bool = False
    checkpoint_path: Optional[str] = None
    executed: bool = False
    success: Optional[bool] = None
    executed_at: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class Checkpoint:
    """A checkpoint for destructive fix rollback"""

    checkpoint_id: str
    created_at: str
    description: str
    affected_nodes: List[str]
    backup_paths: Dict[str, str]
    can_rollback: bool = True


class HealthMonitorAgent:
    """
    Health Monitor Agent for OsMEN Workspace Infrastructure.

    Responsibilities:
    - Continuous heartbeat monitoring of all nodes and MCP servers
    - Latency and error rate tracking
    - Non-destructive auto-fixes (restart, cache clear, port rebind)
    - Destructive fix proposals with checkpoint creation
    - Health reporting and dashboard integration
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the Health Monitor Agent."""
        self.base_path = Path(__file__).parent.parent.parent
        self.infrastructure_path = self.base_path / "infrastructure"
        self.checkpoints_path = self.base_path / "checkpoints"
        self.logs_path = self.base_path / "logs"

        # Ensure directories exist
        self.checkpoints_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)

        # Load configuration
        self.config = self._load_config(config_path)

        # Load node registry
        self.nodes = self._load_node_registry()

        # Health state tracking
        self.health_state: Dict[str, HealthCheckResult] = {}
        self.error_counts: Dict[str, int] = {}
        self.restart_counts: Dict[str, int] = {}

        # Fix tracking
        self.pending_fixes: List[FixAction] = []
        self.fix_history: List[FixAction] = []

        # Monitoring state
        self.is_monitoring = False
        self.monitor_task = None

        logger.info("HealthMonitorAgent initialized")

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load health monitoring configuration from policies."""
        policies_path = self.infrastructure_path / "profiles" / "policies.json"

        if policies_path.exists():
            with open(policies_path, "r") as f:
                policies = json.load(f)
                return policies.get("workspace_policies", {}).get(
                    "health_monitoring", {}
                )

        # Default configuration
        return {
            "heartbeat_interval_seconds": 30,
            "latency_threshold_ms": 5000,
            "error_rate_threshold_percent": 10,
            "auto_restart_enabled": True,
            "max_auto_restart_attempts": 3,
            "checkpoint_before_destructive": True,
        }

    def _load_node_registry(self) -> Dict[str, Any]:
        """Load node registry from infrastructure."""
        registry_path = self.infrastructure_path / "nodes" / "registry.json"

        if registry_path.exists():
            with open(registry_path, "r") as f:
                data = json.load(f)
                return data.get("nodes", {})

        return {}

    def _load_mcp_servers(self) -> Dict[str, Any]:
        """Load MCP server registry."""
        registry_path = self.infrastructure_path / "nodes" / "registry.json"

        if registry_path.exists():
            with open(registry_path, "r") as f:
                data = json.load(f)
                return data.get("mcp_servers", {})

        return {}

    async def check_node_health(
        self, node_id: str, node_config: Dict[str, Any]
    ) -> HealthCheckResult:
        """
        Check health of a specific node.

        Args:
            node_id: Unique identifier for the node
            node_config: Node configuration from registry

        Returns:
            HealthCheckResult with status and details
        """
        node_name = node_config.get("name", node_id)
        endpoint = node_config.get("endpoint", "")
        health_endpoint = node_config.get("health_endpoint")
        node_type = node_config.get("type", "unknown")

        result = HealthCheckResult(
            node_id=node_id, node_name=node_name, status=HealthStatus.UNKNOWN
        )

        # Check based on node type
        if node_type in ["database", "cache"]:
            # Check TCP connectivity for databases
            result = await self._check_tcp_health(node_id, node_config, result)
        elif health_endpoint and AIOHTTP_AVAILABLE:
            # HTTP health check
            result = await self._check_http_health(node_id, node_config, result)
        else:
            # Fallback to port check
            result = await self._check_port_health(node_id, node_config, result)

        # Update health state
        self.health_state[node_id] = result

        # Track errors
        if result.status in [HealthStatus.UNHEALTHY, HealthStatus.UNKNOWN]:
            self.error_counts[node_id] = self.error_counts.get(node_id, 0) + 1
        else:
            self.error_counts[node_id] = 0

        return result

    async def _check_http_health(
        self, node_id: str, node_config: Dict[str, Any], result: HealthCheckResult
    ) -> HealthCheckResult:
        """Check health via HTTP endpoint."""
        if not AIOHTTP_AVAILABLE:
            result.status = HealthStatus.UNKNOWN
            result.error_message = "aiohttp not available"
            return result

        endpoint = node_config.get("endpoint", "")
        health_endpoint = node_config.get("health_endpoint", "/health")

        # Build full URL
        if health_endpoint.startswith("/"):
            url = f"{endpoint.rstrip('/')}{health_endpoint}"
        else:
            url = health_endpoint

        start_time = time.time()

        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    latency = (time.time() - start_time) * 1000
                    result.latency_ms = latency

                    if response.status < 400:
                        result.status = HealthStatus.HEALTHY
                        if latency > self.config.get("latency_threshold_ms", 5000):
                            result.status = HealthStatus.DEGRADED
                            result.details["warning"] = "High latency"
                    else:
                        result.status = HealthStatus.UNHEALTHY
                        result.error_message = f"HTTP {response.status}"

        except asyncio.TimeoutError:
            result.status = HealthStatus.UNHEALTHY
            result.error_message = "Connection timeout"
        except Exception as e:
            result.status = HealthStatus.UNHEALTHY
            result.error_message = str(e)

        return result

    async def _check_tcp_health(
        self, node_id: str, node_config: Dict[str, Any], result: HealthCheckResult
    ) -> HealthCheckResult:
        """Check health via TCP connection."""
        port = node_config.get("port")
        if not port:
            result.status = HealthStatus.UNKNOWN
            result.error_message = "No port configured"
            return result

        start_time = time.time()

        try:
            # Create socket connection
            loop = asyncio.get_event_loop()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)

            await loop.run_in_executor(None, lambda: sock.connect(("localhost", port)))

            latency = (time.time() - start_time) * 1000
            result.latency_ms = latency
            result.status = HealthStatus.HEALTHY

            sock.close()

        except socket.timeout:
            result.status = HealthStatus.UNHEALTHY
            result.error_message = "Connection timeout"
        except ConnectionRefusedError:
            result.status = HealthStatus.UNHEALTHY
            result.error_message = "Connection refused"
        except Exception as e:
            result.status = HealthStatus.UNHEALTHY
            result.error_message = str(e)

        return result

    async def _check_port_health(
        self, node_id: str, node_config: Dict[str, Any], result: HealthCheckResult
    ) -> HealthCheckResult:
        """Check if port is open (fallback check)."""
        port = node_config.get("port")
        if not port:
            result.status = HealthStatus.UNKNOWN
            result.error_message = "No port configured"
            return result

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            connection = sock.connect_ex(("localhost", port))
            sock.close()

            if connection == 0:
                result.status = HealthStatus.HEALTHY
            else:
                result.status = HealthStatus.UNHEALTHY
                result.error_message = f"Port {port} not responding"

        except Exception as e:
            result.status = HealthStatus.UNHEALTHY
            result.error_message = str(e)

        return result

    async def check_all_nodes(self) -> Dict[str, HealthCheckResult]:
        """Check health of all registered nodes."""
        results = {}

        for node_id, node_config in self.nodes.items():
            result = await self.check_node_health(node_id, node_config)
            results[node_id] = result
            logger.info(f"Health check {node_id}: {result.status.value}")

        # Update registry with results
        await self._update_registry(results)

        return results

    async def check_mcp_servers(self) -> Dict[str, HealthCheckResult]:
        """Check health of all MCP servers."""
        mcp_servers = self._load_mcp_servers()
        results = {}

        for server_id, server_config in mcp_servers.items():
            result = HealthCheckResult(
                node_id=server_id,
                node_name=server_config.get("name", server_id),
                status=HealthStatus.UNKNOWN,
            )

            # MCP servers are tracked differently - check via VS Code
            # For now, mark as unknown since they're managed by VS Code
            result.details["managed_by"] = "vscode"
            result.details["tools"] = server_config.get("tools", [])

            results[server_id] = result
            self.health_state[f"mcp_{server_id}"] = result

        return results

    async def _update_registry(self, results: Dict[str, HealthCheckResult]):
        """Update node registry with health check results."""
        registry_path = self.infrastructure_path / "nodes" / "registry.json"

        if not registry_path.exists():
            return

        try:
            with open(registry_path, "r") as f:
                registry = json.load(f)

            for node_id, result in results.items():
                if node_id in registry.get("nodes", {}):
                    registry["nodes"][node_id]["status"] = result.status.value
                    registry["nodes"][node_id]["last_health_check"] = result.last_check

            registry["updated_at"] = datetime.now().isoformat()

            with open(registry_path, "w") as f:
                json.dump(registry, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to update registry: {e}")

    # =========================================================================
    # Non-Destructive Fixes
    # =========================================================================

    async def restart_service(self, node_id: str) -> FixAction:
        """
        Restart a Docker service (non-destructive).

        Args:
            node_id: The node to restart

        Returns:
            FixAction with result
        """
        node_config = self.nodes.get(node_id, {})
        docker_service = node_config.get("docker_service", node_id)

        fix = FixAction(
            fix_id=f"restart_{node_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            node_id=node_id,
            fix_type=FixType.NON_DESTRUCTIVE,
            action="restart",
            description=f"Restart Docker service: {docker_service}",
            requires_approval=False,
        )

        # Check restart count
        restart_count = self.restart_counts.get(node_id, 0)
        max_restarts = self.config.get("max_auto_restart_attempts", 3)

        if restart_count >= max_restarts:
            fix.success = False
            fix.error_message = f"Max restart attempts ({max_restarts}) exceeded"
            self.fix_history.append(fix)
            return fix

        try:
            # Update status
            if node_id in self.health_state:
                self.health_state[node_id].status = HealthStatus.RESTARTING

            # Execute restart
            result = subprocess.run(
                ["docker", "restart", docker_service],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                fix.success = True
                fix.executed = True
                fix.executed_at = datetime.now().isoformat()
                self.restart_counts[node_id] = restart_count + 1
                logger.info(f"Successfully restarted {docker_service}")
            else:
                fix.success = False
                fix.error_message = result.stderr

        except subprocess.TimeoutExpired:
            fix.success = False
            fix.error_message = "Restart timed out"
        except Exception as e:
            fix.success = False
            fix.error_message = str(e)

        self.fix_history.append(fix)
        return fix

    async def clear_cache(self, node_id: str) -> FixAction:
        """Clear cache for a service (non-destructive)."""
        fix = FixAction(
            fix_id=f"cache_clear_{node_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            node_id=node_id,
            fix_type=FixType.NON_DESTRUCTIVE,
            action="clear_cache",
            description=f"Clear cache for: {node_id}",
            requires_approval=False,
        )

        node_config = self.nodes.get(node_id, {})
        node_type = node_config.get("type", "")

        try:
            if node_type == "cache" and node_id == "redis":
                # Redis FLUSHDB
                result = subprocess.run(
                    ["docker", "exec", "osmen-redis", "redis-cli", "FLUSHDB"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                fix.success = result.returncode == 0
                if not fix.success:
                    fix.error_message = result.stderr
            else:
                fix.success = False
                fix.error_message = f"Cache clear not supported for {node_type}"

        except Exception as e:
            fix.success = False
            fix.error_message = str(e)

        fix.executed = True
        fix.executed_at = datetime.now().isoformat()
        self.fix_history.append(fix)
        return fix

    async def rebind_port(
        self, node_id: str, new_port: Optional[int] = None
    ) -> FixAction:
        """Attempt to rebind a service to a different port (non-destructive)."""
        fix = FixAction(
            fix_id=f"rebind_{node_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            node_id=node_id,
            fix_type=FixType.NON_DESTRUCTIVE,
            action="rebind_port",
            description=f"Rebind port for: {node_id}",
            requires_approval=True,  # Port changes should be reviewed
        )

        # This requires docker-compose modification, queue for approval
        self.pending_fixes.append(fix)
        logger.info(f"Port rebind queued for approval: {node_id}")

        return fix

    # =========================================================================
    # Destructive Fixes
    # =========================================================================

    def create_checkpoint(
        self, description: str, affected_nodes: List[str]
    ) -> Checkpoint:
        """
        Create a checkpoint before destructive operations.

        Args:
            description: Description of what this checkpoint is for
            affected_nodes: List of nodes that will be affected

        Returns:
            Checkpoint object with backup information
        """
        checkpoint_id = f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        checkpoint_dir = self.checkpoints_path / checkpoint_id
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        backup_paths = {}

        # Backup relevant configuration files
        config_files = [
            self.infrastructure_path / "nodes" / "registry.json",
            self.infrastructure_path / "tools" / "inventory.json",
            self.infrastructure_path / "graph" / "connections.json",
            self.infrastructure_path / "profiles" / "policies.json",
        ]

        for config_file in config_files:
            if config_file.exists():
                backup_file = checkpoint_dir / config_file.name
                shutil.copy2(config_file, backup_file)
                backup_paths[str(config_file)] = str(backup_file)

        # Save checkpoint metadata
        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            created_at=datetime.now().isoformat(),
            description=description,
            affected_nodes=affected_nodes,
            backup_paths=backup_paths,
        )

        metadata_path = checkpoint_dir / "checkpoint.json"
        with open(metadata_path, "w") as f:
            json.dump(asdict(checkpoint), f, indent=2)

        logger.info(f"Created checkpoint: {checkpoint_id}")
        return checkpoint

    def rollback_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Rollback to a previous checkpoint.

        Args:
            checkpoint_id: ID of checkpoint to restore

        Returns:
            True if successful
        """
        checkpoint_dir = self.checkpoints_path / checkpoint_id
        metadata_path = checkpoint_dir / "checkpoint.json"

        if not metadata_path.exists():
            logger.error(f"Checkpoint not found: {checkpoint_id}")
            return False

        try:
            with open(metadata_path, "r") as f:
                checkpoint_data = json.load(f)

            for original_path, backup_path in checkpoint_data.get(
                "backup_paths", {}
            ).items():
                if Path(backup_path).exists():
                    shutil.copy2(backup_path, original_path)
                    logger.info(f"Restored: {original_path}")

            logger.info(f"Rollback complete: {checkpoint_id}")
            return True

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

    async def propose_destructive_fix(
        self, node_id: str, action: str, description: str
    ) -> FixAction:
        """
        Propose a destructive fix that requires user approval.

        Args:
            node_id: Node to fix
            action: Type of fix (e.g., 'reset', 'rebuild', 'restore')
            description: Human-readable description

        Returns:
            FixAction queued for approval
        """
        # Create checkpoint first
        checkpoint = self.create_checkpoint(
            description=f"Pre-fix checkpoint for {action} on {node_id}",
            affected_nodes=[node_id],
        )

        fix = FixAction(
            fix_id=f"{action}_{node_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            node_id=node_id,
            fix_type=FixType.DESTRUCTIVE,
            action=action,
            description=description,
            requires_approval=True,
            checkpoint_path=str(self.checkpoints_path / checkpoint.checkpoint_id),
        )

        self.pending_fixes.append(fix)

        # Save to queue file for dashboard
        await self._save_pending_fixes()

        logger.warning(f"Destructive fix queued for approval: {fix.fix_id}")
        return fix

    async def execute_approved_fix(self, fix_id: str) -> FixAction:
        """Execute a fix that has been approved by the user."""
        fix = next((f for f in self.pending_fixes if f.fix_id == fix_id), None)

        if not fix:
            raise ValueError(f"Fix not found: {fix_id}")

        if fix.action == "reset":
            # Reset service (stop, remove container, recreate)
            docker_service = self.nodes.get(fix.node_id, {}).get(
                "docker_service", fix.node_id
            )

            try:
                # Stop and remove
                subprocess.run(["docker", "stop", docker_service], timeout=30)
                subprocess.run(["docker", "rm", docker_service], timeout=30)

                # Recreate via docker-compose
                subprocess.run(
                    ["docker-compose", "up", "-d", docker_service],
                    cwd=str(self.base_path),
                    timeout=120,
                )

                fix.success = True

            except Exception as e:
                fix.success = False
                fix.error_message = str(e)

        fix.executed = True
        fix.executed_at = datetime.now().isoformat()

        # Move from pending to history
        self.pending_fixes.remove(fix)
        self.fix_history.append(fix)

        await self._save_pending_fixes()

        return fix

    async def _save_pending_fixes(self):
        """Save pending fixes to queue file for dashboard."""
        queue_dir = self.infrastructure_path / "queues"
        queue_dir.mkdir(parents=True, exist_ok=True)

        queue_path = queue_dir / "destructive_fixes.json"

        fixes_data = [asdict(fix) for fix in self.pending_fixes]
        for fix_data in fixes_data:
            fix_data["fix_type"] = fix_data["fix_type"].value

        with open(queue_path, "w") as f:
            json.dump(
                {"updated_at": datetime.now().isoformat(), "pending_fixes": fixes_data},
                f,
                indent=2,
            )

    # =========================================================================
    # Auto-Healing Logic
    # =========================================================================

    async def auto_heal(self, result: HealthCheckResult) -> Optional[FixAction]:
        """
        Attempt to automatically heal an unhealthy node.

        Args:
            result: The health check result

        Returns:
            FixAction if healing was attempted
        """
        if result.status == HealthStatus.HEALTHY:
            return None

        if not self.config.get("auto_restart_enabled", True):
            return None

        node_id = result.node_id
        error_count = self.error_counts.get(node_id, 0)

        # Escalation logic
        if error_count <= 2:
            # First attempts: try restart
            logger.info(
                f"Auto-healing {node_id}: attempting restart (attempt {error_count})"
            )
            return await self.restart_service(node_id)

        elif error_count <= 4:
            # More errors: try cache clear if applicable
            node_type = self.nodes.get(node_id, {}).get("type", "")
            if node_type == "cache":
                logger.info(f"Auto-healing {node_id}: clearing cache")
                return await self.clear_cache(node_id)
            else:
                return await self.restart_service(node_id)

        else:
            # Many errors: propose destructive fix
            logger.warning(f"Auto-healing {node_id}: proposing destructive fix")
            return await self.propose_destructive_fix(
                node_id=node_id,
                action="reset",
                description=f"Service {node_id} has failed {error_count} health checks. "
                f"Recommending container reset. Please save any work and approve.",
            )

    # =========================================================================
    # Monitoring Loop
    # =========================================================================

    async def start_monitoring(self):
        """Start continuous health monitoring."""
        if self.is_monitoring:
            logger.warning("Monitoring already running")
            return

        self.is_monitoring = True
        logger.info("Starting health monitoring")

        interval = self.config.get("heartbeat_interval_seconds", 30)

        while self.is_monitoring:
            try:
                # Check all nodes
                results = await self.check_all_nodes()

                # Check MCP servers
                mcp_results = await self.check_mcp_servers()

                # Attempt auto-healing for unhealthy nodes
                for node_id, result in results.items():
                    if result.status in [HealthStatus.UNHEALTHY, HealthStatus.DEGRADED]:
                        await self.auto_heal(result)

                # Log summary
                healthy = sum(
                    1 for r in results.values() if r.status == HealthStatus.HEALTHY
                )
                total = len(results)
                logger.info(f"Health check complete: {healthy}/{total} nodes healthy")

                # Write health report
                await self._write_health_report(results, mcp_results)

            except Exception as e:
                logger.error(f"Health monitoring error: {e}")

            await asyncio.sleep(interval)

    def stop_monitoring(self):
        """Stop health monitoring."""
        self.is_monitoring = False
        logger.info("Stopping health monitoring")

    async def _write_health_report(
        self,
        node_results: Dict[str, HealthCheckResult],
        mcp_results: Dict[str, HealthCheckResult],
    ):
        """Write health report to logs."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "nodes": {
                node_id: {
                    "status": result.status.value,
                    "latency_ms": result.latency_ms,
                    "error": result.error_message,
                }
                for node_id, result in node_results.items()
            },
            "mcp_servers": {
                server_id: {"status": result.status.value, "details": result.details}
                for server_id, result in mcp_results.items()
            },
            "pending_fixes": len(self.pending_fixes),
            "summary": {
                "healthy": sum(
                    1 for r in node_results.values() if r.status == HealthStatus.HEALTHY
                ),
                "degraded": sum(
                    1
                    for r in node_results.values()
                    if r.status == HealthStatus.DEGRADED
                ),
                "unhealthy": sum(
                    1
                    for r in node_results.values()
                    if r.status == HealthStatus.UNHEALTHY
                ),
                "unknown": sum(
                    1 for r in node_results.values() if r.status == HealthStatus.UNKNOWN
                ),
            },
        }

        # Write latest report
        report_path = self.logs_path / "health_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        # Append to history
        history_path = (
            self.logs_path / f"health_history_{datetime.now().strftime('%Y%m%d')}.jsonl"
        )
        with open(history_path, "a") as f:
            f.write(json.dumps(report) + "\n")

    # =========================================================================
    # Status and Reporting
    # =========================================================================

    def get_status(self) -> Dict[str, Any]:
        """Get current health monitor status."""
        return {
            "is_monitoring": self.is_monitoring,
            "config": self.config,
            "node_count": len(self.nodes),
            "health_state": {
                node_id: {
                    "status": result.status.value,
                    "last_check": result.last_check,
                    "latency_ms": result.latency_ms,
                    "error": result.error_message,
                }
                for node_id, result in self.health_state.items()
            },
            "pending_fixes": len(self.pending_fixes),
            "fix_history_count": len(self.fix_history),
            "error_counts": self.error_counts,
            "restart_counts": self.restart_counts,
        }

    def get_pending_fixes(self) -> List[Dict[str, Any]]:
        """Get list of pending fixes requiring approval."""
        return [
            {
                "fix_id": fix.fix_id,
                "node_id": fix.node_id,
                "fix_type": fix.fix_type.value,
                "action": fix.action,
                "description": fix.description,
                "checkpoint_path": fix.checkpoint_path,
            }
            for fix in self.pending_fixes
        ]

    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """List available checkpoints for rollback."""
        checkpoints = []

        for checkpoint_dir in self.checkpoints_path.iterdir():
            if checkpoint_dir.is_dir():
                metadata_path = checkpoint_dir / "checkpoint.json"
                if metadata_path.exists():
                    with open(metadata_path, "r") as f:
                        checkpoints.append(json.load(f))

        return sorted(checkpoints, key=lambda x: x["created_at"], reverse=True)


# =============================================================================
# CLI Entry Point
# =============================================================================


async def main():
    """Main entry point for health monitor."""
    agent = HealthMonitorAgent()

    # Run initial health check
    print("Running initial health check...")
    results = await agent.check_all_nodes()

    for node_id, result in results.items():
        status_emoji = {
            HealthStatus.HEALTHY: "✅",
            HealthStatus.DEGRADED: "⚠️",
            HealthStatus.UNHEALTHY: "❌",
            HealthStatus.UNKNOWN: "❓",
            HealthStatus.RESTARTING: "🔄",
        }.get(result.status, "❓")

        latency = f"{result.latency_ms:.0f}ms" if result.latency_ms else "N/A"
        print(f"  {status_emoji} {result.node_name}: {result.status.value} ({latency})")

    print(f"\nStatus: {agent.get_status()['health_state']}")


if __name__ == "__main__":
    asyncio.run(main())
