import unittest
from pathlib import Path
from unittest.mock import patch

import standalone_app.app as app_mod


class ImmediateThread:
    def __init__(self, target=None, args=None, kwargs=None, daemon=None):
        self._target = target
        self._args = args or ()
        self._kwargs = kwargs or {}
        self.daemon = daemon

    def start(self):
        if self._target:
            self._target(*self._args, **self._kwargs)


class StandaloneApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = app_mod.app.test_client()
        app_mod.GENERATION_JOBS.clear()

    def test_run_session_starts_background_job_and_exposes_progress(self):
        paper_path = app_mod.OUTPUT_DIR / "api-job-success.md"
        markdown = (
            "---\n"
            "paper_id: mock-success\n"
            "generated_at: 2026-03-26T11:00:00+08:00\n"
            "rulebook_version: v2026.03.22-1\n"
            "generator_mode: locked_rulebook_only\n"
            "question_count: 20\n"
            "---\n\n"
            "# 测试卷\n"
        )
        paper_path.write_text(markdown, encoding="utf-8")

        try:
            with patch.object(app_mod, "refresh_materials", return_value="refresh ok"), \
                 patch.object(app_mod, "crawl_web_materials", return_value="crawl ok"), \
                 patch.object(app_mod, "build_session_learning_content", return_value=("learning ok", "cached")), \
                 patch.object(app_mod, "generate_valid_paper", return_value=(paper_path, markdown, "validation ok")), \
                 patch.object(app_mod, "save_session_state", return_value=None), \
                 patch.object(app_mod.threading, "Thread", ImmediateThread):
                resp = self.client.post(
                    "/api/run-session",
                    json={
                        "provider": "ollama",
                        "apiKey": "",
                        "model": "dummy",
                        "focus": "",
                        "materialDir": str(app_mod.ROOT),
                    },
                )

                self.assertEqual(resp.status_code, 200)
                payload = resp.get_json()
                self.assertTrue(payload["ok"])
                self.assertIn("job_id", payload)

                job_resp = self.client.get(f"/api/run-session/{payload['job_id']}")
                self.assertEqual(job_resp.status_code, 200)
                job = job_resp.get_json()
                self.assertEqual(job["state"], "succeeded")
                self.assertEqual(job["progress"], 100)
                self.assertEqual(job["result"]["paper_path"], str(paper_path))
                self.assertTrue(any("生成模拟题" in line or "模拟卷" in line for line in job["logs"]))
        finally:
            if paper_path.exists():
                paper_path.unlink()

    def test_run_session_job_fails_when_generated_paper_under_minimum(self):
        paper_path = app_mod.OUTPUT_DIR / "api-job-too-short.md"
        markdown = (
            "---\n"
            "paper_id: mock-short\n"
            "generated_at: 2026-03-26T11:00:00+08:00\n"
            "rulebook_version: v2026.03.22-1\n"
            "generator_mode: locked_rulebook_only\n"
            "question_count: 4\n"
            "---\n\n"
            "# 测试卷\n"
        )
        paper_path.write_text(markdown, encoding="utf-8")

        try:
            with patch.object(app_mod, "refresh_materials", return_value="refresh ok"), \
                 patch.object(app_mod, "crawl_web_materials", return_value="crawl ok"), \
                 patch.object(app_mod, "build_session_learning_content", return_value=("learning ok", "cached")), \
                 patch.object(app_mod, "generate_valid_paper", return_value=(paper_path, markdown, "validation ok")), \
                 patch.object(app_mod.threading, "Thread", ImmediateThread):
                resp = self.client.post(
                    "/api/run-session",
                    json={
                        "provider": "ollama",
                        "apiKey": "",
                        "model": "dummy",
                        "focus": "",
                        "materialDir": str(app_mod.ROOT),
                    },
                )

                self.assertEqual(resp.status_code, 200)
                payload = resp.get_json()
                job_resp = self.client.get(f"/api/run-session/{payload['job_id']}")
                self.assertEqual(job_resp.status_code, 200)
                job = job_resp.get_json()
                self.assertEqual(job["state"], "failed")
                self.assertIn("至少 16 题", job["error"])
        finally:
            if paper_path.exists():
                paper_path.unlink()

    def test_run_session_maps_qwen_alias_to_cloud_model(self):
        paper_path = app_mod.OUTPUT_DIR / "api-job-cloud-model.md"
        markdown = (
            "---\n"
            "paper_id: mock-cloud\n"
            "generated_at: 2026-03-26T11:00:00+08:00\n"
            "rulebook_version: v2026.03.22-1\n"
            "generator_mode: locked_rulebook_only\n"
            "question_count: 20\n"
            "---\n\n"
            "# 测试卷\n"
        )
        paper_path.write_text(markdown, encoding="utf-8")

        requested_model = "qwen3:235b"
        resolved_model = "qwen3-vl:235b-cloud"
        try:
            with patch.object(app_mod, "list_ollama_models", return_value=["gpt-oss:120b-cloud"]), \
                 patch.object(app_mod, "ollama_show_available", side_effect=lambda m: m == resolved_model), \
                 patch.object(app_mod, "refresh_materials", return_value="refresh ok"), \
                 patch.object(app_mod, "crawl_web_materials", return_value="crawl ok"), \
                 patch.object(app_mod, "build_session_learning_content", return_value=("learning ok", "cached")), \
                 patch.object(app_mod, "generate_valid_paper", return_value=(paper_path, markdown, "validation ok")), \
                 patch.object(app_mod, "save_session_state", return_value=None), \
                 patch.object(app_mod.threading, "Thread", ImmediateThread):
                resp = self.client.post(
                    "/api/run-session",
                    json={
                        "provider": "ollama",
                        "apiKey": "",
                        "model": requested_model,
                        "focus": "",
                        "materialDir": str(app_mod.ROOT),
                    },
                )
                self.assertEqual(resp.status_code, 200)
                job_id = resp.get_json()["job_id"]
                job = self.client.get(f"/api/run-session/{job_id}").get_json()
                self.assertEqual(job["state"], "succeeded")
                self.assertEqual(job["result"]["model"], resolved_model)
        finally:
            if paper_path.exists():
                paper_path.unlink()

    def test_find_delivery_gaps_allows_short_stem_with_data_context(self):
        paper = {
            "title": "# 测试卷",
            "sections": [
                {
                    "name": "资料分析（1题）",
                    "material_lines": ["2024年A指标为100，2025年为120，同比增长20%。" * 6],
                    "questions": [
                        {
                            "number": 18,
                            "block_lines": [
                                "18. 根据材料，2025年同比增长率约为多少？",
                                "A. 10%",
                                "B. 20%",
                                "C. 30%",
                                "D. 40%",
                            ],
                            "answer_lines": ["18. B"],
                            "note_lines": [
                                "18. 考点ID=10000004；考点=资料分析；考点路径=资料分析；来源Sheet=全局-基础考点树；"
                                "依据：由120与100可得同比增长20%；错项A将分母误设为120，故排除。"
                            ],
                        }
                    ],
                }
            ],
        }
        gaps = app_mod.find_delivery_gaps(paper)
        if (0, 0) in gaps:
            self.assertNotIn("stem", gaps[(0, 0)])

    def test_extract_rag_source_refs_and_bind_to_specs(self):
        rag_context = (
            "## RAG\n"
            "- 来源=www.stats.gov.cn\n"
            "- 来源=gongyi.people.com.cn\n"
            "- 来源=www.stats.gov.cn\n"
        )
        refs = app_mod.extract_rag_source_refs(rag_context)
        self.assertEqual(refs[:2], ["www.stats.gov.cn", "gongyi.people.com.cn"])

        specs = [
            {"number": 14, "section_name": "资料分析"},
            {"number": 15, "section_name": "资料分析"},
        ]
        bound = app_mod.bind_source_refs_to_question_specs("资料分析", specs, refs)
        self.assertEqual(bound[0].get("source_ref"), "www.stats.gov.cn")
        self.assertEqual(bound[1].get("source_ref"), "gongyi.people.com.cn")

    def test_auto_repair_question_notes_fills_missing_note(self):
        paper = {
            "title": "# 测试卷",
            "sections": [
                {
                    "name": "常识判断（1题）",
                    "material_lines": [],
                    "questions": [
                        {
                            "number": 3,
                            "block_lines": [
                                "3. 某机关作出行政处罚前未告知陈述申辩，以下哪项最符合法定程序？",
                                "A. 直接处罚",
                                "B. 补正告知后再处罚",
                                "C. 忽略程序",
                                "D. 仅口头通知",
                            ],
                            "answer_lines": ["3. B"],
                            "note_lines": [],
                        }
                    ],
                }
            ],
        }
        issues = {(0, 0): ["Q3 命题说明未证明最近错项为何错，缺少唯一性证明。"]}
        spec_lookup = {
            3: {
                "knowledge_point_id": "10000005",
                "knowledge_point_name": "常识判断",
                "knowledge_source_sheet": "全局-基础考点树",
                "knowledge_path": "常识判断",
                "source_ref": "local_state",
            }
        }
        fixed = app_mod.auto_repair_question_notes(
            paper=paper,
            issue_map=issues,
            question_spec_lookup=spec_lookup,
        )
        self.assertEqual(fixed, 1)
        note = paper["sections"][0]["questions"][0]["note_lines"][0]
        self.assertIn("依据", note)
        self.assertIn("排除", note)

    def test_parse_numbered_entry_lines_accepts_common_answer_formats(self):
        lines = [
            "1、A",
            "2)B",
            "**3． C**",
            "4. D",
        ]
        parsed = app_mod.parse_numbered_entry_lines(lines)
        self.assertIn(1, parsed)
        self.assertIn(2, parsed)
        self.assertIn(3, parsed)
        self.assertIn(4, parsed)
        self.assertTrue(parsed[1][0].startswith("1."))

    def test_extract_answer_choice_accepts_non_dot_numbering(self):
        self.assertEqual(app_mod.extract_answer_choice(["1、A"]), "A")
        self.assertEqual(app_mod.extract_answer_choice(["2)B"]), "B")
        self.assertEqual(app_mod.extract_answer_choice(["**3． C**"]), "C")

    def test_parse_numbered_entry_lines_accepts_multiple_number_formats(self):
        lines = [
            "1、B",
            "**2) C**",
            "3．D",
            "4. A",
        ]
        parsed = app_mod.parse_numbered_entry_lines(lines)
        self.assertEqual(parsed[1][0], "1. B")
        self.assertEqual(parsed[2][0], "2. C")
        self.assertEqual(parsed[3][0], "3. D")
        self.assertEqual(parsed[4][0], "4. A")

    def test_extract_answer_choice_accepts_non_dot_formats(self):
        self.assertEqual(app_mod.extract_answer_choice(["1、B"]), "B")
        self.assertEqual(app_mod.extract_answer_choice(["**2) C**"]), "C")
        self.assertEqual(app_mod.extract_answer_choice(["3．D"]), "D")


    def test_replace_question_from_payload_keeps_existing_answer_and_note_when_missing(self):
        paper = {
            "title": "# test",
            "sections": [
                {
                    "name": "常识判断",
                    "material_lines": [],
                    "questions": [
                        {
                            "number": 1,
                            "block_lines": ["1. 原题干", "A. a", "B. b", "C. c", "D. d"],
                            "stem": "原题干",
                            "answer_lines": ["1. C"],
                            "note_lines": ["1. 原解析，包含依据与排除。"],
                        }
                    ],
                }
            ],
        }
        ok = app_mod.replace_question_from_payload(
            paper=paper,
            section_index=0,
            question_index=0,
            question_lines=["1. 新题干", "A. aa", "B. bb", "C. cc", "D. dd"],
            answer_map={},
            note_map={},
            assigned_spec=None,
        )
        self.assertTrue(ok)
        question = paper["sections"][0]["questions"][0]
        self.assertEqual(question["answer_lines"], ["1. C"])
        self.assertEqual(question["note_lines"], ["1. 原解析，包含依据与排除。"])

    def test_repair_delivery_fields_in_place_fills_missing_answer_and_note(self):
        paper = {
            "title": "# test",
            "sections": [
                {
                    "name": "判断推理",
                    "material_lines": [],
                    "questions": [
                        {
                            "number": 1,
                            "block_lines": ["1. 某题", "A. a", "B. b", "C. c", "D. d"],
                            "stem": "某题",
                            "answer_lines": [],
                            "note_lines": [],
                        }
                    ],
                }
            ],
        }
        fixed = app_mod.repair_delivery_fields_in_place(paper, question_spec_lookup={})
        self.assertGreaterEqual(fixed, 2)
        question = paper["sections"][0]["questions"][0]
        self.assertRegex(question["answer_lines"][0], r"^1\.\s*[A-D]$")
        self.assertTrue(question["note_lines"])

    def test_build_library_fallback_paper_returns_minimum_valid_paper(self):
        rows: list[dict] = []
        for chapter in ("政治理论", "常识判断", "言语理解与表达", "数量关系", "判断推理", "资料分析"):
            for idx in range(3):
                rows.append(
                    {
                        "chapter": chapter,
                        "stem": f"{chapter}题干{idx}",
                        "options": {"A": "a", "B": "b", "C": "c", "D": "d"},
                        "answer": "A",
                        "analysis": "依据题干关键信息可确定正确项，其余选项条件不符。",
                        "knowledge_points": [f"{chapter}考点"],
                    }
                )
        blueprint = [
            {"name": "政治理论", "count": 2},
            {"name": "常识判断", "count": 2},
            {"name": "言语理解与表达", "count": 3},
            {"name": "数量关系", "count": 2},
            {"name": "判断推理", "count": 4},
            {"name": "资料分析", "count": 3},
        ]
        with patch.object(app_mod, "read_jsonl", return_value=rows):
            paper = app_mod.build_library_fallback_paper(blueprint=blueprint, question_count=16)
        self.assertIsNotNone(paper)
        self.assertGreaterEqual(len(app_mod.flatten_paper_questions(paper)), 16)


if __name__ == "__main__":
    unittest.main()
