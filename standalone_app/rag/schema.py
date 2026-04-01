from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class RagChunk:
    chunk_id: str
    source_path: str
    source_kind: str
    module: str
    question_type: str
    source_domain: str
    style_tags: list[str]
    difficulty_hint: str
    content: str
    normalized_content: str
    anti_copy_risk: float
    usable_for_generation: bool
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RagChunk":
        return cls(
            chunk_id=str(payload.get("chunk_id", "")),
            source_path=str(payload.get("source_path", "")),
            source_kind=str(payload.get("source_kind", "")),
            module=str(payload.get("module", "")),
            question_type=str(payload.get("question_type", "")),
            source_domain=str(payload.get("source_domain", "")),
            style_tags=[str(item) for item in payload.get("style_tags", [])],
            difficulty_hint=str(payload.get("difficulty_hint", "")),
            content=str(payload.get("content", "")),
            normalized_content=str(payload.get("normalized_content", "")),
            anti_copy_risk=float(payload.get("anti_copy_risk", 0.0)),
            usable_for_generation=bool(payload.get("usable_for_generation", False)),
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass(slots=True)
class RetrievalResult:
    chunk: RagChunk
    score: float
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["chunk"] = self.chunk.to_dict()
        return data
