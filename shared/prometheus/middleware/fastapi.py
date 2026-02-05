# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

"""FastAPI Prometheus middleware.

Provides automatic metrics collection for FastAPI applications.
"""

import time
from typing import Callable, Set

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse

from shared.prometheus.config import get_prometheus_config
from shared.prometheus.metrics.http import get_http_metrics
from shared.prometheus.utils import get_route_template, normalize_route

# Default paths to exclude from metrics
DEFAULT_EXCLUDED_PATHS: Set[str] = {
    "/",
    "/health",
    "/healthz",
    "/ready",
    "/readiness",
    "/live",
    "/liveness",
}


class PrometheusMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for Prometheus metrics collection.

    Automatically collects HTTP request metrics:
    - Request counts by method, endpoint, and status
    - Request latency distribution
    - Concurrent request tracking

    Usage:
        from shared.prometheus.middleware import PrometheusMiddleware

        app.add_middleware(PrometheusMiddleware)
    """

    def __init__(
        self,
        app,
        excluded_paths: Set[str] = None,
    ):
        """Initialize the middleware.

        Args:
            app: The ASGI application
            excluded_paths: Set of paths to exclude from metrics collection.
                           Defaults to health check endpoints.
        """
        super().__init__(app)
        self._metrics = get_http_metrics()
        self._config = get_prometheus_config()

        # Merge default excluded paths with custom ones
        self._excluded_paths = DEFAULT_EXCLUDED_PATHS.copy()
        if excluded_paths:
            self._excluded_paths.update(excluded_paths)

        # Always exclude the metrics endpoint itself
        self._excluded_paths.add(self._config.metrics_path)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and collect metrics.

        Args:
            request: The incoming request
            call_next: The next middleware/handler in the chain

        Returns:
            The response from the handler
        """
        path = request.url.path

        # Skip excluded paths
        if path in self._excluded_paths:
            return await call_next(request)

        # Get normalized endpoint for metrics labels
        route_template = get_route_template(request)
        endpoint = normalize_route(route_template, path)
        method = request.method

        # Track in-progress requests
        self._metrics.inc_in_progress(method, endpoint)
        start_time = time.time()

        try:
            response = await call_next(request)

            # Handle streaming responses
            if isinstance(response, StreamingResponse):
                # Wrap the body iterator to measure total time
                original_body_iterator = response.body_iterator

                async def timed_body_iterator():
                    try:
                        async for chunk in original_body_iterator:
                            yield chunk
                    finally:
                        # Record metrics after streaming completes
                        duration = time.time() - start_time
                        self._metrics.observe_request(
                            method=method,
                            endpoint=endpoint,
                            status_code=response.status_code,
                            duration_seconds=duration,
                        )
                        self._metrics.dec_in_progress(method, endpoint)

                response.body_iterator = timed_body_iterator()
                return response

            # Record metrics for non-streaming responses
            duration = time.time() - start_time
            self._metrics.observe_request(
                method=method,
                endpoint=endpoint,
                status_code=response.status_code,
                duration_seconds=duration,
            )
            self._metrics.dec_in_progress(method, endpoint)

            return response

        except Exception:
            # Record error metrics on exception
            duration = time.time() - start_time
            self._metrics.observe_request(
                method=method,
                endpoint=endpoint,
                status_code=500,
                duration_seconds=duration,
            )
            self._metrics.dec_in_progress(method, endpoint)
            raise


def setup_prometheus_endpoint(app, path: str = None):
    """Add the Prometheus metrics endpoint to a FastAPI app.

    Args:
        app: FastAPI application instance
        path: Path for the metrics endpoint. If None, uses config value.
    """
    from fastapi import APIRouter, Response
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

    from shared.prometheus.registry import get_registry

    config = get_prometheus_config()
    metrics_path = path or config.metrics_path

    # Create a dedicated router for metrics endpoint
    metrics_router = APIRouter()

    @metrics_router.get(metrics_path, include_in_schema=False)
    async def metrics():
        """Prometheus metrics endpoint."""
        registry = get_registry()
        return Response(
            content=generate_latest(registry),
            media_type=CONTENT_TYPE_LATEST,
        )

    # Include the router in the app
    app.include_router(metrics_router)
