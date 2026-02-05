# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

"""Prometheus metrics for Chat Shell module.

This package provides metrics for monitoring:
- LLM calls (requests, tokens, latency, TTFT)
- MCP server connections and tool calls
- Skill loading and tool execution
- Attachment processing
"""

from chat_shell.metrics.attachment_metrics import (
    ATTACHMENT_DOWNLOADS_TOTAL,
    ATTACHMENT_DOWNLOAD_DURATION,
    ATTACHMENT_PARSE_DURATION,
    ATTACHMENT_PARSE_TOTAL,
    record_attachment_download,
    record_attachment_parse,
)
from chat_shell.metrics.llm_metrics import (
    LLM_REQUESTS_TOTAL,
    LLM_REQUEST_DURATION,
    LLM_TIME_TO_FIRST_TOKEN,
    LLM_TOKENS_PER_SECOND,
    LLM_TOKENS_TOTAL,
    LLMMetricsContext,
    record_llm_request,
    record_llm_tokens,
)
from chat_shell.metrics.mcp_metrics import (
    MCP_CONNECTIONS_TOTAL,
    MCP_CONNECTION_DURATION,
    MCP_TOOL_CALLS_TOTAL,
    MCP_TOOL_DURATION,
    record_mcp_connection,
    record_mcp_tool_call,
)
from chat_shell.metrics.skill_metrics import (
    SKILL_LOADS_TOTAL,
    SKILL_LOAD_DURATION,
    SKILL_TOOL_CALLS_TOTAL,
    SKILL_TOOL_DURATION,
    record_skill_load,
    record_skill_tool_call,
)

__all__ = [
    # LLM metrics
    "LLM_REQUESTS_TOTAL",
    "LLM_REQUEST_DURATION",
    "LLM_TOKENS_TOTAL",
    "LLM_TIME_TO_FIRST_TOKEN",
    "LLM_TOKENS_PER_SECOND",
    "LLMMetricsContext",
    "record_llm_request",
    "record_llm_tokens",
    # MCP metrics
    "MCP_CONNECTIONS_TOTAL",
    "MCP_CONNECTION_DURATION",
    "MCP_TOOL_CALLS_TOTAL",
    "MCP_TOOL_DURATION",
    "record_mcp_connection",
    "record_mcp_tool_call",
    # Skill metrics
    "SKILL_LOADS_TOTAL",
    "SKILL_LOAD_DURATION",
    "SKILL_TOOL_CALLS_TOTAL",
    "SKILL_TOOL_DURATION",
    "record_skill_load",
    "record_skill_tool_call",
    # Attachment metrics
    "ATTACHMENT_DOWNLOADS_TOTAL",
    "ATTACHMENT_DOWNLOAD_DURATION",
    "ATTACHMENT_PARSE_TOTAL",
    "ATTACHMENT_PARSE_DURATION",
    "record_attachment_download",
    "record_attachment_parse",
]
