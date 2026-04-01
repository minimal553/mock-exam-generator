from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable

from .extractors import (
    MODULE_ALIASES,
    canonicalize_module,
    canonicalize_question_type,
    normalize_retrieval_text,
)
from .retriever import RagRetriever
from .schema import RetrievalResult
from .storage import load_rag_config


def _pick_focus_modules(focus: str | None) -> list[str]:
    text = normalize_retrieval_text(focus or "")
    if not text:
        return ["言语理解与表达", "判断推理", "资料分析"]

    matches: list[str] = []
    for canonical, aliases in MODULE_ALIASES.items():
        probes = [canonical, *aliases]
        if any(normalize_retrieval_text(item) in text for item in probes if normalize_retrieval_text(item)):
            if canonical not in matches:
                matches.append(canonical)
    return matches or ["言语理解与表达", "判断推理", "资料分析"]


def _format_results(title: str, results: Iterable[RetrievalResult], max_items: int = 5) -> str:
    lines = [f"### {title}"]
    kept = 0
    for result in results:
        lines.append(
            f"- [{result.chunk.source_kind}] 模块={result.chunk.module} "
            f"题型={result.chunk.question_type} 来源={result.chunk.source_domain} "
            f"分数={result.score:.2f} 内容={result.chunk.content[:180]}"
        )
        kept += 1
        if kept >= max_items:
            break
    if kept == 0:
        lines.append("- 暂无命中")
    return "\n".join(lines)


def _result_is_recent_crawler(result: RetrievalResult, *, hours: int = 72) -> bool:
    chunk = result.chunk
    if chunk.source_kind != "crawler":
        return False
    raw = str(
        chunk.metadata.get("last_seen_at")
        or chunk.metadata.get("fetched_at")
        or chunk.metadata.get("published_at")
        or ""
    ).strip()
    if not raw:
        return False
    parsed: datetime | None = None
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
        return False
    now = datetime.now(parsed.tzinfo) if parsed.tzinfo else datetime.now()
    return parsed >= (now - timedelta(hours=hours))


def build_question_bundle(
    module: str,
    question_type: str | None = None,
    retriever: RagRetriever | None = None,
) -> str:
    retriever = retriever or RagRetriever()
    config = load_rag_config()
    canonical_module = canonicalize_module(module)
    canonical_type = canonicalize_question_type(question_type or "", canonical_module)

    rules = retriever.retrieve(
        module=canonical_module,
        question_type=canonical_type,
        layer="rules_rag",
        top_k=int(config.get("rules_rag", {}).get("top_k", 5)),
    )
    style_top_k = int(config.get("style_rag", {}).get("top_k", 4))
    data_module = canonicalize_module("资料分析")
    style_pool_k = style_top_k + 6 if canonical_module == data_module else style_top_k
    style_pool = retriever.retrieve(
        module=canonical_module,
        question_type=canonical_type,
        layer="style_rag",
        top_k=style_pool_k,
    )
    styles = style_pool[:style_top_k]
    recent_styles = [result for result in style_pool if _result_is_recent_crawler(result)]
    types = retriever.retrieve(
        module=canonical_module,
        question_type=canonical_type,
        layer="type_rag",
        top_k=int(config.get("type_rag", {}).get("top_k", 3)),
        generation_mode="creative",
    )

    blocks = [
        f"## RAG 题目上下文\n- 目标模块: {canonical_module}\n- 目标题型: {canonical_type}",
        _format_results("规则约束", rules),
        _format_results("风格参考", styles),
    ]
    if recent_styles:
        blocks.append(_format_results("近期抓取素材（72h）", recent_styles, max_items=4))
    blocks.append(_format_results("题型骨架", types))
    return "\n\n".join(blocks)


def build_learning_bundle(focus: str | None, retriever: RagRetriever | None = None) -> str:
    retriever = retriever or RagRetriever()
    config = load_rag_config()
    modules = _pick_focus_modules(focus)

    rules = retriever.retrieve(
        module="综合",
        layer="rules_rag",
        top_k=int(config.get("rules_rag", {}).get("top_k", 5)),
    )
    style_hits: list[RetrievalResult] = []
    for module in modules:
        style_hits.extend(
            retriever.retrieve(
                module=module,
                layer="style_rag",
                top_k=2,
            )
        )

    return "\n\n".join(
        [
            "## RAG 学习上下文",
            f"- 本轮聚焦模块: {', '.join(modules)}",
            _format_results("规则约束", rules),
            _format_results("风格参考", style_hits, max_items=6),
        ]
    )


def build_paper_planning_bundle(
    section_blueprint: list[dict],
    retriever: RagRetriever | None = None,
) -> str:
    retriever = retriever or RagRetriever()
    config = load_rag_config()
    modules: list[str] = []
    for item in section_blueprint:
        canonical = canonicalize_module(str(item.get("name", "")))
        if canonical not in modules:
            modules.append(canonical)

    rules = retriever.retrieve(
        module="综合",
        layer="rules_rag",
        top_k=int(config.get("rules_rag", {}).get("top_k", 5)),
    )
    style_hits: list[RetrievalResult] = []
    type_hits: list[RetrievalResult] = []
    for module in modules:
        style_hits.extend(retriever.retrieve(module=module, layer="style_rag", top_k=1))
        type_hits.extend(
            retriever.retrieve(
                module=module,
                layer="type_rag",
                top_k=1,
                generation_mode="creative",
            )
        )

    return "\n\n".join(
        [
            "## RAG 整卷规划上下文",
            f"- 覆盖模块: {', '.join(modules)}",
            _format_results("规则约束", rules),
            _format_results("风格参考", style_hits, max_items=8),
            _format_results("题型骨架", type_hits, max_items=8),
        ]
    )
