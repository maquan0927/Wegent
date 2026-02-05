# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

"""MCP (Model Context Protocol) Prometheus metrics for Chat Shell.

This module provides metrics for monitoring MCP server interactions:
- Connection attempts and status
- Connection duration
- Tool call counts and status
- Tool execution duration

All metrics include request_id for tracing correlation.
"""

import time
from contextlib import contextmanager
from typing import Generator

from prometheus_client import Counter, Histogram

# Histogram buckets for MCP operations (starting from 0.1s)
MCP_DURATION_BUCKETS = (
    0.1,
    0.25,
    0.5,
    1.0,
    2.5,
    5.0,
    10.0,
    30.0,
    60.0,
)

# Connection metrics
MCP_CONNECTIONS_TOTAL = Counter(
    "mcp_connections_total",
    "Total MCP server connection attempts",
    ["server_name", "status", "request_id"],
)

MCP_CONNECTION_DURATION = Histogram(
    "mcp_connection_duration_seconds",
    "MCP server connection duration",
    ["server_name", "request_id"],
    buckets=MCP_DURATION_BUCKETS,
)

# Tool call metrics
MCP_TOOL_CALLS_TOTAL = Counter(
    "mcp_tool_calls_total",
    "Total MCP tool calls",
    ["server_name", "tool_name", "status", "request_id"],
)

MCP_TOOL_DURATION = Histogram(
    "mcp_tool_duration_seconds",
    "MCP tool execution duration",
    ["server_name", "tool_name", "request_id"],
    buckets=MCP_DURATION_BUCKETS,
)


def record_mcp_connection(
    server_name: str,
    status: str,
    duration: float,
    request_id: str = "",
) -> None:
    """Record an MCP server connection attempt.

    Args:
        server_name: Name of the MCP server
        status: Connection status (success, error)
        duration: Connection time in seconds
        request_id: Unique request identifier
    """
    MCP_CONNECTIONS_TOTAL.labels(
        server_name=server_name,
        status=status,
        request_id=request_id,
    ).inc()

    MCP_CONNECTION_DURATION.labels(
        server_name=server_name,
        request_id=request_id,
    ).observe(duration)


def record_mcp_tool_call(
    server_name: str,
    tool_name: str,
    status: str,
    duration: float,
    request_id: str = "",
) -> None:
    """Record an MCP tool call.

    Args:
        server_name: Name of the MCP server
        tool_name: Name of the tool called
        status: Call status (success, error)
        duration: Execution time in seconds
        request_id: Unique request identifier
    """
    MCP_TOOL_CALLS_TOTAL.labels(
        server_name=server_name,
        tool_name=tool_name,
        status=status,
        request_id=request_id,
    ).inc()

    MCP_TOOL_DURATION.labels(
        server_name=server_name,
        tool_name=tool_name,
        request_id=request_id,
    ).observe(duration)


@contextmanager
def track_mcp_connection(
    server_name: str,
    request_id: str = "",
) -> Generator[None, None, None]:
    """Context manager to track MCP connection metrics.

    Args:
        server_name: Name of the MCP server
        request_id: Unique request identifier

    Yields:
        None

    Example:
        with track_mcp_connection("filesystem-server", request_id):
            await connect_to_server()
    """
    start_time = time.perf_counter()
    status = "success"
    try:
        yield
    except Exception:
        status = "error"
        raise
    finally:
        duration = time.perf_counter() - start_time
        record_mcp_connection(server_name, status, duration, request_id)


@contextmanager
def track_mcp_tool_call(
    server_name: str,
    tool_name: str,
    request_id: str = "",
) -> Generator[None, None, None]:
    """Context manager to track MCP tool call metrics.

    Args:
        server_name: Name of the MCP server
        tool_name: Name of the tool being called
        request_id: Unique request identifier

    Yields:
        None

    Example:
        with track_mcp_tool_call("filesystem-server", "read_file", request_id):
            result = await call_tool()
    """
    start_time = time.perf_counter()
    status = "success"
    try:
        yield
    except Exception:
        status = "error"
        raise
    finally:
        duration = time.perf_counter() - start_time
        record_mcp_tool_call(server_name, tool_name, status, duration, request_id)
