#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from email import message_from_bytes
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup
from bs4 import FeatureNotFound


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
STATE_DIR = ROOT / "state"
OUTPUT_DIR = ROOT / "output" / "mock_tests"
MATERIAL_INDEX_PATH = DATA_DIR / "material_index.json"
QUESTIONS_PATH = DATA_DIR / "questions.jsonl"
SUMMARY_PATH = DATA_DIR / "material_summary.md"
RULEBOOK_JSON_PATH = STATE_DIR / "locked_rulebook.json"
RULEBOOK_MD_PATH = STATE_DIR / "rulebook.md"
META_MEMORY_PATH = STATE_DIR / "meta_memory.json"
FEEDBACK_LOG_PATH = STATE_DIR / "feedback_log.jsonl"
LEARNING_PACKET_PATH = STATE_DIR / "learning_packet.md"
QUESTION_RE = re.compile(
    r"(?:【试题ID】\d+\s+)?(?P<number>\d+)\.\s*\((?P<qtype>[^)]+)\)\s*(?P<stem>.*?)(?=\s+A\.\s)",
    re.S,
)
OPTION_RE = re.compile(r"([A-D])\.\s*(.*?)(?=(?:\s+[A-D]\.\s)|\s+正确答案：|$)", re.S)


def now_iso() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def iter_docx_files(material_dir: Path) -> list[Path]:
    return sorted(
        p for p in material_dir.rglob("*.docx") if p.is_file() and not p.name.startswith("~$")
    )


def extract_html_from_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        raw = archive.read("word/afchunk.mht")
    message = message_from_bytes(raw)
    for part in message.walk():
        if part.get_content_type() != "text/html":
            continue
        payload = part.get_payload(decode=True)
        charset = part.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="replace")
    raise ValueError(f"未在 {path.name} 中找到 HTML 内容")


def parse_docx_html(html: str) -> BeautifulSoup:
    try:
        return BeautifulSoup(html, "lxml")
    except FeatureNotFound:
        return BeautifulSoup(html, "html.parser")


def extract_between(text: str, start: str, end_markers: list[str]) -> str:
    start_index = text.find(start)
    if start_index == -1:
        return ""
    begin = start_index + len(start)
    end = len(text)
    for marker in end_markers:
        marker_index = text.find(marker, begin)
        if marker_index != -1:
            end = min(end, marker_index)
    return normalize_ws(text[begin:end])


def chapter_name(chapter_text: str) -> str:
    match = re.search(r"[一二三四五六七八九十]+、\s*(.*?)：", chapter_text)
    if match:
        return normalize_ws(match.group(1))
    return normalize_ws(chapter_text)


def parse_options(section_text: str) -> dict[str, str]:
    options: dict[str, str] = {}
    for match in OPTION_RE.finditer(section_text):
        options[match.group(1)] = normalize_ws(match.group(2))
    return options


def infer_exam_family(filename: str) -> str:
    if "国家公务员" in filename:
        return "国考行测"
    if "事业单位联考" in filename:
        return "事业单位联考A类职测"
    return "未知"


def parse_exam(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    html = extract_html_from_docx(path)
    soup = parse_docx_html(html)
    title_node = soup.select_one("h1")
    title = normalize_ws(title_node.get_text(" ", strip=True)) if title_node else path.stem
    chapters: list[str] = []
    questions: list[dict[str, Any]] = []
    current_chapter = ""
    chapter_order = 0
    accuracy_values: list[float] = []

    for section in soup.select("section.question-section"):
        chapter_node = section.select_one("div.chapter")
        if chapter_node:
            current_chapter = normalize_ws(" ".join(chapter_node.stripped_strings))
            chapter_order += 1
            chapters.append(current_chapter)

        section_text = normalize_ws(" ".join(section.stripped_strings))
        if current_chapter and section_text.startswith(current_chapter):
            section_text = normalize_ws(section_text[len(current_chapter) :])

        if "正确答案：" not in section_text:
            continue

        question_match = QUESTION_RE.search(section_text)
        answer_match = re.search(r"正确答案：\s*([A-D]+)", section_text)
        question_number = int(question_match.group("number")) if question_match else None
        question_type = normalize_ws(question_match.group("qtype")) if question_match else ""
        stem = normalize_ws(question_match.group("stem")) if question_match else ""
        options = parse_options(section_text)
        knowledge_points = [
            normalize_ws(item)
            for item in re.split(r"[,，、]", extract_between(section_text, "【考点】", ["【题目适用类型】", "【来源】", "【全站数据】"]))
            if normalize_ws(item)
        ]
        analysis = extract_between(section_text, "解析：", ["【考点】", "【题目适用类型】", "【来源】", "【全站数据】"])
        source_ref = extract_between(section_text, "【来源】", ["【全站数据】"])
        accuracy_match = re.search(r"正确率为\s*([\d.]+)%", section_text)
        wrong_option_match = re.search(r"易错项为\s*([A-D])", section_text)
        question_id_match = re.search(r"【试题ID】\s*(\d+)", section_text)
        accuracy_pct = float(accuracy_match.group(1)) if accuracy_match else None
        if accuracy_pct is not None:
            accuracy_values.append(accuracy_pct)

        questions.append(
            {
                "source_file": path.name,
                "exam_title": title,
                "exam_family": infer_exam_family(path.name),
                "chapter": chapter_name(current_chapter) if current_chapter else "",
                "chapter_intro": current_chapter,
                "chapter_order": chapter_order,
                "question_id": question_id_match.group(1) if question_id_match else "",
                "question_number": question_number,
                "question_type": question_type,
                "stem": stem,
                "options": options,
                "answer": answer_match.group(1) if answer_match else "",
                "analysis": analysis,
                "knowledge_points": knowledge_points,
                "accuracy_pct": accuracy_pct,
                "common_wrong_option": wrong_option_match.group(1) if wrong_option_match else "",
                "source_ref": source_ref,
                "raw_text": section_text,
            }
        )

    material = {
        "source_file": path.name,
        "exam_title": title,
        "exam_family": infer_exam_family(path.name),
        "question_count": len(questions),
        "chapter_count": len(set(q["chapter"] for q in questions if q["chapter"])),
        "chapters": [chapter_name(item) for item in chapters],
        "mean_accuracy_pct": round(sum(accuracy_values) / len(accuracy_values), 2) if accuracy_values else None,
    }
    return material, questions


def build_material_summary(materials: list[dict[str, Any]], questions: list[dict[str, Any]]) -> str:
    chapter_counter = Counter(q["chapter"] for q in questions if q["chapter"])
    family_counter = Counter(m["exam_family"] for m in materials)
    point_counter = Counter()
    for question in questions:
        for point in question["knowledge_points"]:
            point_counter[point] += 1

    lines = [
        "# 学习材料结构摘要",
        "",
        f"- 更新时间: {now_iso()}",
        f"- 材料总数: {len(materials)}",
        f"- 题目总数: {len(questions)}",
        "",
        "## 考试家族分布",
        "",
    ]

    for family, count in family_counter.most_common():
        lines.append(f"- {family}: {count} 套")

    lines.extend(["", "## 单套材料概览", ""])
    for material in materials:
        lines.append(
            f"- {material['source_file']}: {material['question_count']} 题, "
            f"{material['chapter_count']} 个部分, 平均正确率 {material['mean_accuracy_pct'] or 'N/A'}%"
        )

    lines.extend(["", "## 章节题量", ""])
    for chapter, count in chapter_counter.most_common():
        lines.append(f"- {chapter}: {count} 题")

    lines.extend(["", "## 高频考点", ""])
    for point, count in point_counter.most_common(20):
        lines.append(f"- {point}: {count}")

    return "\n".join(lines) + "\n"


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def sync_learning_packet() -> str:
    summary_exists = SUMMARY_PATH.exists()
    materials = read_json(MATERIAL_INDEX_PATH, [])
    rulebook = read_json(RULEBOOK_JSON_PATH, {})
    memory = read_json(META_MEMORY_PATH, {})

    lines = [
        "# 学习包",
        "",
        f"- 更新时间: {now_iso()}",
        f"- 材料索引已生成: {'是' if summary_exists else '否'}",
        f"- 已收录材料: {len(materials)}",
        f"- 当前规则版本: {rulebook.get('version', 'untrained')}",
        f"- 规则状态: {rulebook.get('status', 'unknown')}",
        f"- 反馈总数: {memory.get('totals', {}).get('feedback_entries', 0)}",
        f"- 好标签: {memory.get('totals', {}).get('good', 0)}",
        f"- 坏标签: {memory.get('totals', {}).get('bad', 0)}",
        "",
        "## 最近强化信号",
        "",
    ]

    for item in memory.get("reinforce", [])[:10]:
        lines.append(f"- {item['tag']}: +{item['net']} ({item['good']} 好 / {item['bad']} 坏)")

    if not memory.get("reinforce"):
        lines.append("- 暂无")

    lines.extend(["", "## 最近规避信号", ""])
    for item in memory.get("avoid", [])[:10]:
        lines.append(f"- {item['tag']}: {item['net']} ({item['good']} 好 / {item['bad']} 坏)")

    if not memory.get("avoid"):
        lines.append("- 暂无")

    lines.extend(["", "## 最近反馈", ""])
    recent_feedback = memory.get("recent_feedback", [])
    if recent_feedback:
        for entry in recent_feedback[:10]:
            lines.append(
                f"- {entry['timestamp']}: {entry['label']} / {entry['paper_id']} / "
                f"tags={','.join(entry['tags']) if entry['tags'] else 'none'} / "
                f"notes={entry['notes'] or 'none'}"
            )
    else:
        lines.append("- 暂无")

    if summary_exists:
        lines.extend(["", "## 材料摘要位置", "", f"- {SUMMARY_PATH.relative_to(ROOT)}"])

    LEARNING_PACKET_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(LEARNING_PACKET_PATH.relative_to(ROOT))


def load_feedback_entries() -> list[dict[str, Any]]:
    if not FEEDBACK_LOG_PATH.exists():
        return []
    entries: list[dict[str, Any]] = []
    with FEEDBACK_LOG_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            entries.append(json.loads(line))
    return entries


def rebuild_meta_memory(entries: list[dict[str, Any]]) -> dict[str, Any]:
    totals = {"feedback_entries": len(entries), "good": 0, "bad": 0}
    tag_score: dict[str, dict[str, int]] = defaultdict(lambda: {"good": 0, "bad": 0})

    for entry in entries:
        label = entry["label"]
        totals[label] += 1
        for tag in entry.get("tags", []):
            tag_score[tag][label] += 1

    reinforce = []
    avoid = []
    for tag, counts in tag_score.items():
        net = counts["good"] - counts["bad"]
        bucket = {"tag": tag, "good": counts["good"], "bad": counts["bad"], "net": net}
        if net >= 0:
            reinforce.append(bucket)
        else:
            avoid.append(bucket)

    reinforce.sort(key=lambda item: (-item["net"], -item["good"], item["tag"]))
    avoid.sort(key=lambda item: (item["net"], -item["bad"], item["tag"]))

    return {
        "updated_at": now_iso(),
        "totals": totals,
        "score": totals["good"] - totals["bad"],
        "reinforce": reinforce,
        "avoid": avoid,
        "recent_feedback": list(reversed(entries[-10:])),
    }


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    marker = "\n---\n"
    end_index = text.find(marker, 4)
    if end_index == -1:
        return {}, text
    block = text[4:end_index]
    body = text[end_index + len(marker) :]
    payload: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        payload[key.strip()] = value.strip()
    return payload, body


def command_index_materials(args: argparse.Namespace) -> int:
    material_dir = Path(args.material_dir).resolve()
    files = iter_docx_files(material_dir)
    if not files:
        print(f"未在 {material_dir} 找到 .docx 材料", file=sys.stderr)
        return 1

    materials: list[dict[str, Any]] = []
    questions: list[dict[str, Any]] = []
    skipped: list[str] = []
    for path in files:
        try:
            material, parsed_questions = parse_exam(path)
        except (zipfile.BadZipFile, KeyError, ValueError) as exc:
            skipped.append(f"{path.name}: {exc}")
            continue
        materials.append(material)
        questions.extend(parsed_questions)

    if not materials:
        print("所有 .docx 材料均无法解析", file=sys.stderr)
        for item in skipped[:10]:
            print(f"- {item}", file=sys.stderr)
        return 1

    write_json(MATERIAL_INDEX_PATH, materials)
    write_jsonl(QUESTIONS_PATH, questions)
    SUMMARY_PATH.write_text(build_material_summary(materials, questions), encoding="utf-8")
    sync_learning_packet()

    print(f"已索引 {len(materials)} 份材料, {len(questions)} 道题")
    if skipped:
        print(f"已跳过 {len(skipped)} 份异常材料")
        for item in skipped[:10]:
            print(f"- {item}")
    print(f"- {MATERIAL_INDEX_PATH.relative_to(ROOT)}")
    print(f"- {QUESTIONS_PATH.relative_to(ROOT)}")
    print(f"- {SUMMARY_PATH.relative_to(ROOT)}")
    return 0


def command_sync_learning_packet(_: argparse.Namespace) -> int:
    path = sync_learning_packet()
    print(f"已更新 {path}")
    return 0


def command_record_feedback(args: argparse.Namespace) -> int:
    paper_path = Path(args.paper).resolve()
    if not paper_path.exists():
        print(f"模拟卷不存在: {paper_path}", file=sys.stderr)
        return 1

    frontmatter, _ = parse_frontmatter(paper_path.read_text(encoding="utf-8"))
    entry = {
        "timestamp": now_iso(),
        "paper_path": str(paper_path.relative_to(ROOT)),
        "paper_id": frontmatter.get("paper_id", paper_path.stem),
        "rulebook_version": frontmatter.get("rulebook_version", ""),
        "label": args.label,
        "tags": [normalize_ws(tag) for tag in args.tags.split(",") if normalize_ws(tag)] if args.tags else [],
        "notes": normalize_ws(args.notes or ""),
    }

    FEEDBACK_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with FEEDBACK_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    entries = load_feedback_entries()
    memory = rebuild_meta_memory(entries)
    write_json(META_MEMORY_PATH, memory)
    sync_learning_packet()

    print(f"已记录反馈: {entry['paper_id']} -> {entry['label']}")
    print(f"- {META_MEMORY_PATH.relative_to(ROOT)}")
    return 0


def validate_rulebook_payload(payload: dict[str, Any]) -> list[str]:
    required_keys = [
        "version",
        "generated_at",
        "status",
        "source_materials",
        "exam_profile",
        "hard_constraints",
        "soft_preferences",
        "option_design_rules",
        "explanation_rules",
        "anti_patterns",
        "memory_effects",
    ]
    missing = [key for key in required_keys if key not in payload]
    errors = [f"缺少字段: {key}" for key in missing]

    if payload.get("version") in {"", "untrained", None}:
        errors.append("version 仍然是 untrained")
    if payload.get("status") != "locked":
        errors.append("status 必须为 locked")
    exam_profile = payload.get("exam_profile", {})
    if not isinstance(exam_profile.get("section_blueprint"), list) or not exam_profile.get("section_blueprint"):
        errors.append("exam_profile.section_blueprint 不能为空")
    for key in ["hard_constraints", "option_design_rules", "explanation_rules", "anti_patterns"]:
        if not isinstance(payload.get(key), list) or not payload.get(key):
            errors.append(f"{key} 必须是非空数组")
    memory_effects = payload.get("memory_effects", {})
    if not isinstance(memory_effects.get("reinforce"), list):
        errors.append("memory_effects.reinforce 必须是数组")
    if not isinstance(memory_effects.get("avoid"), list):
        errors.append("memory_effects.avoid 必须是数组")
    return errors


def command_validate_rulebook(_: argparse.Namespace) -> int:
    payload = read_json(RULEBOOK_JSON_PATH, {})
    errors = validate_rulebook_payload(payload)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"规则簿可用: {payload['version']}")
    return 0


def command_validate_paper(args: argparse.Namespace) -> int:
    paper_path = Path(args.paper).resolve()
    if not paper_path.exists():
        print(f"模拟卷不存在: {paper_path}", file=sys.stderr)
        return 1

    current_rulebook = read_json(RULEBOOK_JSON_PATH, {})
    frontmatter, body = parse_frontmatter(paper_path.read_text(encoding="utf-8"))
    required_fields = ["paper_id", "generated_at", "rulebook_version", "generator_mode", "question_count"]
    errors = [f"frontmatter 缺少 {field}" for field in required_fields if field not in frontmatter]
    if not errors:
        if frontmatter["generator_mode"] != "locked_rulebook_only":
            errors.append("generator_mode 必须是 locked_rulebook_only")
        if frontmatter["rulebook_version"] != current_rulebook.get("version"):
            errors.append("rulebook_version 与当前 locked_rulebook.json 不一致")
        question_block = body
        question_start = body.find("## 题目")
        if question_start != -1:
            question_block = body[question_start + len("## 题目") :]
        answer_start = question_block.find("## 答案")
        if answer_start != -1:
            question_block = question_block[:answer_start]
        question_lines = re.findall(r"(?m)^\d+\.\s", question_block)
        answer_block = ""
        note_block = ""
        if "## 答案" in body:
            answer_block = body.split("## 答案", 1)[1]
        if "## 命题说明" in answer_block:
            answer_block, note_block = answer_block.split("## 命题说明", 1)
        answer_lines = re.findall(r"(?m)^\d+\.\s*[A-D]\s*$", answer_block)
        note_lines = re.findall(r"(?m)^\d+\.\s", note_block)
        try:
            question_count = int(frontmatter["question_count"])
            if question_count != len(question_lines):
                errors.append(
                    f"question_count={question_count} 与题目行数={len(question_lines)} 不一致"
                )
            if question_count != len(answer_lines):
                errors.append(
                    f"question_count={question_count} 与答案行数={len(answer_lines)} 不一致"
                )
            if question_count != len(note_lines):
                errors.append(
                    f"question_count={question_count} 与命题说明行数={len(note_lines)} 不一致"
                )
        except ValueError:
            errors.append("question_count 不是整数")

    if "## 答案" not in body:
        errors.append("正文缺少 `## 答案` 段落")
    if "## 命题说明" not in body:
        errors.append("正文缺少 `## 命题说明` 段落")
    if "待补充" in body or "[MISSING]" in body or "\nTBD" in body:
        errors.append("正文仍包含占位内容（待补充 / [MISSING] / TBD）")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(f"模拟卷通过校验: {paper_path.name}")
    return 0


def command_build_rag(_: argparse.Namespace) -> int:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from standalone_app.rag.index_builder import build_rag_index

    manifest = build_rag_index()
    print(f"RAG corpus rebuilt: {manifest['chunk_count']} chunks")
    return 0


def command_status(_: argparse.Namespace) -> int:
    materials = read_json(MATERIAL_INDEX_PATH, [])
    feedback = read_json(META_MEMORY_PATH, {})
    rulebook = read_json(RULEBOOK_JSON_PATH, {})
    question_count = 0
    if QUESTIONS_PATH.exists():
        question_count = sum(1 for line in QUESTIONS_PATH.read_text(encoding="utf-8").splitlines() if line.strip())

    print(f"材料: {len(materials)} 套")
    print(f"题目: {question_count} 道")
    print(f"规则版本: {rulebook.get('version', 'untrained')}")
    print(f"反馈: {feedback.get('totals', {}).get('feedback_entries', 0)} 条")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="公考学习/出题工作流工具")
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser("index-materials", help="抽取 DOCX 学习材料")
    index_parser.add_argument("--material-dir", default=str(ROOT), help="材料目录")
    index_parser.set_defaults(func=command_index_materials)

    sync_parser = subparsers.add_parser("sync-learning-packet", help="刷新学习包")
    sync_parser.set_defaults(func=command_sync_learning_packet)

    feedback_parser = subparsers.add_parser("record-feedback", help="记录人工好/坏反馈")
    feedback_parser.add_argument("--paper", required=True, help="模拟卷 Markdown 路径")
    feedback_parser.add_argument("--label", required=True, choices=["good", "bad"], help="标签")
    feedback_parser.add_argument("--tags", default="", help="逗号分隔的结构化反馈标签")
    feedback_parser.add_argument("--notes", default="", help="可选补充说明")
    feedback_parser.set_defaults(func=command_record_feedback)

    rulebook_parser = subparsers.add_parser("validate-rulebook", help="校验锁定规则簿")
    rulebook_parser.set_defaults(func=command_validate_rulebook)

    paper_parser = subparsers.add_parser("validate-paper", help="校验模拟卷是否遵循锁定规则")
    paper_parser.add_argument("--paper", required=True, help="模拟卷 Markdown 路径")
    paper_parser.set_defaults(func=command_validate_paper)

    rag_parser = subparsers.add_parser("build-rag", help="重建 RAG 检索语料")
    rag_parser.set_defaults(func=command_build_rag)

    status_parser = subparsers.add_parser("status", help="查看当前工作流状态")
    status_parser.set_defaults(func=command_status)

    return parser


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
