#!/usr/bin/env python3
"""
OsMEN System Monitoring Integration

Monitors:
- Task Scheduler (scheduled tasks, failures)
- Startup Applications (registry, startup folder)
- Resource Allocation (RAM, CPU, GPU/CUDA)
- GPU/VRAM utilization

Usage:
    from integrations.system_monitor import SystemMonitor

    monitor = SystemMonitor()
    status = await monitor.get_full_status()
"""

import asyncio
import json
import logging
import os
import platform
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# GPU Monitoring
# ============================================================================


@dataclass
class GPUInfo:
    """GPU information"""

    id: int
    name: str
    memory_total_mb: int
    memory_used_mb: int
    memory_free_mb: int
    utilization_percent: float
    temperature_c: Optional[float] = None
    power_draw_w: Optional[float] = None


class GPUMonitor:
    """Monitor NVIDIA GPU via pynvml"""

    def __init__(self):
        self.available = False
        self._nvml = None
        self._initialize()

    def _initialize(self):
        """Initialize NVML"""
        try:
            import pynvml

            pynvml.nvmlInit()
            self._nvml = pynvml
            self.available = True
            logger.info("NVML initialized - GPU monitoring available")
        except ImportError:
            logger.warning("pynvml not installed - GPU monitoring disabled")
        except Exception as e:
            logger.warning(f"NVML init failed: {e}")

    def get_gpu_count(self) -> int:
        """Get number of NVIDIA GPUs"""
        if not self.available:
            return 0
        try:
            return self._nvml.nvmlDeviceGetCount()
        except:
            return 0

    def get_gpu_info(self, gpu_id: int = 0) -> Optional[GPUInfo]:
        """Get info for specific GPU"""
        if not self.available:
            return None

        try:
            handle = self._nvml.nvmlDeviceGetHandleByIndex(gpu_id)
            name = self._nvml.nvmlDeviceGetName(handle)
            if isinstance(name, bytes):
                name = name.decode("utf-8")

            memory = self._nvml.nvmlDeviceGetMemoryInfo(handle)
            utilization = self._nvml.nvmlDeviceGetUtilizationRates(handle)

            try:
                temperature = self._nvml.nvmlDeviceGetTemperature(
                    handle, self._nvml.NVML_TEMPERATURE_GPU
                )
            except:
                temperature = None

            try:
                power = self._nvml.nvmlDeviceGetPowerUsage(handle) / 1000.0
            except:
                power = None

            return GPUInfo(
                id=gpu_id,
                name=name,
                memory_total_mb=memory.total // (1024 * 1024),
                memory_used_mb=memory.used // (1024 * 1024),
                memory_free_mb=memory.free // (1024 * 1024),
                utilization_percent=utilization.gpu,
                temperature_c=temperature,
                power_draw_w=power,
            )
        except Exception as e:
            logger.error(f"Failed to get GPU info: {e}")
            return None

    def get_all_gpus(self) -> List[GPUInfo]:
        """Get info for all GPUs"""
        gpus = []
        for i in range(self.get_gpu_count()):
            info = self.get_gpu_info(i)
            if info:
                gpus.append(info)
        return gpus

    def to_dict(self) -> Dict[str, Any]:
        """Get all GPU info as dict"""
        gpus = self.get_all_gpus()
        return {
            "available": self.available,
            "gpu_count": len(gpus),
            "gpus": [
                {
                    "id": g.id,
                    "name": g.name,
                    "memory_total_mb": g.memory_total_mb,
                    "memory_used_mb": g.memory_used_mb,
                    "memory_free_mb": g.memory_free_mb,
                    "memory_percent": (
                        round(g.memory_used_mb / g.memory_total_mb * 100, 1)
                        if g.memory_total_mb > 0
                        else 0
                    ),
                    "utilization_percent": g.utilization_percent,
                    "temperature_c": g.temperature_c,
                    "power_draw_w": g.power_draw_w,
                }
                for g in gpus
            ],
        }


# ============================================================================
# Resource Monitoring
# ============================================================================


class ResourceMonitor:
    """Monitor system resources (CPU, RAM, Disk)"""

    def __init__(self):
        try:
            import psutil

            self.psutil = psutil
            self.available = True
        except ImportError:
            self.psutil = None
            self.available = False
            logger.warning("psutil not installed - resource monitoring limited")

    def get_cpu_info(self) -> Dict[str, Any]:
        """Get CPU information"""
        if not self.available:
            return {"available": False}

        return {
            "available": True,
            "cores_physical": self.psutil.cpu_count(logical=False),
            "cores_logical": self.psutil.cpu_count(logical=True),
            "usage_percent": self.psutil.cpu_percent(interval=1),
            "per_core_percent": self.psutil.cpu_percent(interval=0.1, percpu=True),
            "frequency_mhz": (
                self.psutil.cpu_freq().current if self.psutil.cpu_freq() else None
            ),
        }

    def get_memory_info(self) -> Dict[str, Any]:
        """Get RAM information"""
        if not self.available:
            return {"available": False}

        mem = self.psutil.virtual_memory()
        return {
            "available": True,
            "total_gb": round(mem.total / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "free_gb": round(mem.available / (1024**3), 2),
            "percent_used": mem.percent,
        }

    def get_disk_info(self) -> List[Dict[str, Any]]:
        """Get disk information"""
        if not self.available:
            return []

        disks = []
        for partition in self.psutil.disk_partitions():
            try:
                usage = self.psutil.disk_usage(partition.mountpoint)
                disks.append(
                    {
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_gb": round(usage.free / (1024**3), 2),
                        "percent_used": usage.percent,
                    }
                )
            except:
                pass
        return disks

    def get_top_processes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top processes by resource usage"""
        if not self.available:
            return []

        processes = []
        for proc in self.psutil.process_iter(
            ["pid", "name", "cpu_percent", "memory_percent"]
        ):
            try:
                info = proc.info
                processes.append(
                    {
                        "pid": info["pid"],
                        "name": info["name"],
                        "cpu_percent": info["cpu_percent"],
                        "memory_percent": round(info["memory_percent"], 2),
                    }
                )
            except:
                pass

        # Sort by CPU usage
        processes.sort(key=lambda x: x["cpu_percent"], reverse=True)
        return processes[:limit]

    def to_dict(self) -> Dict[str, Any]:
        """Get full resource report"""
        return {
            "cpu": self.get_cpu_info(),
            "memory": self.get_memory_info(),
            "disks": self.get_disk_info(),
            "top_processes": self.get_top_processes(5),
        }


# ============================================================================
# Task Scheduler Monitoring (Windows)
# ============================================================================


class TaskSchedulerMonitor:
    """Monitor Windows Task Scheduler"""

    def __init__(self):
        self.available = platform.system() == "Windows"
        self._scheduler = None
        if self.available:
            self._initialize()

    def _initialize(self):
        """Initialize Task Scheduler COM interface"""
        try:
            import win32com.client

            self._scheduler = win32com.client.Dispatch("Schedule.Service")
            self._scheduler.Connect()
            logger.info("Task Scheduler connected")
        except ImportError:
            logger.warning("pywin32 not installed - Task Scheduler monitoring disabled")
            self.available = False
        except Exception as e:
            logger.warning(f"Task Scheduler init failed: {e}")
            self.available = False

    def get_tasks(self, folder_path: str = "\\") -> List[Dict[str, Any]]:
        """Get all tasks from a folder"""
        if not self.available or not self._scheduler:
            return []

        tasks = []
        try:
            folder = self._scheduler.GetFolder(folder_path)
            for task in folder.GetTasks(0):
                try:
                    last_run = task.LastRunTime
                    next_run = task.NextRunTime

                    tasks.append(
                        {
                            "name": task.Name,
                            "path": task.Path,
                            "enabled": task.Enabled,
                            "state": self._get_state_name(task.State),
                            "last_run": str(last_run) if last_run else None,
                            "next_run": str(next_run) if next_run else None,
                            "last_result": task.LastTaskResult,
                        }
                    )
                except:
                    pass

            # Recursively get tasks from subfolders
            for subfolder in folder.GetFolders(0):
                tasks.extend(self.get_tasks(subfolder.Path))

        except Exception as e:
            logger.error(f"Failed to get tasks: {e}")

        return tasks

    def _get_state_name(self, state: int) -> str:
        """Convert task state to name"""
        states = {0: "Unknown", 1: "Disabled", 2: "Queued", 3: "Ready", 4: "Running"}
        return states.get(state, f"Unknown({state})")

    def get_failed_tasks(self) -> List[Dict[str, Any]]:
        """Get tasks that failed on last run"""
        all_tasks = self.get_tasks()
        return [t for t in all_tasks if t.get("last_result", 0) != 0]

    def to_dict(self) -> Dict[str, Any]:
        """Get task scheduler status"""
        tasks = self.get_tasks()
        failed = [t for t in tasks if t.get("last_result", 0) != 0]

        return {
            "available": self.available,
            "total_tasks": len(tasks),
            "enabled_tasks": len([t for t in tasks if t.get("enabled")]),
            "running_tasks": len([t for t in tasks if t.get("state") == "Running"]),
            "failed_tasks": len(failed),
            "failed_task_names": [t["name"] for t in failed[:5]],
        }


# ============================================================================
# Startup Apps Monitoring (Windows)
# ============================================================================


class StartupAppsMonitor:
    """Monitor Windows startup applications"""

    REGISTRY_PATHS = [
        (r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", "HKCU", "User Run"),
        (r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce", "HKCU", "User RunOnce"),
        (r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", "HKLM", "System Run"),
        (
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
            "HKLM",
            "System RunOnce",
        ),
    ]

    def __init__(self):
        self.available = platform.system() == "Windows"
        self._winreg = None
        if self.available:
            try:
                import winreg

                self._winreg = winreg
            except ImportError:
                self.available = False

    def get_registry_startups(self) -> List[Dict[str, Any]]:
        """Get startup entries from registry"""
        if not self.available or not self._winreg:
            return []

        entries = []

        for path, hive_name, description in self.REGISTRY_PATHS:
            hive = (
                self._winreg.HKEY_CURRENT_USER
                if hive_name == "HKCU"
                else self._winreg.HKEY_LOCAL_MACHINE
            )

            try:
                key = self._winreg.OpenKey(hive, path, 0, self._winreg.KEY_READ)
                i = 0
                while True:
                    try:
                        name, value, _ = self._winreg.EnumValue(key, i)
                        entries.append(
                            {
                                "name": name,
                                "command": value,
                                "location": f"{hive_name}\\{path}",
                                "type": description,
                            }
                        )
                        i += 1
                    except OSError:
                        break
                self._winreg.CloseKey(key)
            except:
                pass

        return entries

    def get_startup_folder_items(self) -> List[Dict[str, Any]]:
        """Get items from startup folders"""
        items = []

        # User startup folder
        user_startup = (
            Path(os.environ.get("APPDATA", ""))
            / "Microsoft/Windows/Start Menu/Programs/Startup"
        )
        if user_startup.exists():
            for item in user_startup.iterdir():
                items.append(
                    {
                        "name": item.stem,
                        "path": str(item),
                        "location": "User Startup Folder",
                        "type": "Shortcut" if item.suffix == ".lnk" else item.suffix,
                    }
                )

        # All users startup folder
        all_users_startup = (
            Path(os.environ.get("PROGRAMDATA", ""))
            / "Microsoft/Windows/Start Menu/Programs/Startup"
        )
        if all_users_startup.exists():
            for item in all_users_startup.iterdir():
                items.append(
                    {
                        "name": item.stem,
                        "path": str(item),
                        "location": "All Users Startup Folder",
                        "type": "Shortcut" if item.suffix == ".lnk" else item.suffix,
                    }
                )

        return items

    def get_all_startups(self) -> List[Dict[str, Any]]:
        """Get all startup entries"""
        entries = self.get_registry_startups()
        entries.extend(self.get_startup_folder_items())
        return entries

    def to_dict(self) -> Dict[str, Any]:
        """Get startup apps status"""
        entries = self.get_all_startups()
        return {
            "available": self.available,
            "total_entries": len(entries),
            "registry_entries": len(
                [
                    e
                    for e in entries
                    if "Registry" in e.get("type", "") or "Run" in e.get("type", "")
                ]
            ),
            "folder_entries": len(
                [e for e in entries if "Folder" in e.get("location", "")]
            ),
            "entries": entries,
        }


# ============================================================================
# Unified System Monitor
# ============================================================================


class SystemMonitor:
    """Unified system monitoring"""

    def __init__(self):
        self.gpu = GPUMonitor()
        self.resources = ResourceMonitor()
        self.task_scheduler = TaskSchedulerMonitor()
        self.startup_apps = StartupAppsMonitor()

        # Alert thresholds
        self.thresholds = {
            "cpu_percent": 90,
            "memory_percent": 90,
            "gpu_memory_percent": 90,
            "gpu_temp_c": 85,
            "disk_percent": 95,
        }

    def get_full_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            "timestamp": datetime.now().isoformat(),
            "platform": platform.system(),
            "gpu": self.gpu.to_dict(),
            "resources": self.resources.to_dict(),
            "task_scheduler": self.task_scheduler.to_dict(),
            "startup_apps": self.startup_apps.to_dict(),
            "alerts": self._check_alerts(),
        }

    def _check_alerts(self) -> List[Dict[str, Any]]:
        """Check for threshold breaches"""
        alerts = []

        # CPU alert
        cpu_info = self.resources.get_cpu_info()
        if cpu_info.get("usage_percent", 0) > self.thresholds["cpu_percent"]:
            alerts.append(
                {
                    "type": "cpu",
                    "severity": "warning",
                    "message": f"CPU usage at {cpu_info['usage_percent']}%",
                }
            )

        # Memory alert
        mem_info = self.resources.get_memory_info()
        if mem_info.get("percent_used", 0) > self.thresholds["memory_percent"]:
            alerts.append(
                {
                    "type": "memory",
                    "severity": "warning",
                    "message": f"Memory usage at {mem_info['percent_used']}%",
                }
            )

        # GPU alerts
        for gpu in self.gpu.get_all_gpus():
            mem_percent = (
                (gpu.memory_used_mb / gpu.memory_total_mb * 100)
                if gpu.memory_total_mb > 0
                else 0
            )
            if mem_percent > self.thresholds["gpu_memory_percent"]:
                alerts.append(
                    {
                        "type": "gpu_memory",
                        "severity": "warning",
                        "message": f"GPU {gpu.id} VRAM at {mem_percent:.1f}%",
                    }
                )

            if gpu.temperature_c and gpu.temperature_c > self.thresholds["gpu_temp_c"]:
                alerts.append(
                    {
                        "type": "gpu_temp",
                        "severity": "critical",
                        "message": f"GPU {gpu.id} temperature at {gpu.temperature_c}°C",
                    }
                )

        # Task Scheduler alerts
        failed_tasks = self.task_scheduler.get_failed_tasks()
        if failed_tasks:
            alerts.append(
                {
                    "type": "task_scheduler",
                    "severity": "info",
                    "message": f"{len(failed_tasks)} scheduled tasks failed",
                    "tasks": [t["name"] for t in failed_tasks[:3]],
                }
            )

        return alerts

    def get_gpu_status(self) -> Dict[str, Any]:
        """Get just GPU status"""
        return self.gpu.to_dict()

    def get_resource_status(self) -> Dict[str, Any]:
        """Get just resource status"""
        return self.resources.to_dict()


# ============================================================================
# MCP Tool Handlers
# ============================================================================

_monitor: Optional[SystemMonitor] = None


def get_monitor() -> SystemMonitor:
    """Get or create monitor instance"""
    global _monitor
    if _monitor is None:
        _monitor = SystemMonitor()
    return _monitor


async def handle_system_status(params: Dict[str, Any]) -> Dict[str, Any]:
    """MCP handler for system status"""
    monitor = get_monitor()
    include = params.get("include", ["all"])

    if "all" in include:
        return monitor.get_full_status()

    result = {"timestamp": datetime.now().isoformat()}

    if "gpu" in include:
        result["gpu"] = monitor.gpu.to_dict()
    if "resources" in include:
        result["resources"] = monitor.resources.to_dict()
    if "tasks" in include:
        result["task_scheduler"] = monitor.task_scheduler.to_dict()
    if "startup" in include:
        result["startup_apps"] = monitor.startup_apps.to_dict()
    if "alerts" in include:
        result["alerts"] = monitor._check_alerts()

    return result


async def handle_gpu_status(params: Dict[str, Any]) -> Dict[str, Any]:
    """MCP handler for GPU status"""
    monitor = get_monitor()
    return monitor.gpu.to_dict()


async def handle_task_scheduler(params: Dict[str, Any]) -> Dict[str, Any]:
    """MCP handler for task scheduler"""
    monitor = get_monitor()

    action = params.get("action", "status")

    if action == "status":
        return monitor.task_scheduler.to_dict()
    elif action == "list":
        return {"tasks": monitor.task_scheduler.get_tasks()}
    elif action == "failed":
        return {"failed_tasks": monitor.task_scheduler.get_failed_tasks()}

    return {"error": f"Unknown action: {action}"}


async def handle_startup_apps(params: Dict[str, Any]) -> Dict[str, Any]:
    """MCP handler for startup apps"""
    monitor = get_monitor()
    return monitor.startup_apps.to_dict()


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    monitor = SystemMonitor()
    status = monitor.get_full_status()
    print(json.dumps(status, indent=2, default=str))
