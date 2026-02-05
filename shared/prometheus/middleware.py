# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

"""FastAPI Prometheus middleware for automatic HTTP metrics collection.

This middleware automatically collects HTTP request metrics including:
- Request count (QPS)
- Request duration distribution
- Status code distribution
- In-progress request count

Features:
- Route template normalization (converts /api/tasks/123 to /api/tasks/{task_id})
- Configurable path exclusion (e.g., /health, /metrics)
- Request ID extraction from request.state
"""

import re
import time
from typing import Callable, Set

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from shared.prometheus.metrics import (
    HTTP_REQUESTS_IN_PROGRESS,
    record_http_request,
)


# Regex patterns for route parameter normalization
# Matches numeric IDs in paths like /tasks/123 or /users/456
NUMERIC_PATH_PATTERN = re.compile(r"/(\d+)(?=/|$)")
# Matches UUID patterns in paths
UUID_PATH_PATTERN = re.compile(
    r"/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})(?=/|$)",
    re.IGNORECASE,
)


def normalize_route(path: str, route_template: str | None = None) -> str:
    """Normalize a request path to a route template.

    Converts actual path values to template placeholders to prevent
    label cardinality explosion.

    Args:
        path: The actual request path (e.g., /api/tasks/123)
        route_template: Optional route template from FastAPI router

    Returns:
        Normalized route template (e.g., /api/tasks/{task_id})

    Examples:
        >>> normalize_route("/api/tasks/123")
        '/api/tasks/{id}'
        >>> normalize_route("/api/users/abc-def-123")
        '/api/users/{id}'
    """
    if route_template:
        return route_template

    # Replace UUIDs with {uuid}
    normalized = UUID_PATH_PATTERN.sub(r"/{uuid}", path)
    # Replace numeric IDs with {id}
    normalized = NUMERIC_PATH_PATTERN.sub(r"/{id}", normalized)

    return normalized


def get_route_template(request: Request) -> str:
    """Extract route template from FastAPI request.

    Attempts to get the route template from FastAPI's routing system.
    Falls back to path normalization if not available.

    Args:
        request: Starlette/FastAPI request object

    Returns:
        Route template string
    """
    # Try to get route from FastAPI's scope
    route = request.scope.get("route")
    if route and hasattr(route, "path"):
        return route.path

    # Fall back to path normalization
    return normalize_route(request.url.path)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for Prometheus HTTP metrics collection.

    Automatically records:
    - http_requests_total: Counter with method, route, status_code, request_id
    - http_request_duration_seconds: Histogram with same labels
    - http_requests_in_progress: Gauge with method, route

    Usage:
        app = FastAPI()
        app.add_middleware(PrometheusMiddleware, excluded_paths={"/health", "/metrics"})
    """

    def __init__(
        self,
        app: Callable,
        excluded_paths: Set[str] | None = None,
    ):
        """Initialize PrometheusMiddleware.

        Args:
            app: ASGI application
            excluded_paths: Set of paths to exclude from metrics collection
        """
        super().__init__(app)
        self.excluded_paths = excluded_paths or {
            "/",
            "/health",
            "/ready",
            "/startup",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and record metrics.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response
        """
        path = request.url.path

        # Skip excluded paths
        if path in self.excluded_paths:
            return await call_next(request)

        # Get route template for metrics
        route = get_route_template(request)
        method = request.method

        # Get request_id from request state (set by logging middleware)
        request_id = getattr(request.state, "request_id", "")

        # Track in-progress requests
        HTTP_REQUESTS_IN_PROGRESS.labels(method=method, route=route).inc()

        start_time = time.perf_counter()
        status_code = 500  # Default in case of exception

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            # Re-raise after recording metrics
            raise
        finally:
            # Record metrics
            duration = time.perf_counter() - start_time
            record_http_request(
                method=method,
                route=route,
                status_code=status_code,
                duration=duration,
                request_id=request_id,
            )
            HTTP_REQUESTS_IN_PROGRESS.labels(method=method, route=route).dec()
