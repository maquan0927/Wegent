# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

"""Prometheus monitoring utilities for Wegent services.

This module provides:
- HTTP request metrics (Counter, Histogram, Gauge)
- FastAPI middleware for automatic metrics collection
- Metrics endpoint factory for /metrics route
- Utility functions for route template normalization

Usage:
    from shared.prometheus import (
        PrometheusMiddleware,
        create_metrics_endpoint,
        http_metrics,
    )

    # Add middleware to FastAPI app
    app.add_middleware(PrometheusMiddleware)

    # Add /metrics endpoint
    app.include_router(create_metrics_endpoint())
"""

from shared.prometheus.endpoint import create_metrics_endpoint
from shared.prometheus.metrics import (
    HTTP_REQUEST_DURATION_BUCKETS,
    HTTP_REQUESTS_IN_PROGRESS,
    HTTP_REQUESTS_TOTAL,
    http_request_duration_seconds,
    record_http_request,
)
from shared.prometheus.middleware import PrometheusMiddleware

__all__ = [
    # Metrics
    "HTTP_REQUESTS_TOTAL",
    "http_request_duration_seconds",
    "HTTP_REQUESTS_IN_PROGRESS",
    "HTTP_REQUEST_DURATION_BUCKETS",
    "record_http_request",
    # Middleware
    "PrometheusMiddleware",
    # Endpoint
    "create_metrics_endpoint",
]
