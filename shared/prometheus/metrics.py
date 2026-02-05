# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

"""Core Prometheus metrics definitions for HTTP/WebSocket/Socket.IO monitoring.

This module defines shared metrics that can be used across backend and chat_shell services.
All metrics follow consistent labeling conventions for unified observability.

Metrics defined:
- http_requests_total: Counter for total HTTP requests
- http_request_duration_seconds: Histogram for request latency
- http_requests_in_progress: Gauge for concurrent requests

Label conventions:
- method: HTTP method (GET, POST, etc.)
- route: Route template (e.g., /api/tasks/{task_id})
- status_code: HTTP status code
- request_id: Unique request identifier for tracing
"""

from prometheus_client import Counter, Gauge, Histogram

# Histogram buckets starting from 0.1 seconds as specified
HTTP_REQUEST_DURATION_BUCKETS = (
    0.1,
    0.25,
    0.5,
    1.0,
    2.5,
    5.0,
    10.0,
    30.0,
    60.0,
    120.0,
)

# HTTP Request Metrics
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "route", "status_code", "request_id"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "route", "status_code", "request_id"],
    buckets=HTTP_REQUEST_DURATION_BUCKETS,
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently in progress",
    ["method", "route"],
)


def record_http_request(
    method: str,
    route: str,
    status_code: int,
    duration: float,
    request_id: str = "",
) -> None:
    """Record HTTP request metrics.

    Args:
        method: HTTP method (GET, POST, etc.)
        route: Route template (e.g., /api/tasks/{task_id})
        status_code: HTTP response status code
        duration: Request duration in seconds
        request_id: Unique request identifier
    """
    labels = {
        "method": method,
        "route": route,
        "status_code": str(status_code),
        "request_id": request_id,
    }
    HTTP_REQUESTS_TOTAL.labels(**labels).inc()
    http_request_duration_seconds.labels(**labels).observe(duration)
