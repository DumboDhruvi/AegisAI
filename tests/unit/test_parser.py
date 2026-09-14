"""Unit tests for DocumentParser service."""

from __future__ import annotations

from pathlib import Path

import pytest

from aegis.services.parser import DocumentParser


def test_parse_raw_text() -> None:
    """Ensure raw text is parsed into a Document with metadata."""
    doc = DocumentParser.parse_raw_text(
        text="This is sample text.",
        document_id="doc-1",
        metadata={"author": "Alice"},
    )
    assert doc.id == "doc-1"
    assert doc.content == "This is sample text."
    assert doc.metadata["author"] == "Alice"
    assert doc.metadata["content_type"] == "text/plain"
    assert doc.metadata["char_count"] == len("This is sample text.")


def test_parse_markdown_extracts_title() -> None:
    """Ensure markdown parser extracts title from top-level header."""
    markdown_content = """# Company Refund Policy
Here are the refund rules.
"""
    doc = DocumentParser.parse_markdown(markdown_content, document_id="policy-doc")
    assert doc.id == "policy-doc"
    assert doc.metadata["title"] == "Company Refund Policy"
    assert doc.metadata["content_type"] == "text/markdown"


def test_parse_empty_content_raises_error() -> None:
    """Ensure whitespace-only content raises ValueError."""
    with pytest.raises(ValueError, match="cannot be empty"):
        DocumentParser.parse_raw_text("   ", document_id="empty-doc")


def test_parse_file(tmp_path: Path) -> None:
    """Ensure file parsing reads text and detects markdown extension."""
    md_file = tmp_path / "guide.md"
    md_file.write_text("# Getting Started\nWelcome to AegisAI.", encoding="utf-8")

    doc = DocumentParser.parse_file(md_file)
    assert doc.id == "guide"
    assert doc.metadata["file_name"] == "guide.md"
    assert doc.metadata["file_extension"] == ".md"
    assert doc.metadata["title"] == "Getting Started"
    assert "Welcome to AegisAI." in doc.content


def test_parse_file_not_found() -> None:
    """Ensure FileNotFoundError is raised for missing files."""
    with pytest.raises(FileNotFoundError):
        DocumentParser.parse_file("non_existent_file.txt")
