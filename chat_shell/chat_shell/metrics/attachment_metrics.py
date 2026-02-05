# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

"""Attachment Prometheus metrics for Chat Shell.

This module provides metrics for monitoring attachment processing:
- Attachment download counts and status
- Attachment download duration
- Attachment parse counts and status
- Attachment parse duration

All metrics include request_id for tracing correlation.
"""

import time
from contextlib import contextmanager
from typing import Generator

from prometheus_client import Counter, Histogram

# Histogram buckets for attachment operations (starting from 0.1s)
ATTACHMENT_DURATION_BUCKETS = (
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

# Download metrics
ATTACHMENT_DOWNLOADS_TOTAL = Counter(
    "attachment_downloads_total",
    "Total attachment download attempts",
    ["file_type", "status", "request_id"],
)

ATTACHMENT_DOWNLOAD_DURATION = Histogram(
    "attachment_download_duration_seconds",
    "Attachment download duration",
    ["file_type", "request_id"],
    buckets=ATTACHMENT_DURATION_BUCKETS,
)

# Parse metrics
ATTACHMENT_PARSE_TOTAL = Counter(
    "attachment_parse_total",
    "Total attachment parse attempts",
    ["file_type", "status", "request_id"],
)

ATTACHMENT_PARSE_DURATION = Histogram(
    "attachment_parse_duration_seconds",
    "Attachment parse duration",
    ["file_type", "request_id"],
    buckets=ATTACHMENT_DURATION_BUCKETS,
)


def record_attachment_download(
    file_type: str,
    status: str,
    duration: float,
    request_id: str = "",
) -> None:
    """Record an attachment download attempt.

    Args:
        file_type: Type of file (pdf, docx, xlsx, etc.)
        status: Download status (success, error)
        duration: Download time in seconds
        request_id: Unique request identifier
    """
    ATTACHMENT_DOWNLOADS_TOTAL.labels(
        file_type=file_type,
        status=status,
        request_id=request_id,
    ).inc()

    ATTACHMENT_DOWNLOAD_DURATION.labels(
        file_type=file_type,
        request_id=request_id,
    ).observe(duration)


def record_attachment_parse(
    file_type: str,
    status: str,
    duration: float,
    request_id: str = "",
) -> None:
    """Record an attachment parse attempt.

    Args:
        file_type: Type of file (pdf, docx, xlsx, etc.)
        status: Parse status (success, error)
        duration: Parse time in seconds
        request_id: Unique request identifier
    """
    ATTACHMENT_PARSE_TOTAL.labels(
        file_type=file_type,
        status=status,
        request_id=request_id,
    ).inc()

    ATTACHMENT_PARSE_DURATION.labels(
        file_type=file_type,
        request_id=request_id,
    ).observe(duration)


@contextmanager
def track_attachment_download(
    file_type: str,
    request_id: str = "",
) -> Generator[None, None, None]:
    """Context manager to track attachment download metrics.

    Args:
        file_type: Type of file being downloaded
        request_id: Unique request identifier

    Yields:
        None

    Example:
        with track_attachment_download("pdf", request_id):
            content = await download_file()
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
        record_attachment_download(file_type, status, duration, request_id)


@contextmanager
def track_attachment_parse(
    file_type: str,
    request_id: str = "",
) -> Generator[None, None, None]:
    """Context manager to track attachment parse metrics.

    Args:
        file_type: Type of file being parsed
        request_id: Unique request identifier

    Yields:
        None

    Example:
        with track_attachment_parse("pdf", request_id):
            text = await parse_file()
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
        record_attachment_parse(file_type, status, duration, request_id)
