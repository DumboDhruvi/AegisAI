"""Document parsing service for extracting text and metadata from files and strings."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aegis.domain.models.rag import Document


class DocumentParser:
    """Parses raw text, markdown, and text files into standard Document models."""

    @classmethod
    def parse_raw_text(
        cls,
        text: str,
        document_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> Document:
        """Parse raw text into a Document."""
        cleaned_text = text.strip()
        if not cleaned_text:
            raise ValueError(f"Document content for ID '{document_id}' cannot be empty.")

        meta = dict(metadata or {})
        meta.setdefault("content_type", "text/plain")
        meta.setdefault("char_count", len(cleaned_text))

        return Document(
            id=document_id,
            content=cleaned_text,
            metadata=meta,
        )

    @classmethod
    def parse_markdown(
        cls,
        markdown_text: str,
        document_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> Document:
        """Parse markdown formatted text into a Document, extracting basic title if available."""
        cleaned = markdown_text.strip()
        if not cleaned:
            raise ValueError(f"Markdown content for ID '{document_id}' cannot be empty.")

        meta = dict(metadata or {})
        meta.setdefault("content_type", "text/markdown")
        meta.setdefault("char_count", len(cleaned))

        # Extract title from first top-level header if present
        for line in cleaned.splitlines():
            line_str = line.strip()
            if line_str.startswith("# ") and "title" not in meta:
                meta["title"] = line_str[2:].strip()
                break

        return Document(
            id=document_id,
            content=cleaned,
            metadata=meta,
        )

    @classmethod
    def parse_file(
        cls,
        file_path: str | Path,
        document_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Document:
        """Parse a local text or markdown file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Source document file not found: {path}")

        raw_content = path.read_text(encoding="utf-8")
        doc_id = document_id or path.stem

        meta = dict(metadata or {})
        meta.setdefault("source", str(path.resolve()))
        meta.setdefault("file_name", path.name)
        meta.setdefault("file_extension", path.suffix.lower())

        if path.suffix.lower() in [".md", ".markdown"]:
            return cls.parse_markdown(raw_content, document_id=doc_id, metadata=meta)
        return cls.parse_raw_text(raw_content, document_id=doc_id, metadata=meta)
