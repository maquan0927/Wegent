# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

"""Prometheus registry management.

Provides a centralized registry for all Prometheus metrics.
Supports both single-process and multi-process modes.
"""

import os
from typing import Optional

from prometheus_client import CollectorRegistry, multiprocess

# Global registry instance
_registry: Optional[CollectorRegistry] = None


def get_registry() -> CollectorRegistry:
    """Get the global Prometheus registry.

    In multi-process mode (when prometheus_multiproc_dir is set),
    uses the multiprocess collector. Otherwise, uses a standard registry.

    Returns:
        CollectorRegistry instance for metrics collection.
    """
    global _registry
    if _registry is None:
        # Check for multi-process mode
        prometheus_multiproc_dir = os.getenv("prometheus_multiproc_dir")
        if prometheus_multiproc_dir:
            # Multi-process mode: use multiprocess collector
            _registry = CollectorRegistry()
            multiprocess.MultiProcessCollector(_registry)
        else:
            # Single-process mode: use standard registry
            _registry = CollectorRegistry(auto_describe=True)

    return _registry


def reset_registry() -> None:
    """Reset the global registry (for testing)."""
    global _registry
    _registry = None
