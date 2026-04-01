from __future__ import annotations

import hashlib
import json
import quopri
import re
import zipfile
from html import unescape
from pathlib import Path
from typing import Any

from .schema import RagChunk
from .storage import load_rag_config, read_json


ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = ROOT / "state"
DATA_DIR = ROOT / "data"

RULEBOOK_MD_PATH = STATE_DIR / "rulebook.md"
RULEBOOK_JSON_PATH = STATE_DIR / "locked_rulebook.json"
META_MEMORY_PATH = STATE_DIR / "meta_memory.json"
APPLIED_RULES_PATH = STATE_DIR / "applied_ability_a_meta_rules.md"
LEARNING_PACKET_PATH = STATE_DIR / "learning_packet.md"
QUESTIONS_PATH = DATA_DIR / "questions.jsonl"
WEB_MATERIALS_PATH = DATA_DIR / "web_materials.jsonl"


MODULE_ALIASES: dict[str, list[str]] = {
    "常识判断": ["常识判断", "常识"],
    "言语理解与表达": ["言语理解与表达", "言语", "逻辑填空", "片段阅读", "语句表达", "语句排序"],
    "判断推理": ["判断推理", "判断", "定义判断", "类比推理", "逻辑判断", "图形推理", "加强", "削弱", "翻译推理"],
    "资料分析": ["资料分析", "资料", "统计表", "文字资料", "增长率", "比重", "倍数", "平均数"],
    "数量关系": ["数量关系", "数量", "数学运算", "工程问题", "行程问题", "经济利润问题", "和差倍比"],
    "政治理论": ["政治理论", "时政", "政治"],
}

QUESTION_TYPE_ALIASES: dict[str, list[str]] = {
    "单选题": ["单选", "单选题"],
    "定义判断": ["定义判断", "定义"],
    "类比推理": ["类比推理", "类比"],
    "图形推理": ["图形推理", "图推", "看图推理"],
    "逻辑判断": ["逻辑判断", "加强", "削弱", "前提", "解释", "评价", "必然结论"],
    "逻辑填空": ["逻辑填空", "选词填空", "填空"],
    "片段阅读": ["片段阅读", "主旨", "标题", "细节", "排序", "衔接", "下文推断"],
    "资料分析": ["资料分析", "增长率", "比重", "平均数", "基期", "现期", "倍数"],
    "数量关系": ["数量关系", "工程", "数列", "年龄", "几何"],
    "常识判断": ["常识判断", "常识"],
    "政治理论": ["政治理论", "时政", "政治"],
}


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def normalize_retrieval_text(text: str) -> str:
    cleaned = normalize_ws(text)
    cleaned = cleaned.replace("\x00", "").replace("锟?", "")
    return cleaned


def stable_chunk_id(prefix: str, *parts: Any) -> str:
    digest = hashlib.sha1("|".join(str(part) for part in parts).encode("utf-8", "ignore")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def canonicalize_value(raw: str, alias_map: dict[str, list[str]], default: str) -> str:
    text = normalize_retrieval_text(raw)
    if not text:
        return default
    lowered = text.lower()
    for canonical, aliases in alias_map.items():
        probes = [canonical, *aliases]
        for alias in probes:
            probe = normalize_retrieval_text(alias)
            if not probe:
                continue
            if probe in text or probe.lower() in lowered:
                return canonical
    return default


def canonicalize_module(raw: str) -> str:
    return canonicalize_value(raw, MODULE_ALIASES, "综合")


def canonicalize_question_type(raw: str, fallback_module: str = "综合") -> str:
    question_type = canonicalize_value(raw, QUESTION_TYPE_ALIASES, "")
    if question_type:
        return question_type
    return fallback_module if fallback_module != "综合" else "未分类"


def estimate_difficulty(accuracy_pct: Any) -> str:
    try:
        value = float(accuracy_pct)
    except (TypeError, ValueError):
        return "unknown"
    if value >= 75:
        return "easy"
    if value >= 55:
        return "medium"
    return "hard"


def split_markdown_sections(text: str) -> list[tuple[str, str]]:
    lines = text.splitlines()
    sections: list[tuple[str, list[str]]] = []
    current_heading = "概览"
    current_lines: list[str] = []
    for line in lines:
        if line.startswith("#"):
            if current_lines:
                sections.append((current_heading, current_lines))
            current_heading = normalize_ws(line.lstrip("# ").strip()) or "概览"
            current_lines = []
            continue
        current_lines.append(line)
    if current_lines:
        sections.append((current_heading, current_lines))
    return [
        (heading, normalize_retrieval_text("\n".join(body)))
        for heading, body in sections
        if normalize_retrieval_text("\n".join(body))
    ]


def markdown_file_chunks(path: Path, source_kind: str, module: str = "综合") -> list[RagChunk]:
    if not path.exists():
        return []
    chunks: list[RagChunk] = []
    text = path.read_text(encoding="utf-8")
    for heading, body in split_markdown_sections(text):
        content = f"{heading}：{body}"
        normalized = normalize_retrieval_text(content)
        chunks.append(
            RagChunk(
                chunk_id=stable_chunk_id(source_kind, path.name, heading),
                source_path=str(path),
                source_kind=source_kind,
                module=module,
                question_type=heading,
                source_domain="local_state",
                style_tags=[path.stem],
                difficulty_hint="guide",
                content=content,
                normalized_content=normalized,
                anti_copy_risk=0.1,
                usable_for_generation=True,
                metadata={"heading": heading},
            )
        )
    return chunks


def extract_rule_chunks() -> list[RagChunk]:
    chunks: list[RagChunk] = []
    chunks.extend(markdown_file_chunks(RULEBOOK_MD_PATH, "rule", module="综合"))
    chunks.extend(markdown_file_chunks(APPLIED_RULES_PATH, "rule", module="综合"))

    rulebook = read_json(RULEBOOK_JSON_PATH, {})
    if rulebook:
        profile = rulebook.get("exam_profile", {})
        memory_effects = rulebook.get("memory_effects", {})
        for name, payload in {"exam_profile": profile, "memory_effects": memory_effects}.items():
            text = normalize_retrieval_text(json.dumps(payload, ensure_ascii=False))
            if not text:
                continue
            chunks.append(
                RagChunk(
                    chunk_id=stable_chunk_id("rule", "locked_rulebook", name),
                    source_path=str(RULEBOOK_JSON_PATH),
                    source_kind="rule",
                    module="综合",
                    question_type=name,
                    source_domain="local_state",
                    style_tags=["locked_rulebook"],
                    difficulty_hint="guide",
                    content=f"{name}: {text}",
                    normalized_content=text,
                    anti_copy_risk=0.1,
                    usable_for_generation=True,
                    metadata={"section": name},
                )
            )
    return chunks


def extract_memory_chunks() -> list[RagChunk]:
    memory = read_json(META_MEMORY_PATH, {})
    if not memory:
        return []
    chunks: list[RagChunk] = []
    for key in ["reinforce", "avoid", "recent_feedback"]:
        payload = memory.get(key, [])
        if not payload:
            continue
        text = normalize_retrieval_text(json.dumps(payload, ensure_ascii=False))
        chunks.append(
            RagChunk(
                chunk_id=stable_chunk_id("memory", key, len(payload)),
                source_path=str(META_MEMORY_PATH),
                source_kind="memory",
                module="综合",
                question_type=key,
                source_domain="local_state",
                style_tags=["meta_memory"],
                difficulty_hint="guide",
                content=f"{key}: {text}",
                normalized_content=text,
                anti_copy_risk=0.1,
                usable_for_generation=True,
                metadata={"key": key},
            )
        )
    return chunks


def extract_learning_packet_chunks() -> list[RagChunk]:
    return markdown_file_chunks(LEARNING_PACKET_PATH, "learning_packet", module="综合")


def question_skeleton(row: dict[str, Any], module: str, question_type: str) -> str:
    knowledge = [normalize_retrieval_text(item) for item in row.get("knowledge_points", []) if normalize_retrieval_text(item)]
    source_ref = normalize_retrieval_text(row.get("source_ref", ""))
    analysis = normalize_retrieval_text(row.get("analysis", ""))[:180]
    answer = normalize_retrieval_text(row.get("answer", ""))
    parts = [
        f"模块: {module}",
        f"题型: {question_type}",
        f"考点: {'、'.join(knowledge[:4]) or '未标注'}",
        f"来源: {source_ref or normalize_retrieval_text(row.get('exam_title', '未标注'))}",
        f"解析摘要: {analysis or '无'}",
        f"答案形式: {answer or '未知'}",
    ]
    return " | ".join(parts)


def extract_question_chunks(limit: int | None = None) -> list[RagChunk]:
    rows = read_jsonl(QUESTIONS_PATH)
    if limit is not None:
        rows = rows[:limit]
    chunks: list[RagChunk] = []
    for row in rows:
        raw_module = row.get("chapter") or row.get("chapter_intro") or row.get("exam_family") or ""
        module = canonicalize_module(str(raw_module))
        question_type = canonicalize_question_type(str(row.get("question_type", "")), module)
        content = question_skeleton(row, module, question_type)
        normalized = normalize_retrieval_text(content)
        chunks.append(
            RagChunk(
                chunk_id=stable_chunk_id("question", row.get("source_file", ""), row.get("question_number", "")),
                source_path=str(row.get("source_ref") or row.get("source_file") or QUESTIONS_PATH),
                source_kind="question",
                module=module,
                question_type=question_type,
                source_domain="question_bank",
                style_tags=[normalize_retrieval_text(row.get("exam_family", "")) or "question_bank"],
                difficulty_hint=estimate_difficulty(row.get("accuracy_pct")),
                content=content,
                normalized_content=normalized,
                anti_copy_risk=0.35,
                usable_for_generation=True,
                metadata={
                    "question_number": row.get("question_number"),
                    "answer": row.get("answer"),
                    "source_file": row.get("source_file"),
                },
            )
        )
    return chunks


def extract_crawler_chunks(limit: int | None = None) -> list[RagChunk]:
    rows = read_jsonl(WEB_MATERIALS_PATH)
    rows.sort(
        key=lambda row: (
            normalize_retrieval_text(row.get("last_seen_at", "") or row.get("fetched_at", "") or row.get("published_at", "")),
            float(row.get("relevance_score", 0) or 0),
        ),
        reverse=True,
    )
    if limit is not None and len(rows) > limit:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            module = canonicalize_module(str(row.get("section", "")))
            grouped.setdefault(module, []).append(row)

        modules = [module for module in grouped.keys() if grouped.get(module)]
        min_per_module = max(2, limit // max(len(modules) * 4, 1))
        selected: list[dict[str, Any]] = []
        cursor: dict[str, int] = {module: 0 for module in modules}

        for module in modules:
            take = min(min_per_module, len(grouped[module]))
            selected.extend(grouped[module][:take])
            cursor[module] = take

        while len(selected) < limit:
            progressed = False
            modules_sorted = sorted(modules, key=lambda name: len(grouped[name]) - cursor[name], reverse=True)
            for module in modules_sorted:
                index = cursor[module]
                if index >= len(grouped[module]):
                    continue
                selected.append(grouped[module][index])
                cursor[module] += 1
                progressed = True
                if len(selected) >= limit:
                    break
            if not progressed:
                break
        rows = selected[:limit]
    chunks: list[RagChunk] = []
    for row in rows:
        module = canonicalize_module(str(row.get("section", "")))
        title = normalize_retrieval_text(row.get("title", ""))
        summary = normalize_retrieval_text(row.get("summary", ""))
        content = normalize_retrieval_text(row.get("content", ""))
        merged = " ".join(part for part in [title, summary, content[:220]] if part)
        if not merged:
            continue
        chunks.append(
            RagChunk(
                chunk_id=stable_chunk_id("crawler", row.get("article_url", ""), row.get("title", "")),
                source_path=str(row.get("article_url") or row.get("seed_url") or WEB_MATERIALS_PATH),
                source_kind="crawler",
                module=module,
                question_type="材料风格",
                source_domain=normalize_retrieval_text(row.get("source_domain", "")) or "web",
                style_tags=[normalize_retrieval_text(row.get("source_name", "")) or "crawler"],
                difficulty_hint="medium",
                content=merged,
                normalized_content=normalize_retrieval_text(merged),
                anti_copy_risk=0.12,
                usable_for_generation=True,
                metadata={
                    "published_at": row.get("published_at"),
                    "source_name": row.get("source_name"),
                    "fetched_at": row.get("fetched_at"),
                    "last_seen_at": row.get("last_seen_at"),
                    "fetch_count": row.get("fetch_count"),
                    "content_chars": row.get("content_chars"),
                },
            )
        )
    return chunks


def _extract_docx_plain_text(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            xml = archive.read("word/document.xml").decode("utf-8", errors="replace")
            mht_text = ""
            if "word/afchunk.mht" in archive.namelist():
                raw_mht = archive.read("word/afchunk.mht")
                decoded_mht = quopri.decodestring(raw_mht).decode("utf-8", errors="replace")
                html_match = re.search(r"<html[\s\S]*</html>", decoded_mht, re.IGNORECASE)
                if html_match:
                    mht_text = html_match.group(0)
    except Exception:  # noqa: BLE001
        return ""
    text = re.sub(r"</w:p>", "\n", xml, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    if mht_text:
        html_plain = re.sub(r"<script[\s\S]*?</script>", " ", mht_text, flags=re.IGNORECASE)
        html_plain = re.sub(r"<style[\s\S]*?</style>", " ", html_plain, flags=re.IGNORECASE)
        html_plain = re.sub(r"<[^>]+>", " ", html_plain)
        html_plain = unescape(html_plain)
        text = f"{text}\n{html_plain}"
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return normalize_retrieval_text(text)


def extract_local_exam_chunks(limit: int = 300) -> list[RagChunk]:
    files = sorted(
        p
        for p in ROOT.rglob("*.docx")
        if p.is_file()
        and not p.name.startswith("~$")
        and ".venv" not in str(p)
        and "__pycache__" not in str(p)
    )
    chunks: list[RagChunk] = []
    for path in files[:limit]:
        text = _extract_docx_plain_text(path)
        if len(text) < 120:
            continue
        module = canonicalize_module(path.stem)
        content = text[:1800]
        chunks.append(
            RagChunk(
                chunk_id=stable_chunk_id("local_exam", path.name, path.stat().st_size),
                source_path=str(path),
                source_kind="local_exam",
                module=module,
                question_type="真题语料",
                source_domain="local_exam_docs",
                style_tags=["local_exam", "docx"],
                difficulty_hint="medium",
                content=content,
                normalized_content=normalize_retrieval_text(content),
                anti_copy_risk=0.15,
                usable_for_generation=True,
                metadata={"filename": path.name},
            )
        )
    return chunks


def extract_all_chunks() -> list[RagChunk]:
    config = load_rag_config()
    question_limit = int(config.get("build", {}).get("question_limit", 1200))
    crawler_limit = int(config.get("build", {}).get("crawler_limit", 400))
    chunks: list[RagChunk] = []
    chunks.extend(extract_rule_chunks())
    chunks.extend(extract_memory_chunks())
    chunks.extend(extract_learning_packet_chunks())
    chunks.extend(extract_question_chunks(limit=question_limit))
    chunks.extend(extract_crawler_chunks(limit=crawler_limit))
    chunks.extend(extract_local_exam_chunks())
    return chunks
