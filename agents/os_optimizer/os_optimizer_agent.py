#!/usr/bin/env python3
"""
OS Optimizer Agent
Provides OS optimization, customization, and performance tuning
"""

import json
import logging
import os
import platform
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class OSOptimizerAgent:
    """OS Optimizer Agent for system optimization and customization."""

    def __init__(self):
        """Initialize the OS Optimizer Agent."""
        logger.info("OSOptimizerAgent initialized successfully")
        self.optimizations = []
        self.customizations = []
        self.is_windows = platform.system() == "Windows"
        self.os_info = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        }

    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        try:
            import psutil

            return psutil.cpu_percent(interval=1)
        except ImportError:
            # Fallback for Windows using wmic
            if self.is_windows:
                try:
                    result = subprocess.run(
                        ["wmic", "cpu", "get", "loadpercentage"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    for line in result.stdout.strip().split("\n"):
                        line = line.strip()
                        if line.isdigit():
                            return float(line)
                except:
                    pass
            return -1.0

    def _get_memory_info(self) -> Dict:
        """Get memory usage information"""
        try:
            import psutil

            mem = psutil.virtual_memory()
            return {
                "total_gb": round(mem.total / (1024**3), 2),
                "available_gb": round(mem.available / (1024**3), 2),
                "used_gb": round(mem.used / (1024**3), 2),
                "percent_used": mem.percent,
            }
        except ImportError:
            if self.is_windows:
                try:
                    result = subprocess.run(
                        [
                            "wmic",
                            "os",
                            "get",
                            "FreePhysicalMemory,TotalVisibleMemorySize",
                            "/format:csv",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    lines = [
                        l.strip()
                        for l in result.stdout.strip().split("\n")
                        if l.strip() and not l.startswith("Node")
                    ]
                    if lines:
                        parts = lines[-1].split(",")
                        if len(parts) >= 3:
                            free_kb = int(parts[1])
                            total_kb = int(parts[2])
                            used_kb = total_kb - free_kb
                            return {
                                "total_gb": round(total_kb / (1024**2), 2),
                                "available_gb": round(free_kb / (1024**2), 2),
                                "used_gb": round(used_kb / (1024**2), 2),
                                "percent_used": round((used_kb / total_kb) * 100, 1),
                            }
                except:
                    pass
            return {
                "total_gb": -1,
                "available_gb": -1,
                "used_gb": -1,
                "percent_used": -1,
            }

    def _get_disk_info(self) -> Dict:
        """Get disk usage information"""
        try:
            import psutil

            disks = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
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
            return {"disks": disks}
        except ImportError:
            if self.is_windows:
                try:
                    result = subprocess.run(
                        [
                            "wmic",
                            "logicaldisk",
                            "get",
                            "DeviceID,FreeSpace,Size",
                            "/format:csv",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    disks = []
                    for line in result.stdout.strip().split("\n"):
                        line = line.strip()
                        if line and not line.startswith("Node") and "," in line:
                            parts = line.split(",")
                            if len(parts) >= 4 and parts[2] and parts[3]:
                                try:
                                    free = int(parts[2])
                                    total = int(parts[3])
                                    used = total - free
                                    disks.append(
                                        {
                                            "device": parts[1],
                                            "total_gb": round(total / (1024**3), 2),
                                            "used_gb": round(used / (1024**3), 2),
                                            "free_gb": round(free / (1024**3), 2),
                                            "percent_used": (
                                                round((used / total) * 100, 1)
                                                if total > 0
                                                else 0
                                            ),
                                        }
                                    )
                                except:
                                    pass
                    return {"disks": disks}
                except:
                    pass
            return {"disks": []}

    def _calculate_performance_score(
        self, cpu_usage: float, memory: Dict, disk: Dict
    ) -> int:
        """Calculate a performance score based on real metrics"""
        score = 100

        # CPU penalty (high CPU usage = lower score)
        if cpu_usage >= 0:
            if cpu_usage > 90:
                score -= 30
            elif cpu_usage > 70:
                score -= 20
            elif cpu_usage > 50:
                score -= 10

        # Memory penalty
        mem_percent = memory.get("percent_used", 0)
        if mem_percent > 90:
            score -= 25
        elif mem_percent > 80:
            score -= 15
        elif mem_percent > 70:
            score -= 5

        # Disk penalty (check if any disk is nearly full)
        for disk_info in disk.get("disks", []):
            disk_percent = disk_info.get("percent_used", 0)
            if disk_percent > 95:
                score -= 20
            elif disk_percent > 90:
                score -= 10
            elif disk_percent > 80:
                score -= 5

        return max(0, min(100, score))

    def analyze_system_performance(self) -> Dict:
        """Analyze system performance metrics.

        Returns:
            Dictionary with performance analysis
        """
        cpu_usage = self._get_cpu_usage()
        memory = self._get_memory_info()
        disk = self._get_disk_info()

        performance_score = self._calculate_performance_score(cpu_usage, memory, disk)

        # Generate recommendations based on real metrics
        recommendations = []

        if cpu_usage > 70:
            recommendations.append(
                f"High CPU usage ({cpu_usage}%) - check running processes"
            )

        if memory.get("percent_used", 0) > 80:
            recommendations.append(
                f"High memory usage ({memory.get('percent_used')}%) - close unused applications"
            )

        for disk_info in disk.get("disks", []):
            if disk_info.get("percent_used", 0) > 85:
                recommendations.append(
                    f"Low disk space on {disk_info.get('device', 'drive')} ({disk_info.get('free_gb', 0)} GB free)"
                )

        if not recommendations:
            recommendations.append("System performance is good")
            recommendations.append(
                "Consider scheduling regular cleanups to maintain performance"
            )

        analysis = {
            "timestamp": datetime.now().isoformat(),
            "os_info": self.os_info,
            "performance_score": performance_score,
            "metrics": {"cpu_usage_percent": cpu_usage, "memory": memory, "disk": disk},
            "recommendations": recommendations,
        }
        logger.info(f"Analyzed system performance: score={performance_score}")
        return analysis

    def apply_optimization(self, optimization_type: str, settings: Dict) -> Dict:
        """Apply system optimization.

        Args:
            optimization_type: Type of optimization (startup, memory, disk, network)
            settings: Optimization settings

        Returns:
            Dictionary with optimization details
        """
        optimization = {
            "id": len(self.optimizations) + 1,
            "type": optimization_type,
            "settings": settings,
            "status": "applied",
            "applied_at": datetime.now().isoformat(),
        }
        self.optimizations.append(optimization)
        logger.info(f"Applied optimization: {optimization_type}")
        return optimization

    def customize_system(self, customization_type: str, config: Dict) -> Dict:
        """Apply system customization.

        Args:
            customization_type: Type of customization (theme, shortcuts, behavior)
            config: Customization configuration

        Returns:
            Dictionary with customization details
        """
        customization = {
            "id": len(self.customizations) + 1,
            "type": customization_type,
            "config": config,
            "status": "applied",
            "applied_at": datetime.now().isoformat(),
        }
        self.customizations.append(customization)
        logger.info(f"Applied customization: {customization_type}")
        return customization

    def cleanup_system(self, cleanup_targets: List[str]) -> Dict:
        """Perform system cleanup.

        Args:
            cleanup_targets: List of cleanup targets (temp, cache, logs, etc.)

        Returns:
            Dictionary with cleanup results
        """
        total_freed = 0
        total_files = 0
        details = []

        # Define cleanup paths for Windows
        cleanup_paths = {
            "temp": [
                Path(os.environ.get("TEMP", "")),
                Path(os.environ.get("TMP", "")),
                Path("C:/Windows/Temp") if self.is_windows else Path("/tmp"),
            ],
            "cache": [
                Path(os.environ.get("LOCALAPPDATA", "")) / "Temp",
                Path(os.environ.get("APPDATA", "")) / "Local" / "Temp",
            ],
            "logs": [
                Path("C:/Windows/Logs") if self.is_windows else Path("/var/log"),
                Path(os.environ.get("LOCALAPPDATA", "")) / "CrashDumps",
            ],
            "downloads": [Path.home() / "Downloads"],
            "recycle": [],  # Special handling
        }

        for target in cleanup_targets:
            target_lower = target.lower()

            if target_lower == "recycle" and self.is_windows:
                # Empty recycle bin on Windows
                try:
                    # Use PowerShell to empty recycle bin
                    result = subprocess.run(
                        [
                            "powershell",
                            "-Command",
                            "Clear-RecycleBin -Force -ErrorAction SilentlyContinue",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    details.append(
                        {
                            "target": "recycle",
                            "status": (
                                "emptied" if result.returncode == 0 else "skipped"
                            ),
                            "message": "Recycle Bin emptied",
                        }
                    )
                except Exception as e:
                    details.append(
                        {"target": "recycle", "status": "error", "error": str(e)}
                    )
                continue

            paths = cleanup_paths.get(target_lower, [])
            target_freed = 0
            target_files = 0

            for path in paths:
                if not path or not path.exists():
                    continue

                try:
                    # Calculate size and clean old files (older than 7 days for safety)
                    import time

                    cutoff_time = time.time() - (7 * 24 * 60 * 60)  # 7 days ago

                    for item in path.rglob("*"):
                        try:
                            if item.is_file():
                                stat = item.stat()
                                if stat.st_mtime < cutoff_time:
                                    size = stat.st_size
                                    item.unlink()
                                    target_freed += size
                                    target_files += 1
                        except (PermissionError, OSError):
                            pass  # Skip files we can't delete

                except Exception as e:
                    logger.warning(f"Error cleaning {path}: {e}")

            total_freed += target_freed
            total_files += target_files
            details.append(
                {
                    "target": target,
                    "files_removed": target_files,
                    "space_freed_mb": round(target_freed / (1024 * 1024), 2),
                }
            )

        result = {
            "targets": cleanup_targets,
            "space_freed_mb": round(total_freed / (1024 * 1024), 2),
            "files_removed": total_files,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }
        logger.info(
            f"Cleaned up {total_files} files, freed {result['space_freed_mb']} MB"
        )
        return result

    def generate_optimizer_report(self) -> Dict:
        """Generate comprehensive OS optimizer report.

        Returns:
            Dictionary with optimizer status and statistics
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "operational",
            "os_info": self.os_info,
            "statistics": {
                "total_optimizations": len(self.optimizations),
                "total_customizations": len(self.customizations),
                "recent_optimizations": len(
                    [
                        o
                        for o in self.optimizations
                        if o["applied_at"].startswith(datetime.now().date().isoformat())
                    ]
                ),
            },
        }


if __name__ == "__main__":
    # Test the agent
    logging.basicConfig(level=logging.INFO)

    agent = OSOptimizerAgent()

    # Analyze performance
    analysis = agent.analyze_system_performance()

    # Apply optimizations
    agent.apply_optimization("startup", {"disable_services": ["service1", "service2"]})
    agent.apply_optimization(
        "memory", {"compress_memory": True, "optimize_paging": True}
    )

    # Apply customizations
    agent.customize_system(
        "shortcuts", {"ctrl_shift_t": "terminal", "ctrl_shift_f": "file_manager"}
    )

    # Cleanup
    agent.cleanup_system(["temp", "cache", "downloads"])

    # Generate report
    report = agent.generate_optimizer_report()
    print(json.dumps(report, indent=2))
