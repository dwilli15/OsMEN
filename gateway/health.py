#!/usr/bin/env python3
"""
Health Check Endpoints for OsMEN v3.0 Gateway

Provides Kubernetes-compatible health checks:
- /health - Overall system health
- /health/live - Liveness probe
- /health/ready - Readiness probe
- /metrics - Prometheus metrics

Usage:
    From gateway/main.py, include these routes
"""

from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse
import time
import psutil
import os
from typing import Dict, Any
from datetime import datetime

router = APIRouter(prefix="/health", tags=["health"])

# Track startup time
START_TIME = time.time()

def get_system_metrics() -> Dict[str, Any]:
    """Get system resource metrics"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu': {
                'percent': cpu_percent,
                'count': psutil.cpu_count()
            },
            'memory': {
                'total_mb': round(memory.total / (1024 * 1024), 2),
                'available_mb': round(memory.available / (1024 * 1024), 2),
                'percent': memory.percent
            },
            'disk': {
                'total_gb': round(disk.total / (1024 * 1024 * 1024), 2),
                'free_gb': round(disk.free / (1024 * 1024 * 1024), 2),
                'percent': disk.percent
            }
        }
    except Exception as e:
        return {'error': str(e)}


def check_database() -> Dict[str, Any]:
    """Check PostgreSQL database connectivity"""
    try:
        import psycopg2
        conn_str = os.getenv('DATABASE_URL', '')
        
        if not conn_str:
            return {'status': 'unconfigured', 'healthy': False}
        
        conn = psycopg2.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        cursor.close()
        conn.close()
        
        return {'status': 'healthy', 'healthy': True}
    except Exception as e:
        return {'status': 'unhealthy', 'healthy': False, 'error': str(e)}


def check_redis() -> Dict[str, Any]:
    """Check Redis connectivity"""
    try:
        import redis
        redis_url = os.getenv('REDIS_URL', '')
        
        if not redis_url:
            return {'status': 'unconfigured', 'healthy': False}
        
        r = redis.from_url(redis_url)
        r.ping()
        
        return {'status': 'healthy', 'healthy': True}
    except Exception as e:
        return {'status': 'unhealthy', 'healthy': False, 'error': str(e)}


def check_qdrant() -> Dict[str, Any]:
    """Check Qdrant vector database connectivity"""
    try:
        from qdrant_client import QdrantClient
        qdrant_url = os.getenv('QDRANT_URL', 'http://localhost:6333')
        
        client = QdrantClient(url=qdrant_url)
        collections = client.get_collections()
        
        return {
            'status': 'healthy',
            'healthy': True,
            'collections_count': len(collections.collections)
        }
    except Exception as e:
        return {'status': 'unhealthy', 'healthy': False, 'error': str(e)}


@router.get("")
@router.get("/")
async def health_check():
    """
    Overall health check - returns detailed system status
    
    Returns 200 if all critical systems are healthy
    Returns 503 if any critical system is unhealthy
    """
    uptime_seconds = time.time() - START_TIME
    
    # Check all systems
    db_health = check_database()
    redis_health = check_redis()
    qdrant_health = check_qdrant()
    system_metrics = get_system_metrics()
    
    # Determine overall health
    critical_systems = [db_health, redis_health, qdrant_health]
    all_healthy = all(sys.get('healthy', False) for sys in critical_systems)
    
    health_status = {
        'status': 'healthy' if all_healthy else 'degraded',
        'timestamp': datetime.utcnow().isoformat(),
        'uptime_seconds': round(uptime_seconds, 2),
        'version': os.getenv('APP_VERSION', '3.0.0'),
        'environment': os.getenv('ENVIRONMENT', 'development'),
        'components': {
            'database': db_health,
            'redis': redis_health,
            'qdrant': qdrant_health
        },
        'system': system_metrics
    }
    
    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(content=health_status, status_code=status_code)


@router.get("/live")
async def liveness_probe():
    """
    Kubernetes liveness probe
    
    Returns 200 if the application is running
    This should almost always return 200 unless the app is completely dead
    """
    uptime = time.time() - START_TIME
    
    return {
        'status': 'alive',
        'uptime_seconds': round(uptime, 2),
        'timestamp': datetime.utcnow().isoformat()
    }


@router.get("/ready")
async def readiness_probe():
    """
    Kubernetes readiness probe
    
    Returns 200 if the application is ready to serve traffic
    Returns 503 if not ready (dependencies unavailable)
    """
    # Check critical dependencies
    db_healthy = check_database().get('healthy', False)
    redis_healthy = check_redis().get('healthy', False)
    
    is_ready = db_healthy and redis_healthy
    
    readiness_status = {
        'status': 'ready' if is_ready else 'not_ready',
        'timestamp': datetime.utcnow().isoformat(),
        'checks': {
            'database': 'healthy' if db_healthy else 'unhealthy',
            'redis': 'healthy' if redis_healthy else 'unhealthy'
        }
    }
    
    status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(content=readiness_status, status_code=status_code)


@router.get("/startup")
async def startup_probe():
    """
    Kubernetes startup probe
    
    Returns 200 once the application has finished starting up
    """
    uptime = time.time() - START_TIME
    startup_timeout = int(os.getenv('STARTUP_TIMEOUT', '30'))
    
    # Application is considered started after minimum uptime
    is_started = uptime > 5  # 5 seconds minimum
    
    return {
        'status': 'started' if is_started else 'starting',
        'uptime_seconds': round(uptime, 2),
        'timestamp': datetime.utcnow().isoformat()
    }


# Prometheus metrics endpoint
@router.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint
    
    Returns metrics in Prometheus text format
    """
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        metrics_output = generate_latest()
        return Response(content=metrics_output, media_type=CONTENT_TYPE_LATEST)
    except ImportError:
        # Fallback if prometheus_client not installed
        uptime = time.time() - START_TIME
        system = get_system_metrics()
        
        metrics_text = f"""# HELP osmen_uptime_seconds Application uptime in seconds
# TYPE osmen_uptime_seconds gauge
osmen_uptime_seconds {uptime}

# HELP osmen_cpu_percent CPU usage percentage
# TYPE osmen_cpu_percent gauge
osmen_cpu_percent {system['cpu']['percent']}

# HELP osmen_memory_percent Memory usage percentage
# TYPE osmen_memory_percent gauge
osmen_memory_percent {system['memory']['percent']}

# HELP osmen_disk_percent Disk usage percentage
# TYPE osmen_disk_percent gauge
osmen_disk_percent {system['disk']['percent']}
"""
        return Response(content=metrics_text, media_type="text/plain")


# Detailed diagnostics (for debugging)
@router.get("/diagnostics")
async def diagnostics():
    """
    Detailed diagnostics information
    
    Returns comprehensive system diagnostics for troubleshooting
    """
    return {
        'timestamp': datetime.utcnow().isoformat(),
        'system': {
            'hostname': os.uname().nodename,
            'platform': os.uname().system,
            'python_version': os.sys.version,
            'pid': os.getpid(),
            **get_system_metrics()
        },
        'application': {
            'version': os.getenv('APP_VERSION', '3.0.0'),
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'uptime_seconds': round(time.time() - START_TIME, 2),
            'start_time': datetime.fromtimestamp(START_TIME).isoformat()
        },
        'dependencies': {
            'database': check_database(),
            'redis': check_redis(),
            'qdrant': check_qdrant()
        },
        'environment_variables': {
            key: ('***' if 'PASSWORD' in key or 'SECRET' in key or 'KEY' in key else value)
            for key, value in os.environ.items()
            if key.startswith('OSMEN_') or key.startswith('APP_')
        }
    }


if __name__ == "__main__":
    # Test health check locally
    import asyncio
    
    async def test():
        print("Testing health endpoints...")
        print("\nOverall Health:")
        result = await health_check()
        print(result)
        
        print("\nLiveness:")
        result = await liveness_probe()
        print(result)
        
        print("\nReadiness:")
        result = await readiness_probe()
        print(result)
    
    asyncio.run(test())
