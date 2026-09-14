"""Text chunking service for slicing documents into retrieval chunks."""

from __future__ import annotations

from collections.abc import Sequence

from aegis.domain.models.rag import Document, DocumentChunk


class TextChunker:
    """Chunks documents into overlapping segments with exact character offsets."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50) -> None:
        if chunk_size <= 0:
            raise ValueError(f"chunk_size must be positive, got {chunk_size}")
        if chunk_overlap < 0:
            raise ValueError(f"chunk_overlap cannot be negative, got {chunk_overlap}")
        if chunk_overlap >= chunk_size:
            raise ValueError(
                f"chunk_overlap ({chunk_overlap}) must be strictly less than "
                f"chunk_size ({chunk_size})"
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, document: Document) -> list[DocumentChunk]:
        """Split a single Document into a sequence of DocumentChunk instances."""
        text = document.content
        text_len = len(text)

        if text_len <= self.chunk_size:
            return [
                DocumentChunk(
                    chunk_id=f"{document.id}#c0",
                    document_id=document.id,
                    content=text,
                    chunk_index=0,
                    start_char=0,
                    end_char=text_len,
                    metadata=dict(document.metadata),
                )
            ]

        chunks: list[DocumentChunk] = []
        step = self.chunk_size - self.chunk_overlap
        start = 0
        chunk_idx = 0

        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            segment = text[start:end].strip()

            if segment:
                chunk_meta = dict(document.metadata)
                chunk_meta["chunk_index"] = chunk_idx
                chunk_meta["char_length"] = len(segment)

                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{document.id}#c{chunk_idx}",
                        document_id=document.id,
                        content=segment,
                        chunk_index=chunk_idx,
                        start_char=start,
                        end_char=end,
                        metadata=chunk_meta,
                    )
                )
                chunk_idx += 1

            if end >= text_len:
                break
            start += step

        return chunks

    def chunk_documents(self, documents: Sequence[Document]) -> list[DocumentChunk]:
        """Split multiple documents into a flat list of DocumentChunks."""
        all_chunks: list[DocumentChunk] = []
        for doc in documents:
            all_chunks.extend(self.chunk_document(doc))
        return all_chunks
