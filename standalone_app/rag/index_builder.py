from __future__ import annotations

from collections import Counter
from datetime import datetime

from .extractors import extract_all_chunks
from .storage import RAG_MANIFEST_PATH, save_chunks, write_json


def build_rag_index() -> dict[str, object]:
    chunks = extract_all_chunks()
    save_chunks(chunks)

    by_source_kind = Counter(chunk.source_kind for chunk in chunks)
    by_module = Counter(chunk.module for chunk in chunks)
    manifest: dict[str, object] = {
        "built_at": datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "chunk_count": len(chunks),
        "source_kind_counts": dict(by_source_kind),
        "module_counts": dict(by_module),
        "manifest_path": str(RAG_MANIFEST_PATH),
    }
    write_json(RAG_MANIFEST_PATH, manifest)
    return manifest
