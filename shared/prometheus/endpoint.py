# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

"""Prometheus metrics endpoint factory for FastAPI.

Provides a factory function to create a /metrics endpoint that exposes
all registered Prometheus metrics in the standard exposition format.

Usage:
    from shared.prometheus import create_metrics_endpoint

    app = FastAPI()
    app.include_router(create_metrics_endpoint())
"""

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest


def create_metrics_endpoint(path: str = "/metrics") -> APIRouter:
    """Create a FastAPI router with Prometheus metrics endpoint.

    Args:
        path: URL path for the metrics endpoint (default: /metrics)

    Returns:
        FastAPI APIRouter with the metrics endpoint

    Usage:
        app = FastAPI()
        app.include_router(create_metrics_endpoint())

        # Or with custom path:
        app.include_router(create_metrics_endpoint("/prometheus/metrics"))
    """
    router = APIRouter(tags=["monitoring"])

    @router.get(path, include_in_schema=False)
    async def metrics() -> Response:
        """Expose Prometheus metrics.

        Returns:
            Response with Prometheus metrics in text format
        """
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )

    return router
