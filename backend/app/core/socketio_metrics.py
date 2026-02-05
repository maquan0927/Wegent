# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

"""Socket.IO Prometheus metrics for real-time communication monitoring.

This module provides metrics for monitoring Socket.IO connections and messages:
- Connection events (connect/disconnect)
- Active connection counts
- Message traffic by namespace and event
- Message processing duration

All metrics follow the same labeling conventions as HTTP metrics for consistency.
"""

import time
from contextlib import contextmanager
from typing import Generator

from prometheus_client import Counter, Gauge, Histogram

# Histogram buckets starting from 0.1 seconds for Socket.IO
SOCKETIO_DURATION_BUCKETS = (
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

# Connection metrics
SOCKETIO_CONNECTIONS_TOTAL = Counter(
    "socketio_connections_total",
    "Total Socket.IO connection events",
    ["namespace", "event_type", "request_id"],
)

SOCKETIO_CONNECTIONS_ACTIVE = Gauge(
    "socketio_connections_active",
    "Current active Socket.IO connections",
    ["namespace"],
)

# Message metrics
SOCKETIO_MESSAGES_TOTAL = Counter(
    "socketio_messages_total",
    "Total Socket.IO messages",
    ["namespace", "event", "direction", "request_id"],
)

SOCKETIO_MESSAGE_DURATION = Histogram(
    "socketio_message_duration_seconds",
    "Socket.IO message processing duration",
    ["namespace", "event", "request_id"],
    buckets=SOCKETIO_DURATION_BUCKETS,
)


def record_connection(
    namespace: str,
    event_type: str,
    request_id: str = "",
) -> None:
    """Record a Socket.IO connection event.

    Args:
        namespace: Socket.IO namespace (e.g., /chat, /local-executor)
        event_type: Event type (connect or disconnect)
        request_id: Unique request identifier
    """
    SOCKETIO_CONNECTIONS_TOTAL.labels(
        namespace=namespace,
        event_type=event_type,
        request_id=request_id,
    ).inc()

    # Update active connections gauge
    if event_type == "connect":
        SOCKETIO_CONNECTIONS_ACTIVE.labels(namespace=namespace).inc()
    elif event_type == "disconnect":
        SOCKETIO_CONNECTIONS_ACTIVE.labels(namespace=namespace).dec()


def record_message(
    namespace: str,
    event: str,
    direction: str,
    request_id: str = "",
) -> None:
    """Record a Socket.IO message.

    Args:
        namespace: Socket.IO namespace
        event: Event name (e.g., chat:send, task:join)
        direction: Message direction (send or receive)
        request_id: Unique request identifier
    """
    SOCKETIO_MESSAGES_TOTAL.labels(
        namespace=namespace,
        event=event,
        direction=direction,
        request_id=request_id,
    ).inc()


@contextmanager
def track_message_duration(
    namespace: str,
    event: str,
    request_id: str = "",
) -> Generator[None, None, None]:
    """Context manager to track Socket.IO message processing duration.

    Args:
        namespace: Socket.IO namespace
        event: Event name
        request_id: Unique request identifier

    Yields:
        None

    Example:
        with track_message_duration("/chat", "chat:send", request_id):
            # Process message
            pass
    """
    start_time = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - start_time
        SOCKETIO_MESSAGE_DURATION.labels(
            namespace=namespace,
            event=event,
            request_id=request_id,
        ).observe(duration)


def record_message_with_duration(
    namespace: str,
    event: str,
    direction: str,
    duration: float,
    request_id: str = "",
) -> None:
    """Record a Socket.IO message with its processing duration.

    Args:
        namespace: Socket.IO namespace
        event: Event name
        direction: Message direction (send or receive)
        duration: Processing duration in seconds
        request_id: Unique request identifier
    """
    record_message(namespace, event, direction, request_id)
    SOCKETIO_MESSAGE_DURATION.labels(
        namespace=namespace,
        event=event,
        request_id=request_id,
    ).observe(duration)
