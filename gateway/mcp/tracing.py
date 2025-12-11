"""
OpenTelemetry Tracing for OsMEN MCP Server
Provides distributed tracing, metrics, and observability
"""

import functools
import logging
import os
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Callable, Dict, Optional

# OpenTelemetry imports with graceful fallback
OTEL_AVAILABLE = False
try:
    from opentelemetry import trace
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.trace import SpanKind, Status, StatusCode
    from opentelemetry.trace.propagation.tracecontext import (
        TraceContextTextMapPropagator,
    )

    # Optional exporters
    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )

        OTLP_AVAILABLE = True
    except ImportError:
        OTLP_AVAILABLE = False

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    OTLP_AVAILABLE = False

logger = logging.getLogger(__name__)


class TracingConfig:
    """Tracing configuration from environment"""

    def __init__(self):
        self.enabled = os.getenv("OTEL_ENABLED", "true").lower() == "true"
        self.service_name = os.getenv("OTEL_SERVICE_NAME", "osmen-mcp-server")
        self.service_version = os.getenv("OTEL_SERVICE_VERSION", "2.0.0")
        self.environment = os.getenv("OTEL_ENVIRONMENT", "development")

        # Exporter settings
        self.exporter_type = os.getenv(
            "OTEL_EXPORTER_TYPE", "console"
        )  # console, otlp, none
        self.otlp_endpoint = os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"
        )

        # Sampling
        self.sample_rate = float(os.getenv("OTEL_SAMPLE_RATE", "1.0"))

        # Log correlation
        self.log_correlation = (
            os.getenv("OTEL_LOG_CORRELATION", "true").lower() == "true"
        )


class NullSpan:
    """Null object pattern for when tracing is disabled"""

    def set_attribute(self, key: str, value: Any) -> None:
        pass

    def set_status(self, status: Any) -> None:
        pass

    def record_exception(self, exception: Exception) -> None:
        pass

    def add_event(self, name: str, attributes: Optional[Dict] = None) -> None:
        pass

    def end(self) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class NullTracer:
    """Null tracer for when OTEL is not available"""

    @contextmanager
    def start_as_current_span(self, name: str, **kwargs):
        yield NullSpan()

    def start_span(self, name: str, **kwargs) -> NullSpan:
        return NullSpan()


class TracingManager:
    """
    Manages OpenTelemetry tracing for OsMEN MCP Server.

    Features:
    - Automatic span creation for tool calls
    - Request/response attribute recording
    - Error tracking and exception recording
    - Distributed trace context propagation
    - Graceful degradation when OTEL unavailable
    """

    _instance: Optional["TracingManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.config = TracingConfig()
        self._tracer: Any = None
        self._provider: Any = None
        self._initialized = True

        if self.config.enabled and OTEL_AVAILABLE:
            self._setup_tracing()
        else:
            logger.info("OpenTelemetry tracing disabled or unavailable")
            self._tracer = NullTracer()

    def _setup_tracing(self) -> None:
        """Initialize OpenTelemetry with configured exporters"""
        try:
            # Create resource with service info
            resource = Resource.create(
                {
                    SERVICE_NAME: self.config.service_name,
                    "service.version": self.config.service_version,
                    "deployment.environment": self.config.environment,
                    "service.namespace": "osmen",
                }
            )

            # Create tracer provider
            self._provider = TracerProvider(resource=resource)

            # Configure exporter based on config
            if self.config.exporter_type == "otlp" and OTLP_AVAILABLE:
                exporter = OTLPSpanExporter(endpoint=self.config.otlp_endpoint)
                logger.info(f"OTLP exporter configured: {self.config.otlp_endpoint}")
            elif self.config.exporter_type == "console":
                exporter = ConsoleSpanExporter()
                logger.info("Console span exporter configured")
            else:
                exporter = None
                logger.info("No span exporter configured")

            if exporter:
                self._provider.add_span_processor(BatchSpanProcessor(exporter))

            # Set as global provider
            trace.set_tracer_provider(self._provider)

            # Get tracer
            self._tracer = trace.get_tracer(
                self.config.service_name,
                self.config.service_version,
            )

            logger.info(
                f"OpenTelemetry tracing initialized: {self.config.service_name}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry: {e}")
            self._tracer = NullTracer()

    @property
    def tracer(self):
        """Get the configured tracer"""
        return self._tracer

    def create_span(
        self,
        name: str,
        kind: Optional[Any] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        """Create a new span with optional attributes"""
        if not OTEL_AVAILABLE or isinstance(self._tracer, NullTracer):
            return NullSpan()

        span_kind = kind if kind else SpanKind.INTERNAL
        return self._tracer.start_as_current_span(
            name,
            kind=span_kind,
            attributes=attributes or {},
        )

    def record_tool_call(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        result: Any,
        duration_ms: float,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """Record a tool call as a span"""
        with self.create_span(
            f"tool.{tool_name}",
            attributes={
                "tool.name": tool_name,
                "tool.parameters": str(parameters)[:500],  # Truncate for safety
                "tool.duration_ms": duration_ms,
                "tool.success": success,
            },
        ) as span:
            if error:
                span.set_attribute("tool.error", error)
                if OTEL_AVAILABLE:
                    span.set_status(Status(StatusCode.ERROR, error))

            span.set_attribute("tool.result_size", len(str(result)))

    def shutdown(self) -> None:
        """Shutdown tracing and flush spans"""
        if self._provider and hasattr(self._provider, "shutdown"):
            self._provider.shutdown()


def get_tracer():
    """Get the global tracer instance"""
    return TracingManager().tracer


def traced(span_name: Optional[str] = None):
    """
    Decorator to trace function execution.

    Usage:
        @traced("my_operation")
        def my_function(arg1, arg2):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            name = span_name or f"{func.__module__}.{func.__name__}"
            manager = TracingManager()

            with manager.create_span(name) as span:
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                start_time = datetime.now()
                try:
                    result = await func(*args, **kwargs)
                    duration = (datetime.now() - start_time).total_seconds() * 1000
                    span.set_attribute("function.duration_ms", duration)
                    return result
                except Exception as e:
                    span.record_exception(e)
                    if OTEL_AVAILABLE:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            name = span_name or f"{func.__module__}.{func.__name__}"
            manager = TracingManager()

            with manager.create_span(name) as span:
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                start_time = datetime.now()
                try:
                    result = func(*args, **kwargs)
                    duration = (datetime.now() - start_time).total_seconds() * 1000
                    span.set_attribute("function.duration_ms", duration)
                    return result
                except Exception as e:
                    span.record_exception(e)
                    if OTEL_AVAILABLE:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


class TracingMiddleware:
    """
    ASGI middleware for request tracing.

    Automatically creates spans for incoming HTTP requests with:
    - HTTP method and path
    - Request headers (filtered)
    - Response status code
    - Request duration
    """

    SENSITIVE_HEADERS = {"authorization", "cookie", "x-api-key", "api-key"}

    def __init__(self, app):
        self.app = app
        self.manager = TracingManager()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "/")

        with self.manager.create_span(
            f"HTTP {method} {path}",
            attributes={
                "http.method": method,
                "http.path": path,
                "http.scheme": scope.get("scheme", "http"),
            },
        ) as span:
            # Extract safe headers
            headers = dict(scope.get("headers", []))
            for key, value in headers.items():
                key_str = key.decode() if isinstance(key, bytes) else key
                if key_str.lower() not in self.SENSITIVE_HEADERS:
                    span.set_attribute(
                        f"http.header.{key_str}",
                        value.decode() if isinstance(value, bytes) else value,
                    )

            # Track response status
            response_status = [None]

            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    response_status[0] = message.get("status", 200)
                    span.set_attribute("http.status_code", response_status[0])
                await send(message)

            try:
                start_time = datetime.now()
                await self.app(scope, receive, send_wrapper)
                duration = (datetime.now() - start_time).total_seconds() * 1000
                span.set_attribute("http.duration_ms", duration)

            except Exception as e:
                span.record_exception(e)
                if OTEL_AVAILABLE:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                raise
