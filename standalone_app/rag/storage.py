from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schema import RagChunk


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
STATE_DIR = ROOT / "state"
RAG_CORPUS_PATH = DATA_DIR / "rag_corpus.jsonl"
RAG_MANIFEST_PATH = STATE_DIR / "rag_manifest.json"
RAG_CONFIG_PATH = STATE_DIR / "rag_config.json"


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_rag_config() -> dict[str, Any]:
    return read_json(RAG_CONFIG_PATH, {})


def save_chunks(chunks: list[RagChunk]) -> None:
    RAG_CORPUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RAG_CORPUS_PATH.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk.to_dict(), ensure_ascii=False) + "\n")


def load_chunks() -> list[RagChunk]:
    if not RAG_CORPUS_PATH.exists():
        return []
    rows: list[RagChunk] = []
    with RAG_CORPUS_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(RagChunk.from_dict(json.loads(line)))
    return rows
