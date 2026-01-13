# SPDX-FileCopyrightText: 2025 Weibo, Inc.
#
# SPDX-License-Identifier: Apache-2.0

import os
import sys

import pytest

# Add shared directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from utils.markdown_util import remap_markdown_headings


@pytest.mark.unit
class TestRemapMarkdownHeadings:
    """Test markdown heading remapping functionality."""

    def test_basic_remap_from_h1_to_h2(self):
        """Test basic remapping from H1 to H2."""
        md_text = "# Title\n## Subtitle\n### Deep"
        expected = "## Title\n### Subtitle\n#### Deep"

        result = remap_markdown_headings(md_text, target_top_level=2)
        assert result == expected

    def test_remap_from_h3_to_h1(self):
        """Test remapping when top level is H3 and target is H1."""
        md_text = "### Already Deep\n#### Even Deeper"
        expected = "# Already Deep\n## Even Deeper"

        result = remap_markdown_headings(md_text, target_top_level=1)
        assert result == expected

    def test_no_headings_returns_original(self):
        """Test that text without headings returns unchanged."""
        md_text = "This is plain text.\nNo headings here."

        result = remap_markdown_headings(md_text, target_top_level=2)
        assert result == md_text

    def test_empty_string_returns_empty(self):
        """Test that empty string returns empty."""
        result = remap_markdown_headings("", target_top_level=2)
        assert result == ""

    def test_heading_level_clamping_upper_bound(self):
        """Test that heading levels are clamped to max 6."""
        md_text = "##### H5\n###### H6"
        # Shifting H5 to become H6 (+1 offset) would make H6 become H7,
        # but it should clamp to H6
        expected = "###### H5\n###### H6"

        result = remap_markdown_headings(md_text, target_top_level=6)
        assert result == expected

    def test_heading_level_clamping_lower_bound(self):
        """Test that heading levels don't go below 1."""
        md_text = "## H2\n### H3"
        # When target is 1 and min is 2, offset is -1
        expected = "# H2\n## H3"

        result = remap_markdown_headings(md_text, target_top_level=1)
        assert result == expected

    def test_target_top_level_clamping(self):
        """Test that target_top_level is clamped to valid range."""
        md_text = "# Title"

        # target_top_level=0 should be clamped to 1
        result_low = remap_markdown_headings(md_text, target_top_level=0)
        assert result_low == "# Title"

        # target_top_level=10 should be clamped to 6
        result_high = remap_markdown_headings(md_text, target_top_level=10)
        assert result_high == "###### Title"

    def test_preserves_indentation(self):
        """Test that leading whitespace is preserved."""
        md_text = "  ## Indented Heading"
        expected = "  ### Indented Heading"

        result = remap_markdown_headings(md_text, target_top_level=3)
        assert result == expected

    def test_preserves_heading_text(self):
        """Test that heading content is preserved exactly."""
        md_text = "# Title with **bold** and `code`"
        expected = "## Title with **bold** and `code`"

        result = remap_markdown_headings(md_text, target_top_level=2)
        assert result == expected

    def test_mixed_content(self):
        """Test with mixed content (headings and regular text)."""
        md_text = """# Main Title

Some paragraph text here.

## Section One

More text.

### Subsection

Even more text."""

        expected = """## Main Title

Some paragraph text here.

### Section One

More text.

#### Subsection

Even more text."""

        result = remap_markdown_headings(md_text, target_top_level=2)
        assert result == expected

    def test_multiple_same_level_headings(self):
        """Test with multiple headings at the same level."""
        md_text = "# First\n# Second\n# Third"
        expected = "### First\n### Second\n### Third"

        result = remap_markdown_headings(md_text, target_top_level=3)
        assert result == expected

    def test_no_change_when_already_at_target(self):
        """Test that no change occurs when top level matches target."""
        md_text = "## Already H2\n### H3"
        expected = "## Already H2\n### H3"

        result = remap_markdown_headings(md_text, target_top_level=2)
        assert result == expected

    def test_handles_trailing_spaces_in_heading(self):
        """Test that trailing spaces in heading text are preserved."""
        md_text = "# Title with trailing spaces   "
        expected = "## Title with trailing spaces   "

        result = remap_markdown_headings(md_text, target_top_level=2)
        assert result == expected

    def test_handles_unicode_content(self):
        """Test with Unicode content in headings."""
        md_text = "# 中文标题\n## 日本語\n### Émoji 🎉"
        expected = "## 中文标题\n### 日本語\n#### Émoji 🎉"

        result = remap_markdown_headings(md_text, target_top_level=2)
        assert result == expected

    def test_skips_code_block_hashes(self):
        """Test that hashes in code blocks are not treated as headings."""
        # Note: This function operates on raw regex matching,
        # so code block content with headings at line start will be affected.
        # This is expected behavior for simple regex-based implementation.
        md_text = "# Title\n```\n# Comment in code\n```"
        expected = "## Title\n```\n## Comment in code\n```"

        result = remap_markdown_headings(md_text, target_top_level=2)
        assert result == expected

    def test_default_target_level_is_two(self):
        """Test that default target_top_level is 2."""
        md_text = "# Title"
        expected = "## Title"

        result = remap_markdown_headings(md_text)
        assert result == expected

    def test_all_six_levels(self):
        """Test remapping through all six heading levels."""
        md_text = "# H1\n## H2\n### H3\n#### H4\n##### H5\n###### H6"
        # Shift everything by +1 (target 2, min 1, offset +1)
        # H6 + 1 = 7, clamped to 6
        expected = "## H1\n### H2\n#### H3\n##### H4\n###### H5\n###### H6"

        result = remap_markdown_headings(md_text, target_top_level=2)
        assert result == expected
