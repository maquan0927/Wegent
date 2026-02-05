# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

"""Skill Prometheus metrics for Chat Shell.

This module provides metrics for monitoring Skill operations:
- Skill loading attempts and status
- Skill load duration
- Skill tool call counts and status
- Skill tool execution duration

All metrics include request_id for tracing correlation.
"""

import time
from contextlib import contextmanager
from typing import Generator

from prometheus_client import Counter, Histogram

# Histogram buckets for Skill operations (starting from 0.1s)
SKILL_DURATION_BUCKETS = (
    0.1,
    0.25,
    0.5,
    1.0,
    2.5,
    5.0,
    10.0,
    30.0,
)

# Skill loading metrics
SKILL_LOADS_TOTAL = Counter(
    "skill_loads_total",
    "Total Skill loading attempts",
    ["skill_name", "status", "request_id"],
)

SKILL_LOAD_DURATION = Histogram(
    "skill_load_duration_seconds",
    "Skill loading duration",
    ["skill_name", "request_id"],
    buckets=SKILL_DURATION_BUCKETS,
)

# Skill tool call metrics
SKILL_TOOL_CALLS_TOTAL = Counter(
    "skill_tool_calls_total",
    "Total Skill tool calls",
    ["skill_name", "tool_name", "status", "request_id"],
)

SKILL_TOOL_DURATION = Histogram(
    "skill_tool_duration_seconds",
    "Skill tool execution duration",
    ["skill_name", "tool_name", "request_id"],
    buckets=SKILL_DURATION_BUCKETS,
)


def record_skill_load(
    skill_name: str,
    status: str,
    duration: float,
    request_id: str = "",
) -> None:
    """Record a Skill loading attempt.

    Args:
        skill_name: Name of the Skill
        status: Load status (success, error)
        duration: Load time in seconds
        request_id: Unique request identifier
    """
    SKILL_LOADS_TOTAL.labels(
        skill_name=skill_name,
        status=status,
        request_id=request_id,
    ).inc()

    SKILL_LOAD_DURATION.labels(
        skill_name=skill_name,
        request_id=request_id,
    ).observe(duration)


def record_skill_tool_call(
    skill_name: str,
    tool_name: str,
    status: str,
    duration: float,
    request_id: str = "",
) -> None:
    """Record a Skill tool call.

    Args:
        skill_name: Name of the Skill
        tool_name: Name of the tool called
        status: Call status (success, error)
        duration: Execution time in seconds
        request_id: Unique request identifier
    """
    SKILL_TOOL_CALLS_TOTAL.labels(
        skill_name=skill_name,
        tool_name=tool_name,
        status=status,
        request_id=request_id,
    ).inc()

    SKILL_TOOL_DURATION.labels(
        skill_name=skill_name,
        tool_name=tool_name,
        request_id=request_id,
    ).observe(duration)


@contextmanager
def track_skill_load(
    skill_name: str,
    request_id: str = "",
) -> Generator[None, None, None]:
    """Context manager to track Skill load metrics.

    Args:
        skill_name: Name of the Skill
        request_id: Unique request identifier

    Yields:
        None

    Example:
        with track_skill_load("code-review", request_id):
            skill = await load_skill()
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
        record_skill_load(skill_name, status, duration, request_id)


@contextmanager
def track_skill_tool_call(
    skill_name: str,
    tool_name: str,
    request_id: str = "",
) -> Generator[None, None, None]:
    """Context manager to track Skill tool call metrics.

    Args:
        skill_name: Name of the Skill
        tool_name: Name of the tool being called
        request_id: Unique request identifier

    Yields:
        None

    Example:
        with track_skill_tool_call("code-review", "analyze_code", request_id):
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
        record_skill_tool_call(skill_name, tool_name, status, duration, request_id)
