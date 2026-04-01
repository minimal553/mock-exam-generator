from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
STATE_DIR = ROOT / "state"
WEB_LIBRARY_PATH = DATA_DIR / "web_materials.jsonl"
WEB_LIBRARY_MANIFEST_PATH = STATE_DIR / "web_material_library_manifest.json"


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def material_content_hash(title: str, content: str) -> str:
    payload = normalize_ws(content) or normalize_ws(title)
    return hashlib.sha1(payload.encode("utf-8", "ignore")).hexdigest()


def parse_timestamp(value: str) -> datetime | None:
    raw = normalize_ws(value)
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def canonicalize_material_row(row: dict[str, Any], *, seen_at: str | None = None) -> dict[str, Any]:
    title = normalize_ws(row.get("title", ""))
    content = str(row.get("content") or "").strip()
    fetched_at = normalize_ws(row.get("fetched_at", "")) or normalize_ws(seen_at or "")
    first_seen_at = normalize_ws(row.get("first_seen_at", "")) or fetched_at
    last_seen_at = normalize_ws(row.get("last_seen_at", "")) or fetched_at
    article_url = normalize_ws(row.get("article_url", ""))
    seen_urls = [normalize_ws(item) for item in row.get("seen_urls", []) if normalize_ws(item)]
    if article_url and article_url not in seen_urls:
        seen_urls.append(article_url)
    return {
        "section": normalize_ws(row.get("section", "")),
        "source_name": normalize_ws(row.get("source_name", "")),
        "source_domain": normalize_ws(row.get("source_domain", "")),
        "seed_url": normalize_ws(row.get("seed_url", "")),
        "article_url": article_url,
        "title": title,
        "published_at": normalize_ws(row.get("published_at", "")),
        "summary": normalize_ws(row.get("summary", "")),
        "content": content,
        "relevance_score": int(float(row.get("relevance_score", 0) or 0)),
        "fetched_at": fetched_at,
        "first_seen_at": first_seen_at,
        "last_seen_at": last_seen_at,
        "fetch_count": int(row.get("fetch_count", 1) or 1),
        "content_hash": normalize_ws(row.get("content_hash", "")) or material_content_hash(title, content),
        "content_chars": int(row.get("content_chars", 0) or len(content)),
        "seen_urls": seen_urls,
    }


def merge_material_rows(
    existing_rows: list[dict[str, Any]],
    incoming_rows: list[dict[str, Any]],
    *,
    seen_at: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    normalized_existing = [canonicalize_material_row(row, seen_at=seen_at) for row in existing_rows]
    by_url = {row["article_url"]: row for row in normalized_existing if row.get("article_url")}
    by_hash = {row["content_hash"]: row for row in normalized_existing if row.get("content_hash")}
    stats = {
        "added_count": 0,
        "updated_count": 0,
        "duplicate_count": 0,
        "total_count": len(normalized_existing),
        "total_chars": sum(int(row.get("content_chars", 0) or 0) for row in normalized_existing),
    }

    for raw_row in incoming_rows:
        row = canonicalize_material_row(raw_row, seen_at=seen_at)
        existing = None
        if row["article_url"]:
            existing = by_url.get(row["article_url"])
        if existing is None and row["content_hash"]:
            existing = by_hash.get(row["content_hash"])

        if existing is None:
            normalized_existing.append(row)
            if row["article_url"]:
                by_url[row["article_url"]] = row
            by_hash[row["content_hash"]] = row
            stats["added_count"] += 1
            continue

        stats["updated_count"] += 1
        stats["duplicate_count"] += 1
        existing["summary"] = row["summary"] or existing["summary"]
        existing["title"] = row["title"] or existing["title"]
        if len(row["content"]) > len(existing["content"]):
            existing["content"] = row["content"]
            existing["content_chars"] = row["content_chars"]
        existing["published_at"] = row["published_at"] or existing["published_at"]
        existing["seed_url"] = row["seed_url"] or existing["seed_url"]
        existing["source_name"] = row["source_name"] or existing["source_name"]
        existing["source_domain"] = row["source_domain"] or existing["source_domain"]
        existing["section"] = row["section"] or existing["section"]
        existing["relevance_score"] = max(
            int(existing.get("relevance_score", 0) or 0),
            int(row.get("relevance_score", 0) or 0),
        )
        existing["fetch_count"] = int(existing.get("fetch_count", 1) or 1) + 1
        existing["first_seen_at"] = existing.get("first_seen_at") or row["first_seen_at"]
        existing["last_seen_at"] = row["last_seen_at"] or existing.get("last_seen_at") or row["fetched_at"]
        existing["fetched_at"] = existing["last_seen_at"]
        merged_urls = {
            normalize_ws(item)
            for item in [*existing.get("seen_urls", []), *row.get("seen_urls", []), row.get("article_url", "")]
            if normalize_ws(item)
        }
        existing["seen_urls"] = sorted(merged_urls)
        if existing["article_url"]:
            by_url[existing["article_url"]] = existing
        for alias_url in existing["seen_urls"]:
            by_url[alias_url] = existing
        by_hash[existing["content_hash"]] = existing

    normalized_existing.sort(
        key=lambda row: (
            parse_timestamp(str(row.get("last_seen_at", ""))) or datetime.min,
            int(row.get("relevance_score", 0) or 0),
        ),
        reverse=True,
    )
    stats["total_count"] = len(normalized_existing)
    stats["total_chars"] = sum(int(row.get("content_chars", 0) or 0) for row in normalized_existing)
    return normalized_existing, stats


def build_material_library_manifest(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_section = Counter(normalize_ws(row.get("section", "")) or "未分类" for row in rows)
    by_domain = Counter(normalize_ws(row.get("source_domain", "")) or "unknown" for row in rows)
    by_source = Counter(normalize_ws(row.get("source_name", "")) or "unknown" for row in rows)
    return {
        "generated_at": datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "row_count": len(rows),
        "total_chars": material_char_count(rows),
        "section_counts": dict(by_section),
        "domain_counts": dict(by_domain),
        "source_counts": dict(by_source),
    }


def save_material_library(rows: list[dict[str, Any]]) -> dict[str, Any]:
    write_jsonl(WEB_LIBRARY_PATH, rows)
    manifest = build_material_library_manifest(rows)
    write_json(WEB_LIBRARY_MANIFEST_PATH, manifest)
    return manifest


def load_material_library() -> list[dict[str, Any]]:
    return read_jsonl(WEB_LIBRARY_PATH)


def material_char_count(rows: list[dict[str, Any]], section: str | None = None) -> int:
    total = 0
    for row in rows:
        if section and normalize_ws(row.get("section", "")) != normalize_ws(section):
            continue
        raw = row.get("content_chars", 0)
        try:
            total += int(raw or 0)
        except (TypeError, ValueError):
            total += len(str(row.get("content") or ""))
    return total
