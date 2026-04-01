from __future__ import annotations

from datetime import datetime
from typing import Any

from .schema import RagChunk, RetrievalResult
from .storage import load_chunks, load_rag_config


LAYER_SOURCE_KINDS = {
    "rules_rag": {"rule", "memory", "learning_packet"},
    "style_rag": {"crawler", "local_exam"},
    "type_rag": {"question"},
}


class RagRetriever:
    def __init__(self, chunks: list[RagChunk] | None = None, config: dict[str, Any] | None = None) -> None:
        self.chunks = chunks if chunks is not None else load_chunks()
        self.config = config if config is not None else load_rag_config()

    def retrieve(
        self,
        *,
        module: str | None = None,
        question_type: str | None = None,
        layer: str,
        top_k: int = 5,
        generation_mode: str = "creative",
    ) -> list[RetrievalResult]:
        allowed_kinds = LAYER_SOURCE_KINDS.get(layer, set())
        anti_copy_threshold = float(self.config.get("anti_copy", {}).get("creative_max_risk", 0.8))
        source_weights = self.config.get("source_weights", {})

        results: list[RetrievalResult] = []
        for chunk in self.chunks:
            if allowed_kinds and chunk.source_kind not in allowed_kinds:
                continue
            if not chunk.usable_for_generation:
                continue
            if module and chunk.module not in {module, "综合"}:
                continue
            if question_type and chunk.question_type not in {question_type, module or "", "未分类"}:
                if layer == "type_rag":
                    continue
            if generation_mode == "creative" and chunk.anti_copy_risk > anti_copy_threshold:
                continue

            score = 0.0
            reasons: list[str] = []

            if module and chunk.module == module:
                score += 4.0
                reasons.append("module_match")
            elif chunk.module == "综合":
                score += 1.0
                reasons.append("module_fallback")

            if question_type and chunk.question_type == question_type:
                score += 3.0
                reasons.append("type_match")

            score += float(source_weights.get(chunk.source_kind, 1.0))
            reasons.append(f"source_kind:{chunk.source_kind}")

            if chunk.source_domain:
                score += float(source_weights.get(chunk.source_domain, 0.0))

            if chunk.source_kind == "crawler":
                score += self._crawler_recency_bonus(chunk.metadata)
                if chunk.metadata.get("fetch_count"):
                    score += min(float(chunk.metadata.get("fetch_count", 0)) * 0.05, 0.5)

            score -= chunk.anti_copy_risk
            results.append(RetrievalResult(chunk=chunk, score=score, reasons=reasons))

        results.sort(key=lambda item: item.score, reverse=True)
        return results[:top_k]

    @staticmethod
    def _crawler_recency_bonus(metadata: dict[str, Any]) -> float:
        raw = str(
            metadata.get("last_seen_at")
            or metadata.get("fetched_at")
            or metadata.get("published_at")
            or ""
        ).strip()
        if not raw:
            return 0.0
        parsed = None
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError:
            for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
                try:
                    parsed = datetime.strptime(raw, fmt)
                    break
                except ValueError:
                    continue
        if parsed is None:
            return 0.0
        now = datetime.now(parsed.tzinfo) if parsed.tzinfo else datetime.now()
        age_days = max((now - parsed).days, 0)
        if age_days <= 14:
            return 1.6
        if age_days <= 45:
            return 0.9
        if age_days <= 120:
            return 0.4
        return 0.0
