# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

"""HTTP/API Prometheus metrics.

Provides metrics for HTTP request tracking:
- http_requests_total: Counter for total requests
- http_request_duration_seconds: Histogram for request latency
- http_requests_in_progress: Gauge for concurrent requests
"""

from typing import Optional

from prometheus_client import Counter, Gauge, Histogram

from shared.prometheus.registry import get_registry

# Histogram buckets starting from 0.1 seconds
# Covers: 0.1, 0.25, 0.5, 0.75, 1, 2.5, 5, 7.5, 10, 30, 60, 120, 300 seconds
HTTP_DURATION_BUCKETS = (
    0.1,
    0.25,
    0.5,
    0.75,
    1.0,
    2.5,
    5.0,
    7.5,
    10.0,
    30.0,
    60.0,
    120.0,
    300.0,
    float("inf"),
)


class HTTPMetrics:
    """HTTP metrics collection class.

    Provides metrics for monitoring HTTP API performance:
    - Request counts by endpoint, method, and status
    - Request latency distribution
    - Concurrent request tracking
    """

    def __init__(self, registry=None):
        """Initialize HTTP metrics.

        Args:
            registry: Optional Prometheus registry. Uses global registry if not provided.
        """
        self._registry = registry or get_registry()
        self._requests_total: Optional[Counter] = None
        self._request_duration: Optional[Histogram] = None
        self._requests_in_progress: Optional[Gauge] = None

    @property
    def requests_total(self) -> Counter:
        """Get or create the requests total counter."""
        if self._requests_total is None:
            self._requests_total = Counter(
                "http_requests_total",
                "Total number of HTTP requests",
                labelnames=["method", "endpoint", "status_code"],
                registry=self._registry,
            )
        return self._requests_total

    @property
    def request_duration(self) -> Histogram:
        """Get or create the request duration histogram."""
        if self._request_duration is None:
            self._request_duration = Histogram(
                "http_request_duration_seconds",
                "HTTP request duration in seconds",
                labelnames=["method", "endpoint", "status_code"],
                buckets=HTTP_DURATION_BUCKETS,
                registry=self._registry,
            )
        return self._request_duration

    @property
    def requests_in_progress(self) -> Gauge:
        """Get or create the requests in progress gauge."""
        if self._requests_in_progress is None:
            self._requests_in_progress = Gauge(
                "http_requests_in_progress",
                "Number of HTTP requests currently being processed",
                labelnames=["method", "endpoint"],
                registry=self._registry,
            )
        return self._requests_in_progress

    def observe_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration_seconds: float,
    ) -> None:
        """Record a completed HTTP request.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: Normalized endpoint path
            status_code: HTTP response status code
            duration_seconds: Request duration in seconds
        """
        status_str = str(status_code)
        self.requests_total.labels(
            method=method, endpoint=endpoint, status_code=status_str
        ).inc()
        self.request_duration.labels(
            method=method, endpoint=endpoint, status_code=status_str
        ).observe(duration_seconds)

    def inc_in_progress(self, method: str, endpoint: str) -> None:
        """Increment the in-progress counter for a request.

        Args:
            method: HTTP method
            endpoint: Normalized endpoint path
        """
        self.requests_in_progress.labels(method=method, endpoint=endpoint).inc()

    def dec_in_progress(self, method: str, endpoint: str) -> None:
        """Decrement the in-progress counter for a request.

        Args:
            method: HTTP method
            endpoint: Normalized endpoint path
        """
        self.requests_in_progress.labels(method=method, endpoint=endpoint).dec()


# Global instance
_http_metrics: Optional[HTTPMetrics] = None


def get_http_metrics() -> HTTPMetrics:
    """Get the global HTTP metrics instance.

    Returns:
        HTTPMetrics singleton instance.
    """
    global _http_metrics
    if _http_metrics is None:
        _http_metrics = HTTPMetrics()
    return _http_metrics


def reset_http_metrics() -> None:
    """Reset the global HTTP metrics (for testing)."""
    global _http_metrics
    _http_metrics = None
