# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

"""
Unit tests for shared prompts module.

Tests that KB prompt constants are properly exported and accessible.
"""

import pytest


class TestKBPromptConstants:
    """Test KB prompt constant exports."""

    def test_kb_prompt_strict_importable(self):
        """Should be able to import KB_PROMPT_STRICT from shared.prompts."""
        from shared.prompts import KB_PROMPT_STRICT

        assert KB_PROMPT_STRICT is not None
        assert isinstance(KB_PROMPT_STRICT, str)
        assert len(KB_PROMPT_STRICT) > 0

    def test_kb_prompt_relaxed_importable(self):
        """Should be able to import KB_PROMPT_RELAXED from shared.prompts."""
        from shared.prompts import KB_PROMPT_RELAXED

        assert KB_PROMPT_RELAXED is not None
        assert isinstance(KB_PROMPT_RELAXED, str)
        assert len(KB_PROMPT_RELAXED) > 0

    def test_kb_prompt_strict_contains_required_content(self):
        """KB_PROMPT_STRICT should contain strict mode instructions."""
        from shared.prompts import KB_PROMPT_STRICT

        # Check for key phrases in strict mode
        assert "MUST use" in KB_PROMPT_STRICT
        assert "knowledge_base_search" in KB_PROMPT_STRICT
        assert "ONLY" in KB_PROMPT_STRICT or "only" in KB_PROMPT_STRICT

    def test_kb_prompt_relaxed_contains_required_content(self):
        """KB_PROMPT_RELAXED should contain relaxed mode instructions."""
        from shared.prompts import KB_PROMPT_RELAXED

        # Check for key phrases in relaxed mode
        assert "knowledge_base_search" in KB_PROMPT_RELAXED
        assert (
            "general knowledge" in KB_PROMPT_RELAXED or "fallback" in KB_PROMPT_RELAXED
        )

    def test_prompts_are_different(self):
        """Strict and relaxed prompts should be different."""
        from shared.prompts import KB_PROMPT_RELAXED, KB_PROMPT_STRICT

        assert KB_PROMPT_STRICT != KB_PROMPT_RELAXED

    def test_prompts_module_all_export(self):
        """shared.prompts module should export KB_PROMPT_STRICT and KB_PROMPT_RELAXED in __all__."""
        from shared import prompts

        assert hasattr(prompts, "__all__")
        assert "KB_PROMPT_STRICT" in prompts.__all__
        assert "KB_PROMPT_RELAXED" in prompts.__all__

    def test_kb_prompts_contain_format_placeholder(self):
        """KB prompts should contain {kb_meta_info} placeholder for formatting."""
        from shared.prompts import KB_PROMPT_RELAXED, KB_PROMPT_STRICT

        assert "{kb_meta_info}" in KB_PROMPT_STRICT
        assert "{kb_meta_info}" in KB_PROMPT_RELAXED

    def test_kb_prompts_format_with_meta_info(self):
        """KB prompts should correctly format with kb_meta_info inside the tags."""
        from shared.prompts import KB_PROMPT_RELAXED, KB_PROMPT_STRICT

        test_meta_info = "Available KBs: KB1, KB2"

        # Test strict prompt formatting
        formatted_strict = KB_PROMPT_STRICT.format(kb_meta_info=f"\n{test_meta_info}")
        # Meta info should be inside the closing tag
        assert test_meta_info in formatted_strict
        assert formatted_strict.find(test_meta_info) < formatted_strict.rfind(
            "</knowledge_base>"
        )

        # Test relaxed prompt formatting
        formatted_relaxed = KB_PROMPT_RELAXED.format(kb_meta_info=f"\n{test_meta_info}")
        # Meta info should be inside the closing tag
        assert test_meta_info in formatted_relaxed
        assert formatted_relaxed.find(test_meta_info) < formatted_relaxed.rfind(
            "</knowledge_base>"
        )

    def test_kb_prompts_format_with_empty_meta_info(self):
        """KB prompts should correctly format with empty kb_meta_info."""
        from shared.prompts import KB_PROMPT_RELAXED, KB_PROMPT_STRICT

        # Test strict prompt formatting with empty string
        formatted_strict = KB_PROMPT_STRICT.format(kb_meta_info="")
        assert "</knowledge_base>" in formatted_strict
        # Should not have extra newline before closing tag
        assert "{kb_meta_info}" not in formatted_strict

        # Test relaxed prompt formatting with empty string
        formatted_relaxed = KB_PROMPT_RELAXED.format(kb_meta_info="")
        assert "</knowledge_base>" in formatted_relaxed
        # Should not have placeholder remaining
        assert "{kb_meta_info}" not in formatted_relaxed
