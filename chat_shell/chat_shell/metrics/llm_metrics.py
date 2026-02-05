# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

"""LLM Prometheus metrics for Chat Shell.

This module provides metrics for monitoring LLM calls including:
- Request counts by model and status
- Request duration (total latency)
- Token consumption (input/output)
- Time to First Token (TTFT) for streaming
- Tokens per second generation rate

All metrics include request_id for tracing correlation.
"""

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Generator, Optional

from prometheus_client import Counter, Histogram

# Histogram buckets for LLM request duration (can be longer than HTTP)
LLM_DURATION_BUCKETS = (
    0.1,
    0.5,
    1.0,
    2.0,
    5.0,
    10.0,
    30.0,
    60.0,
    120.0,
    300.0,
)

# Histogram buckets for Time to First Token
TTFT_BUCKETS = (
    0.1,
    0.25,
    0.5,
    1.0,
    2.0,
    5.0,
    10.0,
)

# Histogram buckets for tokens per second
TOKENS_PER_SECOND_BUCKETS = (
    1,
    5,
    10,
    20,
    50,
    100,
    200,
)

# LLM Request metrics
LLM_REQUESTS_TOTAL = Counter(
    "llm_requests_total",
    "Total number of LLM API requests",
    ["model_id", "provider", "status", "request_id"],
)

LLM_REQUEST_DURATION = Histogram(
    "llm_request_duration_seconds",
    "LLM request duration in seconds",
    ["model_id", "provider", "request_id"],
    buckets=LLM_DURATION_BUCKETS,
)

# Token metrics
LLM_TOKENS_TOTAL = Counter(
    "llm_tokens_total",
    "Total number of tokens consumed",
    ["model_id", "provider", "token_type", "request_id"],
)

# Streaming metrics
LLM_TIME_TO_FIRST_TOKEN = Histogram(
    "llm_time_to_first_token_seconds",
    "Time to receive first token in streaming response",
    ["model_id", "provider", "request_id"],
    buckets=TTFT_BUCKETS,
)

LLM_TOKENS_PER_SECOND = Histogram(
    "llm_tokens_per_second",
    "Token generation rate (tokens per second)",
    ["model_id", "provider", "request_id"],
    buckets=TOKENS_PER_SECOND_BUCKETS,
)


def record_llm_request(
    model_id: str,
    provider: str,
    status: str,
    duration: float,
    request_id: str = "",
) -> None:
    """Record an LLM request with its outcome.

    Args:
        model_id: Model identifier (e.g., gpt-4, claude-3-sonnet)
        provider: LLM provider (openai, anthropic, google)
        status: Request status (success, error)
        duration: Request duration in seconds
        request_id: Unique request identifier
    """
    LLM_REQUESTS_TOTAL.labels(
        model_id=model_id,
        provider=provider,
        status=status,
        request_id=request_id,
    ).inc()

    LLM_REQUEST_DURATION.labels(
        model_id=model_id,
        provider=provider,
        request_id=request_id,
    ).observe(duration)


def record_llm_tokens(
    model_id: str,
    provider: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    request_id: str = "",
) -> None:
    """Record token consumption for an LLM request.

    Args:
        model_id: Model identifier
        provider: LLM provider
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        request_id: Unique request identifier
    """
    if input_tokens > 0:
        LLM_TOKENS_TOTAL.labels(
            model_id=model_id,
            provider=provider,
            token_type="input",
            request_id=request_id,
        ).inc(input_tokens)

    if output_tokens > 0:
        LLM_TOKENS_TOTAL.labels(
            model_id=model_id,
            provider=provider,
            token_type="output",
            request_id=request_id,
        ).inc(output_tokens)


def record_ttft(
    model_id: str,
    provider: str,
    ttft: float,
    request_id: str = "",
) -> None:
    """Record Time to First Token.

    Args:
        model_id: Model identifier
        provider: LLM provider
        ttft: Time to first token in seconds
        request_id: Unique request identifier
    """
    LLM_TIME_TO_FIRST_TOKEN.labels(
        model_id=model_id,
        provider=provider,
        request_id=request_id,
    ).observe(ttft)


def record_tokens_per_second(
    model_id: str,
    provider: str,
    tps: float,
    request_id: str = "",
) -> None:
    """Record tokens per second generation rate.

    Args:
        model_id: Model identifier
        provider: LLM provider
        tps: Tokens per second
        request_id: Unique request identifier
    """
    if tps > 0:
        LLM_TOKENS_PER_SECOND.labels(
            model_id=model_id,
            provider=provider,
            request_id=request_id,
        ).observe(tps)


@dataclass
class LLMMetricsContext:
    """Context manager for tracking LLM metrics during streaming.

    This class helps track TTFT, total duration, and token counts
    during streaming LLM responses.

    Usage:
        ctx = LLMMetricsContext(model_id="gpt-4", provider="openai", request_id="abc123")
        ctx.start()

        async for token in stream:
            ctx.on_token()
            yield token

        ctx.finish(status="success")
    """

    model_id: str
    provider: str
    request_id: str = ""
    start_time: float = field(default=0.0, init=False)
    first_token_time: Optional[float] = field(default=None, init=False)
    token_count: int = field(default=0, init=False)
    _finished: bool = field(default=False, init=False)

    def start(self) -> None:
        """Start timing the LLM request."""
        self.start_time = time.perf_counter()

    def on_token(self) -> None:
        """Record a token received during streaming."""
        if self.first_token_time is None:
            self.first_token_time = time.perf_counter()
        self.token_count += 1

    def finish(self, status: str = "success", input_tokens: int = 0) -> None:
        """Finish tracking and record all metrics.

        Args:
            status: Request status (success, error)
            input_tokens: Number of input tokens (if available)
        """
        if self._finished:
            return
        self._finished = True

        end_time = time.perf_counter()
        duration = end_time - self.start_time

        # Record request metrics
        record_llm_request(
            model_id=self.model_id,
            provider=self.provider,
            status=status,
            duration=duration,
            request_id=self.request_id,
        )

        # Record TTFT if we got any tokens
        if self.first_token_time is not None:
            ttft = self.first_token_time - self.start_time
            record_ttft(
                model_id=self.model_id,
                provider=self.provider,
                ttft=ttft,
                request_id=self.request_id,
            )

        # Record tokens per second if we got tokens
        if self.token_count > 0 and duration > 0:
            tps = self.token_count / duration
            record_tokens_per_second(
                model_id=self.model_id,
                provider=self.provider,
                tps=tps,
                request_id=self.request_id,
            )

        # Record token counts
        record_llm_tokens(
            model_id=self.model_id,
            provider=self.provider,
            input_tokens=input_tokens,
            output_tokens=self.token_count,
            request_id=self.request_id,
        )


@contextmanager
def track_llm_request(
    model_id: str,
    provider: str,
    request_id: str = "",
) -> Generator[LLMMetricsContext, None, None]:
    """Context manager for tracking LLM request metrics.

    Args:
        model_id: Model identifier
        provider: LLM provider
        request_id: Unique request identifier

    Yields:
        LLMMetricsContext for tracking streaming metrics

    Example:
        with track_llm_request("gpt-4", "openai", "abc123") as ctx:
            ctx.start()
            async for token in stream:
                ctx.on_token()
                yield token
            ctx.finish("success")
    """
    ctx = LLMMetricsContext(
        model_id=model_id,
        provider=provider,
        request_id=request_id,
    )
    try:
        yield ctx
    except Exception:
        if not ctx._finished:
            ctx.finish(status="error")
        raise
