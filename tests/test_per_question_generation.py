import unittest
from unittest.mock import patch

import standalone_app.app as app_mod


GOOD_STEM_BASE = (
    "\u67d0\u5730\u5728\u63a8\u8fdb\u57fa\u5c42\u6cbb\u7406\u6570\u5b57\u5316\u6539\u9769\u8fc7\u7a0b\u4e2d\uff0c"
    "\u56f4\u7ed5\u7fa4\u4f17\u8bc9\u6c42\u529e\u7406\u3001\u90e8\u95e8\u534f\u540c\u8054\u52a8\u548c\u4e8b"
    "\u9879\u95ed\u73af\u53cd\u9988\u5efa\u7acb\u4e86\u7edf\u4e00\u5e73\u53f0\u3002\u6839\u636e\u8be5\u5e73\u53f0"
    "\u8fd0\u884c\u8981\u6c42\uff0c\u5de5\u4f5c\u4eba\u5458\u5728\u63a5\u5230\u7fa4\u4f17\u53cd\u6620\u540e\uff0c"
    "\u5e94\u5f53\u9996\u5148\u6838\u5b9e\u4e8b\u9879\u5f52\u5c5e\u5e76\u5224\u65ad\u540e\u7eed\u5904\u7406"
    "\u65b9\u5f0f\u3002\u95ee\uff1a\u4e0b\u5217\u505a\u6cd5\u6700\u7b26\u5408\u6750\u6599\u8981\u6c42\u7684\u662f"
    "\u4ec0\u4e48\uff1f"
)
SHORT_STEM = "\u6839\u636e\u6750\u6599\u8981\u6c42\uff0c\u4e0b\u5217\u8bf4\u6cd5\u6b63\u786e\u7684\u662f\u4ec0\u4e48\uff1f"
DATA_MATERIAL = (
    "\u67d0\u7701\u56f4\u7ed5\u65b0\u80fd\u6e90\u6c7d\u8f66\u3001\u7eff\u8272\u53d1\u7535\u548c\u50a8\u80fd\u8bbe"
    "\u5907\u4e09\u7c7b\u4ea7\u4e1a\u5efa\u7acb\u5b63\u5ea6\u76d1\u6d4b\u5236\u5ea6\u3002\u7edf\u8ba1\u90e8\u95e8"
    "\u6307\u51fa\uff0c2025\u5e74\u4e00\u5b63\u5ea6\uff0c\u76f8\u5173\u4ea7\u4e1a\u5728\u5de5\u4e1a\u589e\u52a0"
    "\u503c\u3001\u56fa\u5b9a\u8d44\u4ea7\u6295\u8d44\u548c\u51fa\u53e3\u4ea4\u8d27\u503c\u65b9\u9762\u5747\u4fdd"
    "\u6301\u8f83\u5feb\u589e\u957f\uff0c\u5176\u4e2d\u65b0\u80fd\u6e90\u6c7d\u8f66\u4ea7\u4e1a\u53d7\u65b0\u54c1"
    "\u4e0a\u5e02\u4e0e\u53bf\u57df\u5145\u7535\u57fa\u7840\u8bbe\u65bd\u6269\u5bb9\u5e26\u52a8\uff0c\u5e02\u573a"
    "\u9700\u6c42\u660e\u663e\u4e0a\u5347\uff1b\u7eff\u8272\u53d1\u7535\u8bbe\u5907\u4ea7\u4e1a\u5219\u4e3b\u8981"
    "\u53d7\u98ce\u7535\u548c\u5206\u5e03\u5f0f\u5149\u4f0f\u9879\u76ee\u96c6\u4e2d\u5f00\u5de5\u5f71\u54cd\uff0c"
    "\u8bbe\u5907\u8ba2\u5355\u6301\u7eed\u589e\u52a0\uff1b\u50a8\u80fd\u8bbe\u5907\u4ea7\u4e1a\u5728\u7535\u7f51"
    "\u4fa7\u8c03\u5cf0\u9879\u76ee\u548c\u5de5\u5546\u4e1a\u50a8\u80fd\u6539\u9020\u7684\u5171\u540c\u63a8\u52a8"
    "\u4e0b\uff0c\u751f\u4ea7\u548c\u9500\u552e\u589e\u901f\u540c\u6b65\u63d0\u5347\u3002\u4e3a\u4fbf\u4e8e\u6bd4"
    "\u8f83\uff0c\u4e0b\u8868\u5217\u793a\u4e86\u4e09\u7c7b\u4ea7\u4e1a\u4e00\u5b63\u5ea6\u4e3b\u8981\u6307\u6807"
    "\u60c5\u51b5\u3002"
)


def build_good_stem(number: int) -> str:
    return GOOD_STEM_BASE + f"\u3010\u6d4b\u8bd5\u4f53\u4f8b{number}\u3011"


def section_name_for_number(number: int) -> str:
    if number <= 2:
        return "政治理论"
    if number <= 5:
        return "常识判断"
    if number <= 10:
        return "言语理解与表达"
    if number <= 12:
        return "数量关系"
    if number <= 17:
        return "判断推理"
    return "资料分析"


def build_section_stem(section_name: str, number: int, short: bool = False) -> str:
    if short:
        return SHORT_STEM
    if section_name == "言语理解与表达":
        return (
            "文段指出，基层治理数字化建设既要提升办理效率，也要避免技术替代责任判断。"
            "有的地方在引入平台后，把所有复杂事项都简单归并为流程节点，导致群众诉求虽然录入更快，"
            "但真正需要跨部门研判的问题反而更难被识别。填入画横线部分最恰当的一项是："
            f"【测试体例{number}】"
        )
    if section_name == "判断推理":
        return (
            "某部门规定：只有完成业务培训且通过系统考核的工作人员，才能独立受理群众诉求；"
            "凡被认定为复杂事项的，必须提交联审会商。现已知小李可以独立受理诉求，且其经办事项未提交联审会商。"
            "根据上述规则，能够必然推出的是哪一项？"
            f"【测试体例{number}】"
        )
    if section_name == "资料分析":
        return (
            "根据上述统计材料，若要判断新能源车产业在一季度三项指标中的综合表现，下列说法最合理的是哪一项？"
            f"【测试体例{number}】"
        )
    return build_good_stem(number)


def build_question(number: int, stem: str) -> str:
    return (
        f"{number}. {stem}\n"
        "A. 先核实事项归属和办理权限，再按流程分派处理\n"
        "B. 为提高效率直接跳过核实环节，先交由任意窗口受理\n"
        "C. 仅根据群众情绪强烈程度决定是否转入重点督办\n"
        "D. 未经核验就公开答复处理意见并结束流转\n"
    )


def build_answer(number: int) -> str:
    answer = "ABCD"[(number - 1) % 4]
    return f"{number}. {answer}"


def build_note(number: int) -> str:
    section_name = section_name_for_number(number)
    default_tag = (
        "考点ID=10000001；考点=言语理解与表达；"
        "考点路径=言语理解与表达；来源Sheet=全局-基础考点树；"
    )
    language_tag = (
        "考点ID=10846071；考点=中心理解题；"
        "考点路径=言语理解与表达 > 片段阅读 > 中心理解题；来源Sheet=全局-基础考点树；"
    )
    if section_name == "言语理解与表达":
        return (
            f"{number}. {language_tag}考点是语境关系与主旨识别；依据在于文段通过转折呈现“效率提升”与“责任判断”之间的张力；"
            "正确项必须同时照应上下文语义，错项要么只抓效率，要么忽略治理责任。"
        )
    if section_name == "判断推理":
        return (
            f"{number}. {default_tag}考点是必要条件与规则推理；依据在于“只有完成培训且通过考核，才能独立受理”属于必要条件；"
            "正确项应顺着规则链推出，错项则错在把必要条件当充分条件或混淆联审触发条件。"
        )
    if section_name == "资料分析":
        return (
            f"{number}. {default_tag}考点是统计口径比较与材料对应；依据在于共享材料中的指标对比关系；"
            "材料来源=库:data/material_index.json#mock-data-001；"
            "正确项必须同时符合材料数据和问法要求，错项通常错在口径、基期现期或分母选择。"
        )
    return (
        f"{number}. {default_tag}考点是程序合规与权限判断；依据在于材料要求先核实事项归属再决定办理路径；"
        "正确项符合先核实后流转的顺序；错项分别错在跳过核验、错置判断标准或提前终结流程。"
    )


def build_full_markdown(bad_numbers=None):
    bad_numbers = set(bad_numbers or [])
    sections = [
        ("\u653f\u6cbb\u7406\u8bba", 2),
        ("\u5e38\u8bc6\u5224\u65ad", 3),
        ("\u8a00\u8bed\u7406\u89e3\u4e0e\u8868\u8fbe", 5),
        ("\u6570\u91cf\u5173\u7cfb", 2),
        ("\u5224\u65ad\u63a8\u7406", 5),
        ("\u8d44\u6599\u5206\u6790", 3),
    ]
    q = 1
    body = [
        "---",
        "paper_id: mock-test",
        "generated_at: 2026-03-20T15:00:00+08:00",
        "rulebook_version: test-version",
        "generator_mode: locked_rulebook_only",
        "question_count: 20",
        "---",
        "",
        "# 测试模拟卷",
        "",
        "## 题目",
        "",
    ]
    answers = ["## 答案", ""]
    notes = ["## 命题说明", ""]
    for name, count in sections:
        body.append(f"### {name}（{count}题）")
        if name == "\u8d44\u6599\u5206\u6790":
            body.append(DATA_MATERIAL)
            body.append("")
        for _ in range(count):
            stem = build_section_stem(name, q, short=q in bad_numbers)
            body.append(build_question(q, stem))
            body.append("")
            answers.append(build_answer(q))
            notes.append(build_note(q))
            q += 1
        body.append("")
    return "\n".join(body + answers + [""] + notes) + "\n"


def repair_payload(question_number: int) -> str:
    section_name = section_name_for_number(question_number)
    return (
        "## 题目片段\n"
        + build_question(question_number, build_section_stem(section_name, question_number))
        + "\n## 答案片段\n"
        + build_answer(question_number)
        + "\n## 命题说明片段\n"
        + build_note(question_number)
        + "\n"
    )


def section_payload(section_name: str, count: int, start_number: int) -> str:
    lines = ["## 题目片段", f"### {section_name}（{count}题）"]
    if section_name == "资料分析":
        lines.append(DATA_MATERIAL)
        lines.append("")
    for offset in range(count):
        number = start_number + offset
        lines.append(build_question(number, build_section_stem(section_name, number)))
        lines.append("")

    answer_lines = ["## 答案片段"]
    note_lines = ["## 命题说明片段"]
    for offset in range(count):
        number = start_number + offset
        answer_lines.append(build_answer(number))
        note_lines.append(build_note(number))

    return "\n".join(lines + answer_lines + note_lines) + "\n"


class PerQuestionRepairTests(unittest.TestCase):
    def test_section_generation_prompt_uses_parseable_fragment_headers(self):
        prompt = app_mod.build_section_generation_prompt(
            focus=None,
            paper_id="mock-test",
            generated_at="2026-03-23T10:00:00+08:00",
            rulebook_version="test-version",
            section_name="资料分析",
            section_count=3,
            start_number=18,
        )

        self.assertIn("## 题目片段", prompt)
        self.assertIn("## 答案片段", prompt)
        self.assertIn("## 命题说明片段", prompt)
        self.assertIn("### 资料分析（3题）", prompt)
        self.assertNotIn("????", prompt)

    def test_evaluate_paper_questions_rejects_placeholder_options_and_notes(self):
        paper = {
            "title": "# 测试卷",
            "sections": [
                {
                    "name": "判断推理",
                    "material_lines": [],
                    "questions": [
                        {
                            "number": 1,
                            "block_lines": [
                                "1. 某地围绕基层治理数字化转型建立统一平台，要求工作人员依据事项归属和办理权限作出处理决定。问：下列做法最符合要求的是哪一项？",
                                "A. 方案一",
                                "B. 方案二",
                                "C. 方案三",
                                "D. 方案四",
                            ],
                            "stem": "某地围绕基层治理数字化转型建立统一平台，要求工作人员依据事项归属和办理权限作出处理决定。问：下列做法最符合要求的是哪一项？",
                            "answer_lines": ["1. A"],
                            "note_lines": ["1. 待补充"],
                        }
                    ],
                }
            ],
        }

        with patch.object(
            app_mod,
            "build_source_stem_index",
            return_value=[
                {
                    "normalized": "完全无关的原题样本用于原创性比对",
                    "stem": "完全无关的原题样本用于原创性比对",
                    "source_ref": "dummy",
                }
            ],
        ):
            issues = app_mod.evaluate_paper_questions(paper)

        joined = " | ".join(issues[(0, 0)])
        self.assertIn("选项", joined)
        self.assertIn("命题说明", joined)

    def test_evaluate_paper_questions_allows_normal_note_text_with_hulue(self):
        paper = {
            "title": "# 测试卷",
            "sections": [
                {
                    "name": "言语理解与表达",
                    "material_lines": [],
                    "questions": [
                        {
                            "number": 6,
                            "block_lines": [
                                f"6. {build_section_stem('言语理解与表达', 6)}",
                                "A. 只强调提高办理速度，不再区分事项复杂程度。",
                                "B. 同时兼顾平台效率提升与责任判断边界，避免忽略治理责任。",
                                "C. 将所有问题统一归并为同一流程节点，减少人工判断。",
                                "D. 先对外答复处理结论，再补做事项核验和分派。",
                            ],
                            "stem": build_section_stem("言语理解与表达", 6),
                            "answer_lines": ["6. B"],
                            "note_lines": [build_note(6)],
                        }
                    ],
                }
            ],
        }

        with patch.object(
            app_mod,
            "build_source_stem_index",
            return_value=[
                {
                    "normalized": "完全无关的原题样本用于原创性比对",
                    "stem": "完全无关的原题样本用于原创性比对",
                    "source_ref": "dummy",
                }
            ],
        ):
            issues = app_mod.evaluate_paper_questions(paper)

        joined = " | ".join(issues.get((0, 0), []))
        self.assertNotIn("占位内容", joined)

    def test_evaluate_paper_questions_rejects_module_mismatch(self):
        paper = {
            "title": "# 测试卷",
            "sections": [
                {
                    "name": "判断推理",
                    "material_lines": [],
                    "questions": [
                        {
                            "number": 13,
                            "block_lines": [
                                "13. 以下关于“可持续发展”概念的阐述，哪一项最符合联合国相关报告对其核心要素的描述？",
                                "A. 以提高当前经济总量为首要目标，兼顾环境治理",
                                "B. 以保证资源永续利用、促进公平正义和提升生活质量为基本要求",
                                "C. 以实现技术创新驱动为唯一手段，忽视社会公平因素",
                                "D. 以降低短期成本为主要考量，强调快速增长模式",
                            ],
                            "stem": "以下关于“可持续发展”概念的阐述，哪一项最符合联合国相关报告对其核心要素的描述？",
                            "answer_lines": ["13. B"],
                            "note_lines": [
                                "13. 考点是概念辨析；依据在于选项B同时覆盖经济、社会与环境维度；正确项完整，错项分别遗漏关键维度。"
                            ],
                        }
                    ],
                }
            ],
        }

        with patch.object(
            app_mod,
            "build_source_stem_index",
            return_value=[
                {
                    "normalized": "完全无关的原题样本用于原创性比对",
                    "stem": "完全无关的原题样本用于原创性比对",
                    "source_ref": "dummy",
                }
            ],
        ):
            issues = app_mod.evaluate_paper_questions(paper)

        self.assertIn("判断推理模块不匹配", " | ".join(issues[(0, 0)]))

    def test_evaluate_release_quality_allows_soft_issues_only(self):
        paper = app_mod.parse_markdown_paper(build_full_markdown())
        release_errors, release_warnings = app_mod.evaluate_release_quality(
            paper=paper,
            final_issues={
                (2, 0): ["Q6 题目内容与言语理解模块不匹配，缺少语境/主旨/词语或文段信号。"],
                (2, 1): ["Q7 命题说明缺少依据或干扰项排除信息。"],
            },
            expected_question_count=20,
        )

        self.assertEqual(release_errors, [])
        self.assertTrue(release_warnings)
        self.assertIn("软性问题", " | ".join(release_warnings))

    def test_generate_valid_paper_skips_repairs_for_soft_only_issues(self):
        paper = app_mod.parse_markdown_paper(build_full_markdown())
        soft_issues = {
            (2, 0): ["Q6 题目内容与言语理解模块不匹配，缺少语境/主旨/词语或文段信号。"],
            (2, 1): ["Q7 命题说明缺少依据或干扰项排除信息。"],
        }
        rulebook = {
            "version": "test-version",
            "exam_profile": {
                "section_blueprint": [
                    {"name": "政治理论", "count": 2},
                    {"name": "常识判断", "count": 3},
                    {"name": "言语理解与表达", "count": 5},
                    {"name": "数量关系", "count": 2},
                    {"name": "判断推理", "count": 5},
                    {"name": "资料分析", "count": 3},
                ],
                "default_question_count": 20,
            },
        }

        def fake_call_provider(provider: str, api_key: str, prompt: str, model: str) -> str:
            self.fail(f"soft-only issues should not trigger repair calls: {prompt[:80]}")

        with patch.object(app_mod, "generate_initial_paper_by_sections", return_value=(paper, 20)), \
             patch.object(app_mod, "evaluate_paper_questions", side_effect=[soft_issues, soft_issues, soft_issues]), \
             patch.object(app_mod, "read_json", return_value=rulebook), \
             patch.object(app_mod, "validate_paper", return_value=(True, "ok")), \
             patch.object(app_mod, "call_provider", side_effect=fake_call_provider):
            _paper_path, markdown, validation = app_mod.generate_valid_paper(
                provider="ollama",
                api_key="",
                model="dummy",
                focus=None,
            )

        self.assertIn("question_count: 16", markdown)
        self.assertIn("ok", validation)

    def test_generate_valid_paper_returns_best_effort_output_when_release_errors_persist(self):
        paper = app_mod.parse_markdown_paper(build_full_markdown())
        hard_issues = {
            (2, 3): ["Q9 选项内容重复或近重复。"],
            (4, 4): ["Q17 与卷内其他题过于相似（0.92）。"],
        }
        rulebook = {
            "version": "test-version",
            "exam_profile": {
                "section_blueprint": [
                    {"name": "政治理论", "count": 2},
                    {"name": "常识判断", "count": 3},
                    {"name": "言语理解与表达", "count": 5},
                    {"name": "数量关系", "count": 2},
                    {"name": "判断推理", "count": 5},
                    {"name": "资料分析", "count": 3},
                ],
                "default_question_count": 20,
            },
        }

        with patch.object(app_mod, "generate_initial_paper_by_sections", return_value=(paper, 20)), \
             patch.object(app_mod, "evaluate_paper_questions", side_effect=[hard_issues] * 9), \
             patch.object(app_mod, "read_json", return_value=rulebook), \
             patch.object(app_mod, "call_provider", return_value=""), \
             patch.object(app_mod, "validate_paper", return_value=(False, "bad")):
            paper_path, markdown, validation = app_mod.generate_valid_paper(
                provider="ollama",
                api_key="",
                model="dummy",
                focus=None,
            )

        self.assertTrue(paper_path.exists())
        self.assertIn("question_count: 18", markdown)
        self.assertIn("降级输出", validation)
        self.assertIn("Q9", validation)

    def test_generate_valid_paper_uses_cached_fallback_when_no_new_candidate_exists(self):
        rulebook = {
            "version": "test-version",
            "exam_profile": {
                "section_blueprint": [
                    {"name": "政治理论", "count": 2},
                    {"name": "常识判断", "count": 3},
                    {"name": "言语理解与表达", "count": 5},
                    {"name": "数量关系", "count": 2},
                    {"name": "判断推理", "count": 5},
                    {"name": "资料分析", "count": 3},
                ],
                "default_question_count": 20,
            },
        }
        cached_path = app_mod.OUTPUT_DIR / "cached-fallback-paper.md"
        cached_markdown = build_full_markdown()
        cached_path.write_text(cached_markdown, encoding="utf-8")

        try:
            with patch.object(app_mod, "generate_initial_paper_by_sections", side_effect=RuntimeError("boom")), \
                 patch.object(app_mod, "call_provider", return_value="??"), \
                 patch.object(app_mod, "load_latest_generated_paper", return_value=(cached_path, cached_markdown)), \
                 patch.object(app_mod, "read_json", return_value=rulebook):
                paper_path, markdown, validation = app_mod.generate_valid_paper(
                    provider="ollama",
                    api_key="",
                    model="dummy",
                    focus=None,
                )
        finally:
            if cached_path.exists():
                cached_path.unlink()

        self.assertEqual(paper_path.name, "cached-fallback-paper.md")
        self.assertIn("# 测试模拟卷", markdown)
        self.assertIn("回退到最近成功卷", validation)

    def test_generate_valid_paper_uses_cached_fallback_when_provider_raises_502(self):
        rulebook = {
            "version": "test-version",
            "exam_profile": {
                "section_blueprint": [
                    {"name": "政治理论", "count": 2},
                    {"name": "常识判断", "count": 3},
                    {"name": "言语理解与表达", "count": 5},
                    {"name": "数量关系", "count": 2},
                    {"name": "判断推理", "count": 5},
                    {"name": "资料分析", "count": 3},
                ],
                "default_question_count": 20,
            },
        }
        cached_path = app_mod.OUTPUT_DIR / "cached-502-fallback-paper.md"
        cached_markdown = build_full_markdown()
        cached_path.write_text(cached_markdown, encoding="utf-8")

        try:
            with patch.object(app_mod, "generate_initial_paper_by_sections", side_effect=RuntimeError("section failed")), \
                 patch.object(app_mod, "call_provider", side_effect=RuntimeError("Ollama Cloud 连续重试 2 次后仍失败，HTTP 502。")), \
                 patch.object(app_mod, "load_latest_generated_paper", return_value=(cached_path, cached_markdown)), \
                 patch.object(app_mod, "read_json", return_value=rulebook):
                paper_path, markdown, validation = app_mod.generate_valid_paper(
                    provider="ollama",
                    api_key="",
                    model="dummy",
                    focus=None,
                )
        finally:
            if cached_path.exists():
                cached_path.unlink()

        self.assertEqual(paper_path.name, "cached-502-fallback-paper.md")
        self.assertIn("question_count: 20", markdown)
        self.assertIn("回退到最近成功卷", validation)
        self.assertIn("HTTP 502", validation)

    def test_generate_valid_paper_uses_cached_fallback_when_section_provider_raises_500(self):
        rulebook = {
            "version": "test-version",
            "exam_profile": {
                "section_blueprint": [
                    {"name": "鏀挎不鐞嗚", "count": 2},
                    {"name": "甯歌瘑鍒ゆ柇", "count": 3},
                    {"name": "瑷€璇悊瑙ｄ笌琛ㄨ揪", "count": 5},
                    {"name": "鏁伴噺鍏崇郴", "count": 2},
                    {"name": "鍒ゆ柇鎺ㄧ悊", "count": 5},
                    {"name": "璧勬枡鍒嗘瀽", "count": 3},
                ],
                "default_question_count": 20,
            },
        }
        cached_path = app_mod.OUTPUT_DIR / "cached-500-fallback-paper.md"
        cached_markdown = build_full_markdown()
        cached_path.write_text(cached_markdown, encoding="utf-8")

        try:
            with patch.object(
                app_mod,
                "build_paper_question_plan",
                return_value=[],
            ), patch.object(
                app_mod,
                "build_question_spec_lookup",
                return_value={},
            ), patch.object(
                app_mod,
                "build_section_question_plan",
                return_value=[
                    {
                        "number": 1,
                        "band": "MID",
                        "section_name": "鏀挎不鐞嗚",
                        "scenario": "基层治理协同",
                        "ask_style": "policy_principle_match",
                        "distractor_rule": "absolute_statement",
                        "authenticity_rule": "policy_evaluation",
                        "knowledge_point_id": "10928464",
                        "knowledge_point_name": "政治理论",
                        "knowledge_source_sheet": "政治理论",
                        "knowledge_path": "政治理论",
                    }
                ],
            ), patch.object(
                app_mod,
                "preflight_section_question_plan",
                return_value=None,
            ), patch.object(
                app_mod,
                "build_section_generation_prompt",
                return_value="Section generation task: 政治理论",
            ), patch.object(
                app_mod,
                "call_provider",
                side_effect=app_mod.ProviderRequestError("ollama", 500, {"error": "Internal Server Error"}),
            ), patch.object(
                app_mod,
                "load_latest_generated_paper",
                return_value=(cached_path, cached_markdown),
            ), patch.object(app_mod, "read_json", return_value=rulebook):
                paper_path, markdown, validation = app_mod.generate_valid_paper(
                    provider="ollama",
                    api_key="",
                    model="dummy",
                    focus=None,
                )
        finally:
            if cached_path.exists():
                cached_path.unlink()

        self.assertEqual(paper_path.name, "cached-500-fallback-paper.md")
        self.assertIn("question_count: 20", markdown)
        self.assertIn("回退到最近成功卷", validation)
        self.assertIn("500", validation)

    def test_generate_valid_paper_best_effort_never_renders_missing_placeholders(self):
        paper = app_mod.parse_markdown_paper(build_full_markdown())
        rows = app_mod.flatten_paper_questions(paper)
        for row in rows[8:]:
            row["question"]["answer_lines"] = []
            row["question"]["note_lines"] = []

        rulebook = {
            "version": "test-version",
            "exam_profile": {
                "section_blueprint": [
                    {"name": "政治理论", "count": 2},
                    {"name": "常识判断", "count": 3},
                    {"name": "言语理解与表达", "count": 5},
                    {"name": "数量关系", "count": 2},
                    {"name": "判断推理", "count": 5},
                    {"name": "资料分析", "count": 3},
                ],
                "default_question_count": 20,
            },
        }
        cached_path = app_mod.OUTPUT_DIR / "cached-best-effort-fallback.md"
        cached_markdown = build_full_markdown().replace(
            "rulebook_version: test-version",
            "rulebook_version: v2026.03.22-1",
        )
        cached_path.write_text(cached_markdown, encoding="utf-8")

        try:
            with patch.object(app_mod, "generate_initial_paper_by_sections", return_value=(paper, 20)), \
                 patch.object(app_mod, "evaluate_paper_questions", return_value={}), \
                 patch.object(app_mod, "read_json", return_value=rulebook), \
                 patch.object(app_mod, "load_latest_generated_paper", return_value=(cached_path, cached_markdown)):
                paper_path, markdown, validation = app_mod.generate_valid_paper(
                    provider="ollama",
                    api_key="",
                    model="dummy",
                    focus=None,
                )
        finally:
            if cached_path.exists():
                cached_path.unlink()

        self.assertTrue(paper_path.exists())
        self.assertNotIn("[MISSING]", markdown)
        self.assertEqual(markdown, cached_markdown)
        self.assertIn("降级输出", markdown)
        self.assertNotIn("通过逐题校验后发布 20 题", markdown)
        self.assertIn("输出题数: 8", validation)

    def test_load_latest_generated_paper_skips_missing_marker_files(self):
        good_path = app_mod.OUTPUT_DIR / "cached-good-paper.md"
        bad_path = app_mod.OUTPUT_DIR / "cached-bad-paper.md"
        good_markdown = build_full_markdown().replace("rulebook_version: test-version", "rulebook_version: v2026.03.22-1")
        bad_markdown = good_markdown.replace("9. C", "9. [MISSING]", 1)
        good_path.write_text(good_markdown, encoding="utf-8")
        bad_path.write_text(bad_markdown, encoding="utf-8")

        try:
            with patch("pathlib.Path.glob", return_value=[bad_path, good_path]):
                result = app_mod.load_latest_generated_paper()
        finally:
            if good_path.exists():
                good_path.unlink()
            if bad_path.exists():
                bad_path.unlink()

        self.assertIsNotNone(result)

    def test_generate_valid_paper_best_effort_never_renders_missing_placeholders(self):
        paper = app_mod.parse_markdown_paper(build_full_markdown())
        rows = app_mod.flatten_paper_questions(paper)
        for row in rows[8:]:
            row["question"]["answer_lines"] = []
            row["question"]["note_lines"] = []

        rulebook = {
            "version": "test-version",
            "exam_profile": {
                "section_blueprint": [
                    {"name": "政治理论", "count": 2},
                    {"name": "常识判断", "count": 3},
                    {"name": "言语理解与表达", "count": 5},
                    {"name": "数量关系", "count": 2},
                    {"name": "判断推理", "count": 5},
                    {"name": "资料分析", "count": 3},
                ],
                "default_question_count": 20,
            },
        }
        cached_path = app_mod.OUTPUT_DIR / "cached-best-effort-fallback.md"
        cached_markdown = build_full_markdown().replace(
            "rulebook_version: test-version",
            "rulebook_version: v2026.03.22-1",
        )
        cached_path.write_text(cached_markdown, encoding="utf-8")

        try:
            with patch.object(app_mod, "generate_initial_paper_by_sections", return_value=(paper, 20)), \
                 patch.object(app_mod, "evaluate_paper_questions", return_value={}), \
                 patch.object(app_mod, "read_json", return_value=rulebook), \
                 patch.object(app_mod, "load_latest_generated_paper", return_value=(cached_path, cached_markdown)):
                paper_path, markdown, validation = app_mod.generate_valid_paper(
                    provider="ollama",
                    api_key="",
                    model="dummy",
                    focus=None,
                )
        finally:
            if cached_path.exists():
                cached_path.unlink()

        self.assertEqual(paper_path, cached_path)
        self.assertNotIn("[MISSING]", markdown)
        self.assertEqual(markdown, cached_markdown)
        self.assertIn("降级输出", validation)
        self.assertIn("回退到最近成功卷", validation)

    def test_load_latest_generated_paper_skips_test_fixture_papers(self):
        prod_path = app_mod.OUTPUT_DIR / "cached-prod-paper.md"
        test_path = app_mod.OUTPUT_DIR / "cached-test-paper.md"
        prod_markdown = build_full_markdown().replace("rulebook_version: test-version", "rulebook_version: v2026.03.22-1")
        test_markdown = build_full_markdown()
        prod_path.write_text(prod_markdown, encoding="utf-8")
        test_path.write_text(test_markdown, encoding="utf-8")

        try:
            with patch("pathlib.Path.glob", return_value=[test_path, prod_path]):
                result = app_mod.load_latest_generated_paper()
        finally:
            if prod_path.exists():
                prod_path.unlink()
            if test_path.exists():
                test_path.unlink()

        self.assertIsNotNone(result)
        paper_path, markdown = result
        self.assertEqual(paper_path.name, "cached-prod-paper.md")
        self.assertIn("rulebook_version: v2026.03.22-1", markdown)

    def test_plan_question_bands_soft_targets_shift_up_one_level(self):
        bands = app_mod.plan_question_bands(20)

        self.assertEqual(len(bands), 20)
        self.assertEqual(bands.count("LOW"), 0)
        self.assertEqual(bands.count("MID"), 6)
        self.assertEqual(bands.count("HIGH"), 11)
        self.assertEqual(bands.count("VERY_HIGH"), 3)

    def test_plan_question_bands_non_20_count_is_normalized(self):
        bands = app_mod.plan_question_bands(17)

        self.assertEqual(len(bands), 17)
        self.assertEqual(sum(band in {"MID", "HIGH", "VERY_HIGH"} for band in bands), 17)
        self.assertGreaterEqual(bands.count("VERY_HIGH"), 2)

    def test_build_question_band_plan_maps_question_numbers(self):
        plan = app_mod.build_question_band_plan(20)

        self.assertEqual(len(plan), 20)
        self.assertEqual(plan[1], "MID")
        self.assertIn(plan[20], {"HIGH", "VERY_HIGH"})

    def test_build_section_question_plan_creates_preflight_specs(self):
        specs = app_mod.build_section_question_plan(
            section_name="常识判断",
            section_count=3,
            start_number=3,
            target_bands=["MID", "HIGH", "VERY_HIGH"],
        )

        self.assertEqual(len(specs), 3)
        self.assertEqual(specs[0]["number"], 3)
        self.assertEqual(specs[0]["band"], "MID")
        self.assertEqual(specs[0]["section_name"], "常识判断")
        self.assertIn("scenario", specs[0])
        self.assertIn("ask_style", specs[0])
        self.assertIn("distractor_rule", specs[0])
        self.assertIn("ability_target", specs[0])
        self.assertIn("boundary_rule", specs[0])
        self.assertEqual(len(specs[0]["strong_distractors"]), 2)
        self.assertIn("uniqueness_rule", specs[0])
        self.assertIn("explanation_focus", specs[0])

    def test_preflight_section_question_plan_rejects_direct_definition_shapes(self):
        with self.assertRaises(RuntimeError):
            app_mod.preflight_section_question_plan(
                section_name="常识判断",
                specs=[
                    {
                        "number": 3,
                        "band": "HIGH",
                        "section_name": "常识判断",
                        "scenario": "公共资源配置",
                        "ask_style": "direct_definition_match",
                        "distractor_rule": "self_disclosing_labels",
                        "authenticity_rule": "policy_evaluation",
                        "ability_target": "concept_boundary",
                        "boundary_rule": "facts_only",
                        "strong_distractors": ["scope_swap", "result_swap"],
                        "uniqueness_rule": "eliminate strongest distractor explicitly",
                        "explanation_focus": "closest wrong option",
                    }
                ],
            )

    def test_preflight_section_question_plan_rejects_missing_uniqueness_proof(self):
        with self.assertRaises(RuntimeError):
            app_mod.preflight_section_question_plan(
                section_name="判断推理",
                specs=[
                    {
                        "number": 13,
                        "band": "HIGH",
                        "section_name": "判断推理",
                        "question_family": "rule_based_inference",
                        "scenario": "基层治理事项分流",
                        "ask_style": "best_inference",
                        "distractor_rule": "one_condition_off",
                        "authenticity_rule": "real_workplace_logic",
                        "ability_target": "condition_chain_inference",
                        "boundary_rule": "facts_only",
                        "strong_distractors": ["scope_swap", "condition_missing"],
                        "uniqueness_rule": "",
                        "explanation_focus": "closest wrong option",
                    }
                ],
            )

    def test_section_generation_prompt_includes_band_targets(self):
        prompt = app_mod.build_section_generation_prompt(
            focus=None,
            paper_id="mock-test",
            generated_at="2026-03-23T10:00:00+08:00",
            rulebook_version="test-version",
            section_name="判断推理",
            section_count=2,
            start_number=13,
            target_bands=["HIGH", "VERY_HIGH"],
            question_specs=[
                {
                    "number": 13,
                    "band": "HIGH",
                    "section_name": "判断推理",
                    "question_family": "rule_based_inference",
                    "scenario": "基层治理事项分流",
                    "ask_style": "best_inference",
                    "distractor_rule": "one_condition_off",
                    "authenticity_rule": "real_workplace_logic",
                    "ability_target": "condition_chain_inference",
                    "boundary_rule": "facts_only_no_conclusion",
                    "strong_distractors": ["scope_swap", "condition_missing"],
                    "uniqueness_rule": "prove why the closest wrong option fails on one decisive condition",
                    "explanation_focus": "closest wrong option",
                },
                {
                    "number": 14,
                    "band": "VERY_HIGH",
                    "section_name": "判断推理",
                    "question_family": "argument_evaluation",
                    "scenario": "招投标合规审查",
                    "ask_style": "best_evaluation",
                    "distractor_rule": "same_domain_close_errors",
                    "authenticity_rule": "real_workplace_logic",
                    "ability_target": "multi_constraint_evaluation",
                    "boundary_rule": "facts_only_no_conclusion",
                    "strong_distractors": ["wrong_priority_rule", "scope_swap"],
                    "uniqueness_rule": "prove why the closest wrong option fails on one decisive condition",
                    "explanation_focus": "closest wrong option",
                },
            ],
        )

        self.assertIn("Target bands", prompt)
        self.assertIn("HIGH", prompt)
        self.assertIn("VERY_HIGH", prompt)
        self.assertIn("Question blueprint", prompt)
        self.assertIn("基层治理事项分流", prompt)
        self.assertIn("one_condition_off", prompt)
        self.assertIn("condition_chain_inference", prompt)
        self.assertIn("closest wrong option", prompt)

    def test_section_generation_prompt_describes_real_difficulty_contract(self):
        prompt = app_mod.build_section_generation_prompt(
            focus=None,
            paper_id="mock-test",
            generated_at="2026-03-23T10:00:00+08:00",
            rulebook_version="test-version",
            section_name="判断推理",
            section_count=2,
            start_number=13,
            target_bands=["HIGH", "VERY_HIGH"],
        )

        self.assertIn("college-educated adult", prompt)
        self.assertIn("2-3 reasoning steps", prompt)
        self.assertIn("3-4 reasoning steps", prompt)
        self.assertIn("elementary-school level", prompt)
        self.assertIn("toy propositions", prompt)
        self.assertIn("concept matching", prompt)
        self.assertIn("self-disclosing", prompt)

    def test_section_generation_prompt_includes_source_anti_repeat_rules(self):
        specs = app_mod.build_section_question_plan(
            section_name="判断推理",
            section_count=2,
            start_number=13,
            target_bands=["HIGH", "VERY_HIGH"],
        )
        prompt = app_mod.build_section_generation_prompt(
            focus=None,
            paper_id="mock-test",
            generated_at="2026-03-23T10:00:00+08:00",
            rulebook_version="test-version",
            section_name="判断推理",
            section_count=2,
            start_number=13,
            target_bands=["HIGH", "VERY_HIGH"],
            question_specs=specs,
        )

        self.assertIn("No two questions in this section may reuse the same core scenario", prompt)
        self.assertIn("near-identical option wording", prompt)
        self.assertIn("anti_repeat=same_core_scenario_and_near_duplicate_shell_forbidden", prompt)

    def test_section_generation_prompt_bans_rule_copy_items_for_policy_sections(self):
        prompt = app_mod.build_section_generation_prompt(
            focus=None,
            paper_id="mock-test",
            generated_at="2026-03-25T10:00:00+08:00",
            rulebook_version="test-version",
            section_name="常识判断",
            section_count=2,
            start_number=3,
            target_bands=["HIGH", "VERY_HIGH"],
        )

        self.assertIn("near-verbatim copy of one clause already written in the stem", prompt)
        self.assertIn("concrete case fact that interacts with the rule", prompt)

    def test_section_generation_prompt_hardens_quantity_closure_rules(self):
        specs = app_mod.build_section_question_plan(
            section_name="数量关系",
            section_count=2,
            start_number=11,
            target_bands=["HIGH", "VERY_HIGH"],
        )
        prompt = app_mod.build_section_generation_prompt(
            focus=None,
            paper_id="mock-test",
            generated_at="2026-03-25T10:00:00+08:00",
            rulebook_version="test-version",
            section_name="数量关系",
            section_count=2,
            start_number=11,
            target_bands=["HIGH", "VERY_HIGH"],
            question_specs=specs,
        )

        self.assertIn("options may not invent extra unannounced schemes", prompt)
        self.assertIn("same cost components and time assumptions", prompt)
        self.assertIn("closed_parameters_same_cost_components_across_options", prompt)
        self.assertIn("derived work quantities and durations must close exactly", prompt)

    def test_section_generation_prompt_hardens_argument_evaluation_rules(self):
        prompt = app_mod.build_section_generation_prompt(
            focus=None,
            paper_id="mock-test",
            generated_at="2026-03-25T10:00:00+08:00",
            rulebook_version="test-version",
            section_name="判断推理",
            section_count=2,
            start_number=13,
            target_bands=["HIGH", "VERY_HIGH"],
        )

        self.assertIn("generic downside statements", prompt)
        self.assertIn("averages or norms as if they were criteria", prompt)
        self.assertIn("key assumption", prompt)

    def test_build_section_question_plan_assigns_subtype_template_contracts(self):
        fake_points = [
            {
                "sheet_name": "言语",
                "point_id": "10000001",
                "point_name": "中心理解题",
                "path": "片段阅读 > 中心理解题",
            }
        ]

        with patch.object(app_mod, "get_allowed_knowledge_points_for_section", return_value=fake_points):
            specs = app_mod.build_section_question_plan(
                section_name="言语理解与表达",
                section_count=3,
                start_number=6,
                target_bands=["HIGH", "HIGH", "VERY_HIGH"],
            )

        subtypes = {spec["question_subtype"] for spec in specs}
        self.assertIn("language_main_idea", subtypes)
        self.assertIn("language_detail_judgment", subtypes)
        self.assertIn("language_fill_blank", subtypes)
        self.assertEqual(specs[0]["material_form"], "official_commentary_passage")
        self.assertEqual(specs[0]["option_punctuation_rule"], "no_terminal_punctuation")
        self.assertGreaterEqual(specs[0]["stem_min_chars"], 100)

    def test_build_section_question_plan_assigns_judgment_quantity_and_data_subtypes(self):
        fake_points = [
            {
                "sheet_name": "判断",
                "point_id": "2001",
                "point_name": "逻辑判断",
                "path": "判断推理 > 逻辑判断",
            }
        ]

        with patch.object(app_mod, "get_allowed_knowledge_points_for_section", return_value=fake_points):
            judgment_specs = app_mod.build_section_question_plan(
                section_name="判断推理",
                section_count=4,
                start_number=13,
                target_bands=["HIGH", "HIGH", "VERY_HIGH", "VERY_HIGH"],
            )
            quantity_specs = app_mod.build_section_question_plan(
                section_name="数量关系",
                section_count=2,
                start_number=11,
                target_bands=["HIGH", "VERY_HIGH"],
            )
            data_specs = app_mod.build_section_question_plan(
                section_name="资料分析",
                section_count=2,
                start_number=18,
                target_bands=["HIGH", "VERY_HIGH"],
            )

        judgment_subtypes = {spec["question_subtype"] for spec in judgment_specs}
        quantity_subtypes = {spec["question_subtype"] for spec in quantity_specs}
        data_subtypes = {spec["question_subtype"] for spec in data_specs}

        self.assertIn("translation_reasoning", judgment_subtypes)
        self.assertTrue({"argument_weaken", "argument_strengthen"} & judgment_subtypes)
        self.assertIn("engineering_optimization", quantity_subtypes)
        self.assertIn("procurement_cost_comparison", quantity_subtypes)
        self.assertIn("data_growth_rate_compare", data_subtypes)
        self.assertIn("official_source_required", {spec["source_class"] for spec in data_specs})

    def test_section_generation_prompt_includes_subtype_template_contracts(self):
        question_specs = [
            {
                "number": 6,
                "band": "HIGH",
                "section_name": "言语理解与表达",
                "question_family": "language_detail_judgment",
                "question_subtype": "language_detail_judgment",
                "scenario": "政务评论短文",
                "ask_style": "detail_judgment",
                "distractor_rule": "scope_shift",
                "authenticity_rule": "official_commentary_voice",
                "construction_order": "point_then_boundary_then_two_strong_distractors_then_answer",
                "stem_rule": "facts_first_no_conclusion_leak",
                "tone_rule": "exam_voice_not_file_voice",
                "anti_repeat_rule": "same_core_scenario_and_near_duplicate_shell_forbidden",
                "ability_target": "detail_point_discrimination",
                "boundary_rule": "language_material_not_rule_clause",
                "strong_distractors": ["scope_shift", "over_inference"],
                "uniqueness_rule": "prove why the closest wrong option misreads one detail",
                "explanation_focus": "closest wrong option",
                "knowledge_point_id": "10000001",
                "knowledge_point_name": "中心理解题",
                "knowledge_source_sheet": "言语",
                "knowledge_path": "片段阅读 > 中心理解题",
                "material_form": "official_commentary_passage",
                "source_class": "template_rewrite_source",
                "stem_min_chars": 150,
                "stem_max_chars": 260,
                "option_min_chars": 18,
                "option_max_chars": 36,
                "option_punctuation_rule": "no_terminal_punctuation",
                "ask_contract": "根据这段文字，下列说法正确/不正确的是",
                "banned_constructions": ["numbered_rule_clauses", "已知条件", "规定①②③"],
            }
        ]

        prompt = app_mod.build_section_generation_prompt(
            focus=None,
            paper_id="mock-test",
            generated_at="2026-03-25T10:00:00+08:00",
            rulebook_version="test-version",
            section_name="言语理解与表达",
            section_count=1,
            start_number=6,
            target_bands=["HIGH"],
            question_specs=question_specs,
        )

        self.assertIn("subtype=language_detail_judgment", prompt)
        self.assertIn("material_form=official_commentary_passage", prompt)
        self.assertIn("source_class=template_rewrite_source", prompt)
        self.assertIn("stem_chars=150-260", prompt)
        self.assertIn("options_chars=18-36", prompt)
        self.assertIn("option_punctuation=no_terminal_punctuation", prompt)
        self.assertIn("numbered_rule_clauses", prompt)

    def test_section_generation_prompt_hardens_rule_and_data_source_contracts(self):
        question_specs = [
            {
                "number": 13,
                "band": "HIGH",
                "section_name": "判断推理",
                "question_family": "rule_based_inference",
                "question_subtype": "translation_reasoning",
                "scenario": "审批流转约束",
                "ask_style": "must_be_true",
                "distractor_rule": "scope_swap",
                "authenticity_rule": "real_workplace_logic",
                "construction_order": "point_then_boundary_then_two_strong_distractors_then_answer",
                "stem_rule": "facts_first_no_conclusion_leak",
                "tone_rule": "exam_voice_not_file_voice",
                "anti_repeat_rule": "same_core_scenario_and_near_duplicate_shell_forbidden",
                "ability_target": "condition_chain_inference",
                "boundary_rule": "facts_only_no_conclusion",
                "strong_distractors": ["scope_swap", "condition_missing"],
                "uniqueness_rule": "prove why the closest wrong option fails on one decisive condition",
                "explanation_focus": "closest wrong option",
                "knowledge_point_id": "2001",
                "knowledge_point_name": "逻辑判断",
                "knowledge_source_sheet": "判断",
                "knowledge_path": "判断推理 > 逻辑判断",
                "material_form": "translated_policy_or_workplace_rules",
                "source_class": "template_rewrite_source",
                "stem_min_chars": 120,
                "stem_max_chars": 200,
                "option_min_chars": 25,
                "option_max_chars": 40,
                "option_punctuation_rule": "no_terminal_punctuation",
                "ask_contract": "以下哪项一定为真 / 以下哪项不能推出",
                "banned_constructions": ["pure_symbolic_letters", "classroom_truth_table", "unlisted_category_inference"],
            },
            {
                "number": 18,
                "band": "HIGH",
                "section_name": "资料分析",
                "question_family": "statistical_comparison",
                "question_subtype": "data_growth_rate_compare",
                "scenario": "财政收入结构",
                "ask_style": "growth_rate_estimate",
                "distractor_rule": "percentage_point_swap",
                "authenticity_rule": "official_statistics_usage",
                "construction_order": "point_then_boundary_then_two_strong_distractors_then_answer",
                "stem_rule": "facts_first_no_conclusion_leak",
                "tone_rule": "exam_voice_not_file_voice",
                "anti_repeat_rule": "same_core_scenario_and_near_duplicate_shell_forbidden",
                "ability_target": "statistical_term_and_base_period_control",
                "boundary_rule": "official_term_usage_only",
                "strong_distractors": ["base_period_swap", "percentage_point_swap"],
                "uniqueness_rule": "prove why the closest wrong option fails on one decisive statistical term or base-period constraint",
                "explanation_focus": "closest wrong option",
                "knowledge_point_id": "3001",
                "knowledge_point_name": "增长率比较",
                "knowledge_source_sheet": "资料",
                "knowledge_path": "资料分析 > 增长率比较",
                "material_form": "official_statistics_table_or_brief",
                "source_class": "official_source_required",
                "stem_min_chars": 20,
                "stem_max_chars": 60,
                "option_min_chars": 2,
                "option_max_chars": 12,
                "option_punctuation_rule": "no_terminal_punctuation",
                "ask_contract": "下列哪项最高 / 最低 / 增长最快",
                "banned_constructions": ["fake_time_series", "nonstandard_statistical_term"],
            },
        ]

        prompt = app_mod.build_section_generation_prompt(
            focus=None,
            paper_id="mock-test",
            generated_at="2026-03-25T10:00:00+08:00",
            rulebook_version="test-version",
            section_name="资料分析",
            section_count=1,
            start_number=18,
            target_bands=["HIGH"],
            question_specs=question_specs,
        )

        self.assertIn("official_source_required", prompt)
        self.assertIn("nonstandard_statistical_term", prompt)
        self.assertIn("Statistical terms must be exact", prompt)

    def test_single_question_repair_prompt_includes_subtype_template_contract(self):
        assigned_spec = {
            "number": 13,
            "question_subtype": "translation_reasoning",
            "knowledge_point_id": "2001",
            "knowledge_point_name": "翻译推理",
            "knowledge_source_sheet": "判断",
            "knowledge_path": "判断推理 > 逻辑判断 > 翻译推理",
            "material_form": "translated_policy_or_workplace_rules",
            "source_class": "template_rewrite_source",
            "stem_min_chars": 120,
            "stem_max_chars": 200,
            "option_min_chars": 25,
            "option_max_chars": 40,
            "option_punctuation_rule": "no_terminal_punctuation",
            "ask_contract": "以下哪项一定为真/不能推出",
            "banned_constructions": ["pure_symbolic_letters", "classroom_truth_table"],
        }

        prompt = app_mod.build_single_question_repair_prompt(
            section_name="判断推理",
            question_number=13,
            question_block=[
                "13. 某部门围绕审批流转设置了若干条件。根据这些条件，下列哪项一定为真？",
                "A. 方案甲",
                "B. 方案乙",
                "C. 方案丙",
                "D. 方案丁",
            ],
            answer_lines=["13. A"],
            note_lines=["13. 依据在于条件链条。"],
            failure_reasons=["题型边界不清"],
            target_band="HIGH",
            assigned_spec=assigned_spec,
        )

        self.assertIn("Subtype: translation_reasoning", prompt)
        self.assertIn("material_form=translated_policy_or_workplace_rules", prompt)
        self.assertIn("ask_contract=以下哪项一定为真/不能推出", prompt)
        self.assertIn("pure_symbolic_letters", prompt)

    def test_single_question_repair_prompt_carries_band_contract(self):
        prompt = app_mod.build_single_question_repair_prompt(
            section_name="判断推理",
            question_number=13,
            question_block=[
                "13. 某单位开展项目复盘，负责人提出三个候选方案，要求在预算、时限和风险三项约束下择优确定最终路径。",
                "A. 方案甲",
                "B. 方案乙",
                "C. 方案丙",
                "D. 方案丁",
            ],
            answer_lines=["13. A"],
            note_lines=["13. 依据条件筛选。"],
            failure_reasons=["题目过于直白。"],
            target_band="VERY_HIGH",
        )

        self.assertIn("Target band: VERY_HIGH", prompt)
        self.assertIn("college-educated adult", prompt)
        self.assertIn("3-4 reasoning steps", prompt)
        self.assertIn("elementary-school level", prompt)

    def test_section_prompt_bans_graphic_reasoning(self):
        prompt = app_mod.build_section_generation_prompt(
            focus=None,
            paper_id="mock-test",
            generated_at="2026-03-23T10:00:00+08:00",
            rulebook_version="test-version",
            section_name="判断推理",
            section_count=2,
            start_number=13,
            target_bands=["HIGH", "VERY_HIGH"],
        )

        self.assertIn("图形推断", prompt)
        self.assertIn("禁止", prompt)

    def test_build_paper_prompt_includes_adult_difficulty_contract(self):
        rulebook = {
            "version": "test-version",
            "exam_profile": {
                "section_blueprint": [
                    {"name": "政治理论", "count": 2},
                    {"name": "常识判断", "count": 3},
                    {"name": "言语理解与表达", "count": 5},
                    {"name": "数量关系", "count": 2},
                    {"name": "判断推理", "count": 5},
                    {"name": "资料分析", "count": 3},
                ],
                "default_question_count": 20,
            },
        }
        memory = {"recent_feedback": ["题目太简单"]}

        with patch.object(app_mod, "read_text", return_value="prompt-notes"), \
             patch.object(app_mod, "read_json", side_effect=[rulebook, memory]), \
             patch.object(app_mod, "read_web_summary", return_value="web-summary"), \
             patch.object(app_mod, "read_applied_rules_summary", return_value="applied-rules"), \
             patch.object(app_mod, "build_paper_rag_context", return_value="paper-rag"), \
             patch.object(app_mod, "build_question_bank_digest", return_value="bank-digest"):
            prompt = app_mod.build_paper_prompt(
                focus="判断推理 资料分析",
                paper_id="mock-paper",
                generated_at="2026-03-23T10:00:00+08:00",
                question_count=20,
            )

        self.assertIn("college-educated adult", prompt)
        self.assertIn("elementary-school level", prompt)
        self.assertIn("MID=6", prompt)
        self.assertIn("HIGH=11", prompt)
        self.assertIn("VERY_HIGH=3", prompt)

    def test_evaluate_paper_questions_rejects_graphic_reasoning(self):
        paper = {
            "title": "# 测试卷",
            "sections": [
                {
                    "name": "判断推理",
                    "material_lines": [],
                    "questions": [
                        {
                            "number": 13,
                            "block_lines": [
                                "13. 根据下图所示的图形旋转规律，选择最符合下一步变化的一项。",
                                "A. 黑色三角形顺时针旋转90度后叠加白色圆点。",
                                "B. 黑色三角形逆时针旋转90度后叠加白色圆点。",
                                "C. 黑色三角形保持不动并交换左右位置。",
                                "D. 黑色三角形翻转后移动到底边中央。",
                            ],
                            "stem": "根据下图所示的图形旋转规律，选择最符合下一步变化的一项。",
                            "answer_lines": ["13. A"],
                            "note_lines": ["13. 考点是图形推断；依据在于图形旋转与叠加规律；正确项符合观察结果，错项偏离旋转方向。"],
                        }
                    ],
                }
            ],
        }

        with patch.object(
            app_mod,
            "build_source_stem_index",
            return_value=[
                {
                    "normalized": "完全无关的原题样本用于原创性比对",
                    "stem": "完全无关的原题样本用于原创性比对",
                    "source_ref": "dummy",
                }
            ],
        ):
            issues = app_mod.evaluate_paper_questions(paper)

        self.assertIn("图形", " | ".join(issues[(0, 0)]))

    def test_evaluate_paper_questions_rejects_rule_restatement_item(self):
        paper = {
            "title": "# 测试卷",
            "sections": [
                {
                    "name": "常识判断",
                    "material_lines": [],
                    "questions": [
                        {
                            "number": 4,
                            "block_lines": [
                                "4. 某行政机关作出行政处罚决定，并已明确告知：企业可以在30日内提起行政复议；在复议期间暂停执行。企业在送达后第10日申请行政复议。此时最符合题干规则的处理是：",
                                "A. 继续执行原处罚，复议结果仅供参考",
                                "B. 暂停执行，待复议决定后再决定是否执行",
                                "C. 直接终止处罚执行",
                                "D. 先重新审查再决定是否送达",
                            ],
                            "stem": "某行政机关作出行政处罚决定，并已明确告知：企业可以在30日内提起行政复议；在复议期间暂停执行。企业在送达后第10日申请行政复议。此时最符合题干规则的处理是：",
                            "answer_lines": ["4. B"],
                            "note_lines": [
                                "4. 考点ID=2001；考点=行政法；考点路径=常识判断 > 法律常识 > 行政法；来源Sheet=常识判断；依据在于题干已经写明“在复议期间暂停执行”，正确项直接对应该规则，错误项排除在于与题干规定不符。"
                            ],
                        }
                    ],
                }
            ],
        }

        fake_catalog = {
            "entries": [
                {
                    "sheet_name": "常识判断",
                    "point_id": "2001",
                    "point_name": "行政法",
                    "path": "常识判断 > 法律常识 > 行政法",
                }
            ],
            "by_id": {
                "2001": {
                    "sheet_name": "常识判断",
                    "point_id": "2001",
                    "point_name": "行政法",
                    "path": "常识判断 > 法律常识 > 行政法",
                }
            },
        }

        with patch.object(
            app_mod,
            "build_source_stem_index",
            return_value=[
                {
                    "normalized": "完全无关的原题样本用于原创性比对",
                    "stem": "完全无关的原题样本用于原创性比对",
                    "source_ref": "dummy",
                }
            ],
        ), patch.object(app_mod, "load_knowledge_point_catalog", return_value=fake_catalog):
            issues = app_mod.evaluate_paper_questions(paper)

        self.assertIn("直接给出执行规则", " | ".join(issues[(0, 0)]))

    def test_evaluate_paper_questions_rejects_language_rule_style_mismatch(self):
        paper = {
            "title": "# 测试卷",
            "sections": [
                {
                    "name": "言语理解与表达",
                    "material_lines": [],
                    "questions": [
                        {
                            "number": 6,
                            "block_lines": [
                                "6. 某市新规规定：①可回收物投放蓝色箱；②有害垃圾投放红色箱；③湿垃圾不得早于9时投放。根据上述规定，下列哪项必然正确？",
                                "A. 小李8时投放湿垃圾一定违规",
                                "B. 小李投放的是有害垃圾",
                                "C. 小李应投放到蓝色箱",
                                "D. 小李的行为符合全部规定",
                            ],
                            "stem": "某市新规规定：①可回收物投放蓝色箱；②有害垃圾投放红色箱；③湿垃圾不得早于9时投放。根据上述规定，下列哪项必然正确？",
                            "answer_lines": ["6. A"],
                            "note_lines": [
                                "6. 考点ID=10000001；考点=中心理解题；考点路径=片段阅读 > 中心理解题；来源Sheet=言语；依据在于题干规则链条。"
                            ],
                        }
                    ],
                }
            ],
        }
        fake_catalog = {
            "entries": [
                {
                    "sheet_name": "言语",
                    "point_id": "10000001",
                    "point_name": "中心理解题",
                    "path": "片段阅读 > 中心理解题",
                }
            ],
            "by_id": {
                "10000001": {
                    "sheet_name": "言语",
                    "point_id": "10000001",
                    "point_name": "中心理解题",
                    "path": "片段阅读 > 中心理解题",
                }
            },
        }

        with patch.object(
            app_mod,
            "build_source_stem_index",
            return_value=[{"normalized": "无关样本", "stem": "无关样本", "source_ref": "dummy"}],
        ), patch.object(app_mod, "load_knowledge_point_catalog", return_value=fake_catalog):
            issues = app_mod.evaluate_paper_questions(paper)

        self.assertIn("规则条文式", " | ".join(issues[(0, 0)]))

    def test_evaluate_paper_questions_rejects_language_option_terminal_punctuation(self):
        paper = {
            "title": "# 测试卷",
            "sections": [
                {
                    "name": "言语理解与表达",
                    "material_lines": [],
                    "questions": [
                        {
                            "number": 7,
                            "block_lines": [
                                "7. 文段指出，平台建设既要提升效率，也要保留复杂问题的人工研判能力。下列说法最准确的是：",
                                "A. 平台建设应兼顾效率与责任判断。",
                                "B. 平台建设只需要提升录入速度。",
                                "C. 技术工具可以完全替代人工判断。",
                                "D. 复杂事项不必进行跨部门研判。",
                            ],
                            "stem": "文段指出，平台建设既要提升效率，也要保留复杂问题的人工研判能力。下列说法最准确的是：",
                            "answer_lines": ["7. A"],
                            "note_lines": [
                                "7. 考点ID=10000001；考点=中心理解题；考点路径=片段阅读 > 中心理解题；来源Sheet=言语；正确项概括文段重点，错误项排除在于片面化。"
                            ],
                        }
                    ],
                }
            ],
        }
        fake_catalog = {
            "entries": [
                {
                    "sheet_name": "言语",
                    "point_id": "10000001",
                    "point_name": "中心理解题",
                    "path": "片段阅读 > 中心理解题",
                }
            ],
            "by_id": {
                "10000001": {
                    "sheet_name": "言语",
                    "point_id": "10000001",
                    "point_name": "中心理解题",
                    "path": "片段阅读 > 中心理解题",
                }
            },
        }

        with patch.object(
            app_mod,
            "build_source_stem_index",
            return_value=[{"normalized": "无关样本", "stem": "无关样本", "source_ref": "dummy"}],
        ), patch.object(app_mod, "load_knowledge_point_catalog", return_value=fake_catalog):
            issues = app_mod.evaluate_paper_questions(paper)

        self.assertIn("末尾不应加句号", " | ".join(issues[(0, 0)]))

    def test_evaluate_paper_questions_rejects_multiple_obvious_language_distractors(self):
        paper = {
            "title": "# 测试卷",
            "sections": [
                {
                    "name": "言语理解与表达",
                    "material_lines": [],
                    "questions": [
                        {
                            "number": 8,
                            "block_lines": [
                                "8. 文段指出，科技治理需要在提升效率的同时守住责任边界，避免把所有复杂事项都简单流程化。下列概括最准确的是：",
                                "A. 平台建设需要兼顾效率与责任边界",
                                "B. 只有技术工具才能解决所有治理问题",
                                "C. 所有复杂事项都应取消人工研判",
                                "D. 治理效率完全不重要",
                            ],
                            "stem": "文段指出，科技治理需要在提升效率的同时守住责任边界，避免把所有复杂事项都简单流程化。下列概括最准确的是：",
                            "answer_lines": ["8. A"],
                            "note_lines": [
                                "8. 考点ID=10000001；考点=中心理解题；考点路径=片段阅读 > 中心理解题；来源Sheet=言语；正确项覆盖双重要求，错误项排除在于绝对化和反向推断。"
                            ],
                        }
                    ],
                }
            ],
        }
        fake_catalog = {
            "entries": [
                {
                    "sheet_name": "言语",
                    "point_id": "10000001",
                    "point_name": "中心理解题",
                    "path": "片段阅读 > 中心理解题",
                }
            ],
            "by_id": {
                "10000001": {
                    "sheet_name": "言语",
                    "point_id": "10000001",
                    "point_name": "中心理解题",
                    "path": "片段阅读 > 中心理解题",
                }
            },
        }

        with patch.object(
            app_mod,
            "build_source_stem_index",
            return_value=[{"normalized": "无关样本", "stem": "无关样本", "source_ref": "dummy"}],
        ), patch.object(app_mod, "load_knowledge_point_catalog", return_value=fake_catalog):
            issues = app_mod.evaluate_paper_questions(paper)

        self.assertIn("两个以上明显弱干扰项", " | ".join(issues[(0, 0)]))

    def test_evaluate_paper_questions_rejects_nonstandard_data_terms_and_indicator_drift(self):
        paper = {
            "title": "# 测试卷",
            "sections": [
                {
                    "name": "资料分析",
                    "material_lines": [
                        "以下为2025年1-3月五省人均社会消费品零售总额及增长率情况。"
                    ],
                    "questions": [
                        {
                            "number": 18,
                            "block_lines": [
                                "18. 与2025年12月相比，2026年3月人均消费额增幅率最高的是哪一省份？",
                                "A. 北京",
                                "B. 上海",
                                "C. 广东",
                                "D. 四川",
                            ],
                            "stem": "与2025年12月相比，2026年3月人均消费额增幅率最高的是哪一省份？",
                            "answer_lines": ["18. D"],
                            "note_lines": [
                                "18. 考点ID=3001；考点=增长率比较；考点路径=资料分析 > 增长率比较；来源Sheet=资料；依据在于比较各省增幅。"
                            ],
                        }
                    ],
                }
            ],
        }
        fake_catalog = {
            "entries": [
                {
                    "sheet_name": "资料",
                    "point_id": "3001",
                    "point_name": "增长率比较",
                    "path": "资料分析 > 增长率比较",
                }
            ],
            "by_id": {
                "3001": {
                    "sheet_name": "资料",
                    "point_id": "3001",
                    "point_name": "增长率比较",
                    "path": "资料分析 > 增长率比较",
                }
            },
        }

        with patch.object(
            app_mod,
            "build_source_stem_index",
            return_value=[{"normalized": "无关样本", "stem": "无关样本", "source_ref": "dummy"}],
        ), patch.object(app_mod, "load_knowledge_point_catalog", return_value=fake_catalog):
            issues = app_mod.evaluate_paper_questions(paper)

        joined = " | ".join(issues[(0, 0)])
        self.assertIn("增幅率", joined)
        self.assertIn("指标名称", joined)

    def test_evaluate_paper_questions_rejects_judgment_knowledge_path_mismatch_for_weaken_item(self):
        paper = {
            "title": "# 测试卷",
            "sections": [
                {
                    "name": "判断推理",
                    "material_lines": [],
                    "questions": [
                        {
                            "number": 14,
                            "block_lines": [
                                "14. 某市计划建设大型城市公园，论证报告称能提升城市形象、吸引游客并带动经济。以下哪项最能削弱上述观点",
                                "A. 去年同期样本口径存在差异",
                                "B. 同类城市类似项目建成后并未提升旅游收入",
                                "C. 项目用地需额外投入",
                                "D. 维护成本可能超预算",
                            ],
                            "stem": "某市计划建设大型城市公园，论证报告称能提升城市形象、吸引游客并带动经济。以下哪项最能削弱上述观点",
                            "answer_lines": ["14. B"],
                            "note_lines": [
                                "14. 考点ID=4001；考点=定义判断；考点路径=判断推理 > 定义判断；来源Sheet=判断；依据在于案例是否符合定义。"
                            ],
                        }
                    ],
                }
            ],
        }
        fake_catalog = {
            "entries": [{"sheet_name": "判断", "point_id": "4001", "point_name": "定义判断", "path": "判断推理 > 定义判断"}],
            "by_id": {"4001": {"sheet_name": "判断", "point_id": "4001", "point_name": "定义判断", "path": "判断推理 > 定义判断"}},
        }

        with patch.object(app_mod, "build_source_stem_index", return_value=[{"normalized": "无关样本", "stem": "无关样本", "source_ref": "dummy"}]), \
             patch.object(app_mod, "load_knowledge_point_catalog", return_value=fake_catalog):
            issues = app_mod.evaluate_paper_questions(paper)

        self.assertIn("问法与考点路径不匹配", " | ".join(issues[(0, 0)]))

    def test_evaluate_paper_questions_rejects_common_knowledge_path_mismatch_for_legal_item(self):
        paper = {
            "title": "# 测试卷",
            "sections": [
                {
                    "name": "常识判断",
                    "material_lines": [],
                    "questions": [
                        {
                            "number": 4,
                            "block_lines": [
                                "4. 食品监管局未依法告知企业违法事实和申辩权利，企业提起行政复议。以下处理最符合法定程序的是？",
                                "A. 维持原处罚",
                                "B. 补充通知后直接执行",
                                "C. 撤销原处罚后重新告知、调查并作出处分",
                                "D. 直接转为行政强制执行",
                            ],
                            "stem": "食品监管局未依法告知企业违法事实和申辩权利，企业提起行政复议。以下处理最符合法定程序的是？",
                            "answer_lines": ["4. C"],
                            "note_lines": [
                                "4. 考点ID=5001；考点=经济常识；考点路径=常识判断 > 经济常识；来源Sheet=常识判断；依据在于市场运行规则。"
                            ],
                        }
                    ],
                }
            ],
        }
        fake_catalog = {
            "entries": [{"sheet_name": "常识判断", "point_id": "5001", "point_name": "经济常识", "path": "常识判断 > 经济常识"}],
            "by_id": {"5001": {"sheet_name": "常识判断", "point_id": "5001", "point_name": "经济常识", "path": "常识判断 > 经济常识"}},
        }

        with patch.object(app_mod, "build_source_stem_index", return_value=[{"normalized": "无关样本", "stem": "无关样本", "source_ref": "dummy"}]), \
             patch.object(app_mod, "load_knowledge_point_catalog", return_value=fake_catalog):
            issues = app_mod.evaluate_paper_questions(paper)

        self.assertIn("法律程序题错挂到经济类考点", " | ".join(issues[(0, 0)]))

    def test_evaluate_paper_questions_rejects_quantity_knowledge_path_mismatch_for_procurement_item(self):
        paper = {
            "title": "# 测试卷",
            "sections": [
                {
                    "name": "数量关系",
                    "material_lines": [],
                    "questions": [
                        {
                            "number": 12,
                            "block_lines": [
                                "12. 某公司采购5000件零部件，比较四种采购方案的总费用。请问哪一种方案费用最低？",
                                "A. 方案A",
                                "B. 方案B",
                                "C. 方案C",
                                "D. 方案D",
                            ],
                            "stem": "某公司采购5000件零部件，比较四种采购方案的总费用。请问哪一种方案费用最低？",
                            "answer_lines": ["12. A"],
                            "note_lines": [
                                "12. 考点ID=6001；考点=数字推理；考点路径=数量关系 > 数字推理；来源Sheet=数量；依据在于数字规律。"
                            ],
                        }
                    ],
                }
            ],
        }
        fake_catalog = {
            "entries": [{"sheet_name": "数量", "point_id": "6001", "point_name": "数字推理", "path": "数量关系 > 数字推理"}],
            "by_id": {"6001": {"sheet_name": "数量", "point_id": "6001", "point_name": "数字推理", "path": "数量关系 > 数字推理"}},
        }

        with patch.object(app_mod, "build_source_stem_index", return_value=[{"normalized": "无关样本", "stem": "无关样本", "source_ref": "dummy"}]), \
             patch.object(app_mod, "load_knowledge_point_catalog", return_value=fake_catalog):
            issues = app_mod.evaluate_paper_questions(paper)

        self.assertIn("采购费用比较题错挂到数字推理", " | ".join(issues[(0, 0)]))

    def test_evaluate_paper_questions_rejects_answer_note_conflict(self):
        paper = {
            "title": "# 测试卷",
            "sections": [
                {
                    "name": "判断推理",
                    "material_lines": [],
                    "questions": [
                        {
                            "number": 17,
                            "block_lines": [
                                "17. 项目Y已完成并提交报告，但缺少改进建议部分。以下哪项不能推出？",
                                "A. 项目Y仍具备下一年度项目资格",
                                "B. 项目Y的报告不符合完整性要求",
                                "C. 项目Y可能因报告不完整而被追责",
                                "D. 项目Y已满足提交报告的时间要求",
                            ],
                            "stem": "项目Y已完成并提交报告，但缺少改进建议部分。以下哪项不能推出？",
                            "answer_lines": ["17. A"],
                            "note_lines": [
                                "17. 考点ID=2001；考点=逻辑判断；考点路径=判断推理 > 逻辑判断；来源Sheet=判断；但未说明是否会导致资格取消，只能推出报告不完整。选项B正确。"
                            ],
                        }
                    ],
                }
            ],
        }
        fake_catalog = {
            "entries": [{"sheet_name": "判断", "point_id": "2001", "point_name": "逻辑判断", "path": "判断推理 > 逻辑判断"}],
            "by_id": {"2001": {"sheet_name": "判断", "point_id": "2001", "point_name": "逻辑判断", "path": "判断推理 > 逻辑判断"}},
        }

        with patch.object(app_mod, "build_source_stem_index", return_value=[{"normalized": "无关样本", "stem": "无关样本", "source_ref": "dummy"}]), \
             patch.object(app_mod, "load_knowledge_point_catalog", return_value=fake_catalog):
            issues = app_mod.evaluate_paper_questions(paper)

        self.assertIn("答案与命题说明冲突", " | ".join(issues[(0, 0)]))

    def test_evaluate_paper_questions_rejects_data_question_without_shared_material_support(self):
        paper = {
            "title": "# 测试卷",
            "sections": [
                {
                    "name": "资料分析",
                    "material_lines": [],
                    "questions": [
                        {
                            "number": 18,
                            "block_lines": [
                                "18. 根据上述材料，2025年第二季度，哪一地区的增值税增长率最高？",
                                "A. 地区A",
                                "B. 地区B",
                                "C. 地区C",
                                "D. 三地区相同",
                            ],
                            "stem": "根据上述材料，2025年第二季度，哪一地区的增值税增长率最高？",
                            "answer_lines": ["18. A"],
                            "note_lines": [
                                "18. 考点ID=3001；考点=增长率比较；考点路径=资料分析 > 增长率比较；来源Sheet=资料；依据在于比较三地增值税增速。"
                            ],
                        }
                    ],
                }
            ],
        }
        fake_catalog = {
            "entries": [{"sheet_name": "资料", "point_id": "3001", "point_name": "增长率比较", "path": "资料分析 > 增长率比较"}],
            "by_id": {"3001": {"sheet_name": "资料", "point_id": "3001", "point_name": "增长率比较", "path": "资料分析 > 增长率比较"}},
        }

        with patch.object(app_mod, "build_source_stem_index", return_value=[{"normalized": "无关样本", "stem": "无关样本", "source_ref": "dummy"}]), \
             patch.object(app_mod, "load_knowledge_point_catalog", return_value=fake_catalog):
            issues = app_mod.evaluate_paper_questions(paper)

        self.assertIn("引用“上述材料”但共享材料不足", " | ".join(issues[(0, 0)]))

    def test_evaluate_paper_questions_rejects_engineering_schedule_explanation_conflict(self):
        paper = {
            "title": "# 测试卷",
            "sections": [
                {
                    "name": "数量关系",
                    "material_lines": [],
                    "questions": [
                        {
                            "number": 11,
                            "block_lines": [
                                "11. 某工程包括三项子任务：①土建工程需10天；②电气安装需8天，必须在土建完成后才能开始；③调试验收需5天，可在电气安装的最后两天同步进行。若采用最优安排，总工期最短为多少天？",
                                "A. 18天",
                                "B. 20天",
                                "C. 22天",
                                "D. 24天",
                            ],
                            "stem": "某工程包括三项子任务：①土建工程需10天；②电气安装需8天，必须在土建完成后才能开始；③调试验收需5天，可在电气安装的最后两天同步进行。若采用最优安排，总工期最短为多少天？",
                            "answer_lines": ["11. B"],
                            "note_lines": [
                                "11. 考点ID=10000002；考点=数量关系；考点路径=数量关系；来源Sheet=全局-基础考点树；第9-16天电气（第9天开始，可部分并行）；第15-20天调试（与电气最后两天同步）。总工期20天。正确项B。"
                            ],
                        }
                    ],
                }
            ],
        }
        fake_catalog = {
            "entries": [{"sheet_name": "全局-基础考点树", "point_id": "10000002", "point_name": "数量关系", "path": "数量关系"}],
            "by_id": {"10000002": {"sheet_name": "全局-基础考点树", "point_id": "10000002", "point_name": "数量关系", "path": "数量关系"}},
        }

        with patch.object(app_mod, "build_source_stem_index", return_value=[{"normalized": "无关样本", "stem": "无关样本", "source_ref": "dummy"}]), \
             patch.object(app_mod, "load_knowledge_point_catalog", return_value=fake_catalog):
            issues = app_mod.evaluate_paper_questions(paper)

        self.assertIn("工序先后关系与命题说明冲突", " | ".join(issues[(0, 0)]))

    def test_evaluate_paper_questions_rejects_toy_symbolic_reasoning(self):
        paper = {
            "title": "# 测试卷",
            "sections": [
                {
                    "name": "判断推理",
                    "material_lines": [],
                    "questions": [
                        {
                            "number": 13,
                            "block_lines": [
                                "13. 已知命题A与命题B的关系如下：若A为真，则B必为真；若B为真，则A必为真。请问下列关于A、B关系的表述，哪一项是正确的？",
                                "A. A是B的充分条件，但不是必要条件",
                                "B. A是B的必要条件，但不是充分条件",
                                "C. A既是B的充分条件又是必要条件",
                                "D. A既不是B的充分条件也不是必要条件",
                            ],
                            "stem": "已知命题A与命题B的关系如下：若A为真，则B必为真；若B为真，则A必为真。请问下列关于A、B关系的表述，哪一项是正确的？",
                            "answer_lines": ["13. C"],
                            "note_lines": ["13. 考点是充分必要条件；依据是双向推出；正确项为C，其他选项遗漏其中一个方向。"],
                        }
                    ],
                }
            ],
        }

        with patch.object(
            app_mod,
            "build_source_stem_index",
            return_value=[
                {
                    "normalized": "完全无关的原题样本用于原创性比对",
                    "stem": "完全无关的原题样本用于原创性比对",
                    "source_ref": "dummy",
                }
            ],
        ):
            issues = app_mod.evaluate_paper_questions(paper)

        self.assertIn("抽象字母逻辑", " | ".join(issues[(0, 0)]))

    def test_evaluate_paper_questions_rejects_definition_matching_weak_item(self):
        paper = {
            "title": "# 测试卷",
            "sections": [
                {
                    "name": "常识判断",
                    "material_lines": [],
                    "questions": [
                        {
                            "number": 5,
                            "block_lines": [
                                "5. 公共资源配置的公平性通常包括机会公平和结果公平两个维度。机会公平强调所有主体在获取资源时的平等机会，结果公平关注最终获得的资源量是否合理。若以下描述中只涉及机会公平而未涉及结果公平，则该描述为：",
                                "A. 只要所有居民都能申请住房补贴，政策就实现了公平。",
                                "B. 低收入家庭获得的补贴比例高于高收入家庭，体现了结果公平。",
                                "C. 政府在税收征收上对不同收入层次实行累进税率，兼顾机会与结果。",
                                "D. 城市公共图书馆对所有人免费开放，且每年新增藏书数量均衡增长。",
                            ],
                            "stem": "公共资源配置的公平性通常包括机会公平和结果公平两个维度。机会公平强调所有主体在获取资源时的平等机会，结果公平关注最终获得的资源量是否合理。若以下描述中只涉及机会公平而未涉及结果公平，则该描述为：",
                            "answer_lines": ["5. A"],
                            "note_lines": ["5. 考点是机会公平与结果公平的区分；依据是A只涉及申请机会，B与C直接包含结果维度，D同时涉及开放与资源增长。"],
                        }
                    ],
                }
            ],
        }

        with patch.object(
            app_mod,
            "build_source_stem_index",
            return_value=[
                {
                    "normalized": "完全无关的原题样本用于原创性比对",
                    "stem": "完全无关的原题样本用于原创性比对",
                    "source_ref": "dummy",
                }
            ],
        ):
            issues = app_mod.evaluate_paper_questions(paper)

        self.assertIn("直给型弱题", " | ".join(issues[(0, 0)]))

    def test_evaluate_paper_questions_rejects_missing_uniqueness_proof(self):
        paper = {
            "title": "# 测试卷",
            "sections": [
                {
                    "name": "判断推理",
                    "material_lines": [],
                    "questions": [
                        {
                            "number": 13,
                            "block_lines": [
                                "13. 某部门规定：只有完成业务培训且通过系统考核的工作人员，才能独立受理群众诉求；凡被认定为复杂事项的，必须提交联审会商。现已知小李可以独立受理诉求，且其经办事项未提交联审会商。根据上述规则，能够必然推出的是哪一项？",
                                "A. 小李完成了业务培训并通过系统考核。",
                                "B. 小李经办事项一定不属于群众诉求。",
                                "C. 所有复杂事项都不能由小李受理。",
                                "D. 只要未联审会商，就一定完成业务培训。",
                            ],
                            "stem": "某部门规定：只有完成业务培训且通过系统考核的工作人员，才能独立受理群众诉求；凡被认定为复杂事项的，必须提交联审会商。现已知小李可以独立受理诉求，且其经办事项未提交联审会商。根据上述规则，能够必然推出的是哪一项？",
                            "answer_lines": ["13. A"],
                            "note_lines": [
                                "13. 考点是必要条件推理；依据在于题干给出了独立受理与培训考核之间的规则链，因此答案选A。"
                            ],
                        }
                    ],
                }
            ],
        }

        with patch.object(
            app_mod,
            "build_source_stem_index",
            return_value=[
                {
                    "normalized": "完全无关的原题样本用于原创性比对",
                    "stem": "完全无关的原题样本用于原创性比对",
                    "source_ref": "dummy",
                }
            ],
        ):
            issues = app_mod.evaluate_paper_questions(paper)

        self.assertIn("唯一性证明", " | ".join(issues[(0, 0)]))

    def test_evaluate_paper_questions_allows_text_only_reasoning(self):
        paper = {
            "title": "# 测试卷",
            "sections": [
                {
                    "name": "判断推理",
                    "material_lines": [],
                    "questions": [
                        {
                            "number": 13,
                            "block_lines": [
                                "13. 某部门规定，只有完成业务培训且通过系统考核的工作人员，才能独立受理群众诉求；凡被认定为复杂事项的，必须提交联审会商。已知小李可以独立受理诉求，且其经办事项未提交联审会商。根据上述规则，能够必然推出的是哪一项？",
                                "A. 小李完成了业务培训并通过系统考核。",
                                "B. 小李经办事项一定不属于群众诉求。",
                                "C. 所有复杂事项都不能由小李受理。",
                                "D. 只要未联审会商，就一定完成业务培训。",
                            ],
                            "stem": "某部门规定，只有完成业务培训且通过系统考核的工作人员，才能独立受理群众诉求；凡被认定为复杂事项的，必须提交联审会商。已知小李可以独立受理诉求，且其经办事项未提交联审会商。根据上述规则，能够必然推出的是哪一项？",
                            "answer_lines": ["13. A"],
                            "note_lines": ["13. 考点是必要条件推理；依据在于“只有……才……”构成必要条件；正确项顺着规则链推出，错项混淆必要与充分。"],
                        }
                    ],
                }
            ],
        }

        with patch.object(
            app_mod,
            "build_source_stem_index",
            return_value=[
                {
                    "normalized": "完全无关的原题样本用于原创性比对",
                    "stem": "完全无关的原题样本用于原创性比对",
                    "source_ref": "dummy",
                }
            ],
        ):
            issues = app_mod.evaluate_paper_questions(paper)

        self.assertNotIn("图形", " | ".join(issues.get((0, 0), [])))

    def test_generate_initial_paper_by_sections_preserves_band_mapping(self):
        blueprint = [
            {"name": "政治理论", "count": 2},
            {"name": "常识判断", "count": 3},
            {"name": "言语理解与表达", "count": 5},
            {"name": "数量关系", "count": 2},
            {"name": "判断推理", "count": 5},
            {"name": "资料分析", "count": 3},
        ]
        section_starts = {}
        cursor = 1
        for item in blueprint:
            section_starts[item["name"]] = cursor
            cursor += int(item["count"])

        def fake_call_provider(provider: str, api_key: str, prompt: str, model: str) -> str:
            for item in blueprint:
                marker = f"Section generation task: {item['name']}"
                if marker in prompt:
                    return section_payload(item["name"], int(item["count"]), section_starts[item["name"]])
            return "# malformed"

        with patch.object(app_mod, "call_provider", side_effect=fake_call_provider):
            paper, candidate_count, band_map = app_mod.generate_initial_paper_by_sections(
                provider="ollama",
                api_key="",
                model="dummy",
                focus=None,
                paper_id="mock-test",
                generated_at="2026-03-23T10:00:00+08:00",
                rulebook_version="test-version",
                blueprint=blueprint,
            )

        self.assertEqual(candidate_count, 20)
        self.assertEqual(len(paper["sections"]), 6)
        self.assertEqual(len(band_map), 20)
        self.assertEqual(band_map[1], "MID")
        self.assertIn(band_map[20], {"HIGH", "VERY_HIGH"})

    def test_generate_initial_paper_by_sections_repairs_bad_section_count_in_place(self):
        prompts = []

        def fake_call_provider(provider: str, api_key: str, prompt: str, model: str) -> str:
            prompts.append(prompt)
            if len(prompts) == 1:
                return section_payload("言语理解与表达", 3, 1)
            return section_payload("言语理解与表达", 2, 1)

        with patch.object(app_mod, "call_provider", side_effect=fake_call_provider):
            paper, candidate_count, _band_map = app_mod.generate_initial_paper_by_sections(
                provider="ollama",
                api_key="",
                model="dummy",
                focus=None,
                paper_id="mock-test",
                generated_at="2026-03-23T10:00:00+08:00",
                rulebook_version="test-version",
                blueprint=[{"name": "言语理解与表达", "count": 2}],
            )

        self.assertEqual(candidate_count, 2)
        self.assertEqual(len(paper["sections"]), 1)
        self.assertEqual(len(paper["sections"][0]["questions"]), 2)
        self.assertEqual(len(prompts), 2)

    def test_generate_initial_paper_by_sections_runs_preflight_before_provider(self):
        def fake_call_provider(provider: str, api_key: str, prompt: str, model: str) -> str:
            self.fail("invalid preplan should fail before calling provider")

        with patch.object(
            app_mod,
            "build_section_question_plan",
            return_value=[
                {
                    "number": 1,
                    "band": "HIGH",
                    "section_name": "常识判断",
                    "scenario": "公共资源配置",
                    "ask_style": "direct_definition_match",
                    "distractor_rule": "self_disclosing_labels",
                    "authenticity_rule": "policy_evaluation",
                }
            ],
        ), patch.object(app_mod, "call_provider", side_effect=fake_call_provider):
            with self.assertRaises(RuntimeError):
                app_mod.generate_initial_paper_by_sections(
                    provider="ollama",
                    api_key="",
                    model="dummy",
                    focus=None,
                    paper_id="mock-test",
                    generated_at="2026-03-23T10:00:00+08:00",
                    rulebook_version="test-version",
                    blueprint=[{"name": "常识判断", "count": 1}],
                )

    def test_generate_initial_paper_by_sections_wraps_provider_request_error(self):
        with patch.object(
            app_mod,
            "build_section_question_plan",
            return_value=[
                {
                    "number": 1,
                    "band": "MID",
                    "section_name": "鏀挎不鐞嗚",
                    "scenario": "基层治理协同",
                    "ask_style": "policy_principle_match",
                    "distractor_rule": "absolute_statement",
                    "authenticity_rule": "policy_evaluation",
                    "knowledge_point_id": "10928464",
                    "knowledge_point_name": "政治理论",
                    "knowledge_source_sheet": "政治理论",
                    "knowledge_path": "政治理论",
                }
            ],
        ), patch.object(
            app_mod,
            "preflight_section_question_plan",
            return_value=None,
        ), patch.object(
            app_mod,
            "build_section_generation_prompt",
            return_value="Section generation task: 政治理论",
        ), patch.object(
            app_mod,
            "call_provider",
            side_effect=app_mod.ProviderRequestError("ollama", 500, {"error": "Internal Server Error"}),
        ):
            with self.assertRaises(RuntimeError) as ctx:
                app_mod.generate_initial_paper_by_sections(
                    provider="ollama",
                    api_key="",
                    model="dummy",
                    focus=None,
                    paper_id="mock-test",
                    generated_at="2026-03-23T10:00:00+08:00",
                    rulebook_version="test-version",
                    blueprint=[{"name": "鏀挎不鐞嗚", "count": 1}],
                )

        self.assertIn("500", str(ctx.exception))

    def test_preflight_section_question_plan_rejects_duplicate_core_scenarios(self):
        specs = [
            {
                "number": 13,
                "band": "HIGH",
                "section_name": "判断推理",
                "question_family": "condition_chain_inference",
                "scenario": "shared-scenario",
                "ask_style": "best_inference",
                "distractor_rule": "one_condition_off",
                "authenticity_rule": "real_workplace_logic",
                "construction_order": "point_then_boundary_then_two_strong_distractors_then_answer",
                "stem_rule": "facts_first_no_conclusion_leak",
                "tone_rule": "exam_voice_not_file_voice",
                "anti_repeat_rule": "same_core_scenario_and_near_duplicate_shell_forbidden",
                "ability_target": "compare conditions",
                "boundary_rule": "do not leak conclusion",
                "strong_distractors": ["range swap", "scope swap"],
                "uniqueness_rule": "closest wrong option fails on one decisive detail",
                "explanation_focus": "why the closest wrong option fails",
            },
            {
                "number": 14,
                "band": "HIGH",
                "section_name": "判断推理",
                "question_family": "condition_chain_inference",
                "scenario": "shared-scenario",
                "ask_style": "best_evaluation",
                "distractor_rule": "same_domain_close_errors",
                "authenticity_rule": "real_workplace_logic",
                "construction_order": "point_then_boundary_then_two_strong_distractors_then_answer",
                "stem_rule": "facts_first_no_conclusion_leak",
                "tone_rule": "exam_voice_not_file_voice",
                "anti_repeat_rule": "same_core_scenario_and_near_duplicate_shell_forbidden",
                "ability_target": "compare conditions",
                "boundary_rule": "do not leak conclusion",
                "strong_distractors": ["range swap", "scope swap"],
                "uniqueness_rule": "closest wrong option fails on one decisive detail",
                "explanation_focus": "why the closest wrong option fails",
            },
        ]

        with self.assertRaises(RuntimeError):
            app_mod.preflight_section_question_plan("判断推理", specs)

    def test_should_refresh_materials_skips_recent_cached_index(self):
        session = {
            "material_dir": "C:/materials",
            "materials_refreshed_at": app_mod.now_iso(),
        }

        with patch.object(app_mod, "has_recent_artifact", return_value=True):
            self.assertFalse(app_mod.should_refresh_materials("C:/materials", session))
            self.assertTrue(app_mod.should_refresh_materials("C:/other", session))

    def test_should_crawl_web_materials_respects_recent_cache_unless_forced(self):
        session = {
            "focus": "判断推理",
            "web_crawled_at": app_mod.now_iso(),
        }

        self.assertFalse(app_mod.should_crawl_web_materials("判断推理", session))
        self.assertTrue(app_mod.should_crawl_web_materials("强制抓取 资料分析", session))

    def test_build_session_learning_content_prefers_cached_then_offline_fast(self):
        session = {
            "provider": "ollama",
            "model": "dummy",
            "focus": "判断推理",
            "learning_generated_at": app_mod.now_iso(),
            "learning_content": "cached plan",
        }

        content, source = app_mod.build_session_learning_content(
            provider="ollama",
            model="dummy",
            focus="判断推理",
            session=session,
        )
        self.assertEqual(content, "cached plan")
        self.assertEqual(source, "cached")

        with patch.object(app_mod, "build_offline_plan", return_value="offline fast plan"):
            content, source = app_mod.build_session_learning_content(
                provider="ollama",
                model="dummy",
                focus="资料分析",
                session={},
            )

        self.assertEqual(content, "offline fast plan")
        self.assertEqual(source, "offline_fast")

    def test_generate_paper_batches_by_section_blueprint(self):
        blueprint = [
            {"name": "政治理论", "count": 2},
            {"name": "常识判断", "count": 3},
            {"name": "言语理解与表达", "count": 5},
            {"name": "数量关系", "count": 2},
            {"name": "判断推理", "count": 5},
            {"name": "资料分析", "count": 3},
        ]
        section_starts = {}
        cursor = 1
        for item in blueprint:
            section_starts[item["name"]] = cursor
            cursor += int(item["count"])

        seen_sections: list[str] = []

        def fake_call_provider(provider: str, api_key: str, prompt: str, model: str) -> str:
            for item in blueprint:
                marker = f"Section generation task: {item['name']}"
                if marker in prompt:
                    seen_sections.append(item["name"])
                    return section_payload(item["name"], int(item["count"]), section_starts[item["name"]])
            return "# malformed"

        rulebook = {
            "version": "test-version",
            "exam_profile": {
                "section_blueprint": blueprint,
                "default_question_count": 20,
            },
        }

        with patch.object(app_mod, "call_provider", side_effect=fake_call_provider), \
             patch.object(app_mod, "read_json", return_value=rulebook), \
             patch.object(app_mod, "validate_paper", return_value=(True, "ok")), \
             patch.object(app_mod, "INTERNAL_DUPLICATE_THRESHOLD", 1.01), \
             patch.object(
                 app_mod,
                 "build_source_stem_index",
                 return_value=[
                     {
                         "normalized": "完全无关的原题样本用于原创性比对",
                         "stem": "完全无关的原题样本用于原创性比对",
                         "source_ref": "dummy",
                     }
                 ],
             ):
            _paper_path, markdown, validation = app_mod.generate_valid_paper(
                provider="ollama",
                api_key="",
                model="dummy",
                focus=None,
            )

        self.assertCountEqual(seen_sections, [item["name"] for item in blueprint])
        positions = [markdown.index(f"### {item['name']}") for item in blueprint]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("question_count: 20", markdown)
        self.assertIn("ok", validation)

    def test_structure_repair_recovers_from_zero_parsed_questions(self):
        malformed_markdown = "# 随便写一段不合格输出\n\n这里没有标准区块，也没有可解析题目。"
        repaired_markdown = build_full_markdown()

        calls = {"count": 0}

        def fake_call_provider(provider: str, api_key: str, prompt: str, model: str) -> str:
            calls["count"] += 1
            if "结构校验" in prompt or "结构不稳定" in prompt:
                return repaired_markdown
            return malformed_markdown

        rulebook = {
            "version": "test-version",
            "exam_profile": {
                "section_blueprint": [
                    {"name": "\u653f\u6cbb\u7406\u8bba", "count": 2},
                    {"name": "\u5e38\u8bc6\u5224\u65ad", "count": 3},
                    {"name": "\u8a00\u8bed\u7406\u89e3\u4e0e\u8868\u8fbe", "count": 5},
                    {"name": "\u6570\u91cf\u5173\u7cfb", "count": 2},
                    {"name": "\u5224\u65ad\u63a8\u7406", "count": 5},
                    {"name": "\u8d44\u6599\u5206\u6790", "count": 3},
                ],
                "default_question_count": 20,
            },
        }

        with patch.object(app_mod, "call_provider", side_effect=fake_call_provider), \
             patch.object(app_mod, "read_json", return_value=rulebook), \
             patch.object(app_mod, "validate_paper", return_value=(True, "ok")), \
             patch.object(app_mod, "INTERNAL_DUPLICATE_THRESHOLD", 1.01), \
             patch.object(
                 app_mod,
                 "build_source_stem_index",
                 return_value=[
                     {
                         "normalized": "\u5b8c\u5168\u65e0\u5173\u7684\u539f\u9898\u6837\u672c\u7528\u4e8e\u539f\u521b\u6027\u6bd4\u5bf9",
                         "stem": "\u5b8c\u5168\u65e0\u5173\u7684\u539f\u9898\u6837\u672c\u7528\u4e8e\u539f\u521b\u6027\u6bd4\u5bf9",
                         "source_ref": "dummy",
                     }
                 ],
             ):
            _paper_path, markdown, validation = app_mod.generate_valid_paper(
                provider="ollama",
                api_key="",
                model="dummy",
                focus=None,
            )

        self.assertGreaterEqual(calls["count"], 2)
        self.assertIn("question_count: 20", markdown)
        self.assertIn("ok", validation)

    def test_publish_when_at_least_16_questions_pass_and_repair_bad_ones(self):
        initial_markdown = build_full_markdown(bad_numbers={14, 15, 16, 17})
        repairs = {
            14: repair_payload(14),
            15: repair_payload(15),
            16: repair_payload(16),
            17: repair_payload(17),
        }
        prompts = []

        def fake_call_provider(provider: str, api_key: str, prompt: str, model: str) -> str:
            prompts.append(prompt)
            if "\u5355\u9053\u9898" in prompt:
                for number, payload in repairs.items():
                    if f"\u9898\u53f7\uff1a{number}" in prompt:
                        return payload
            return initial_markdown

        rulebook = {
            "version": "test-version",
            "exam_profile": {
                "section_blueprint": [
                    {"name": "\u653f\u6cbb\u7406\u8bba", "count": 2},
                    {"name": "\u5e38\u8bc6\u5224\u65ad", "count": 3},
                    {"name": "\u8a00\u8bed\u7406\u89e3\u4e0e\u8868\u8fbe", "count": 5},
                    {"name": "\u6570\u91cf\u5173\u7cfb", "count": 2},
                    {"name": "\u5224\u65ad\u63a8\u7406", "count": 5},
                    {"name": "\u8d44\u6599\u5206\u6790", "count": 3},
                ],
                "default_question_count": 20,
            },
        }

        with patch.object(app_mod, "call_provider", side_effect=fake_call_provider), \
             patch.object(app_mod, "read_json", return_value=rulebook), \
             patch.object(app_mod, "validate_paper", return_value=(True, "ok")), \
             patch.object(app_mod, "INTERNAL_DUPLICATE_THRESHOLD", 1.01), \
             patch.object(
                 app_mod,
                 "build_source_stem_index",
                 return_value=[
                     {
                         "normalized": "\u5b8c\u5168\u65e0\u5173\u7684\u539f\u9898\u6837\u672c\u7528\u4e8e\u539f\u521b\u6027\u6bd4\u5bf9",
                         "stem": "\u5b8c\u5168\u65e0\u5173\u7684\u539f\u9898\u6837\u672c\u7528\u4e8e\u539f\u521b\u6027\u6bd4\u5bf9",
                         "source_ref": "dummy",
                     }
                 ],
             ):
            paper_path, markdown, validation = app_mod.generate_valid_paper(
                provider="ollama",
                api_key="",
                model="dummy",
                focus=None,
            )

        self.assertEqual(paper_path.suffix, ".md")
        self.assertIn("question_count: 20", markdown)
        self.assertIn("发布说明", markdown)
        self.assertIn("发布 20 题", markdown)
        self.assertIn("题号：14", "\n".join(prompts))
        self.assertIn("ok", validation)

    def test_reject_publish_when_some_repairs_fail(self):
        initial_markdown = build_full_markdown(bad_numbers={14, 15, 16, 17})

        def fake_call_provider(provider: str, api_key: str, prompt: str, model: str) -> str:
            if "\u5355\u9053\u9898" in prompt:
                return "## 题目片段\n"
            return initial_markdown

        rulebook = {
            "version": "test-version",
            "exam_profile": {
                "section_blueprint": [
                    {"name": "\u653f\u6cbb\u7406\u8bba", "count": 2},
                    {"name": "\u5e38\u8bc6\u5224\u65ad", "count": 3},
                    {"name": "\u8a00\u8bed\u7406\u89e3\u4e0e\u8868\u8fbe", "count": 5},
                    {"name": "\u6570\u91cf\u5173\u7cfb", "count": 2},
                    {"name": "\u5224\u65ad\u63a8\u7406", "count": 5},
                    {"name": "\u8d44\u6599\u5206\u6790", "count": 3},
                ],
                "default_question_count": 20,
            },
        }

        with patch.object(app_mod, "call_provider", side_effect=fake_call_provider), \
             patch.object(app_mod, "read_json", return_value=rulebook), \
             patch.object(app_mod, "validate_paper", return_value=(True, "ok")), \
             patch.object(app_mod, "INTERNAL_DUPLICATE_THRESHOLD", 1.01), \
             patch.object(
                 app_mod,
                 "build_source_stem_index",
                 return_value=[
                     {
                         "normalized": "\u5b8c\u5168\u65e0\u5173\u7684\u539f\u9898\u6837\u672c\u7528\u4e8e\u539f\u521b\u6027\u6bd4\u5bf9",
                         "stem": "\u5b8c\u5168\u65e0\u5173\u7684\u539f\u9898\u6837\u672c\u7528\u4e8e\u539f\u521b\u6027\u6bd4\u5bf9",
                         "source_ref": "dummy",
                     }
                 ],
             ):
            paper_path, markdown, validation = app_mod.generate_valid_paper(
                provider="ollama",
                api_key="",
                model="dummy",
                focus=None,
            )

        self.assertTrue(paper_path.exists())
        self.assertIn("question_count: 20", markdown)
        self.assertIn("降级输出", validation)


    def test_load_knowledge_point_catalog_includes_global_tree_entries(self):
        catalog = app_mod.load_knowledge_point_catalog(force_reload=True)

        sheets = {entry["sheet_name"] for entry in catalog["entries"]}
        self.assertIn("\u5168\u5c40-\u57fa\u7840\u8003\u70b9\u6811", sheets)

        turning_point = next(
            (
                entry
                for entry in catalog["entries"]
                if entry.get("point_id") == "10846075"
            ),
            None,
        )
        self.assertIsNotNone(turning_point)
        self.assertEqual(turning_point["point_name"], "\u8f6c\u6298")

    def test_build_section_question_plan_assigns_catalog_knowledge_points(self):
        fake_points = [
            {
                "sheet_name": "\u8a00\u8bed",
                "point_id": "10000001",
                "point_name": "\u4e2d\u5fc3\u7406\u89e3\u9898",
                "path": "\u7247\u6bb5\u9605\u8bfb > \u4e2d\u5fc3\u7406\u89e3\u9898",
            },
            {
                "sheet_name": "\u5168\u5c40-\u57fa\u7840\u8003\u70b9\u6811",
                "point_id": "10846071",
                "point_name": "\u8f6c\u6298",
                "path": "\u7247\u6bb5\u9605\u8bfb > \u4e2d\u5fc3\u7406\u89e3\u9898 > \u5173\u8054\u8bcd > \u8f6c\u6298",
            },
        ]

        with patch.object(app_mod, "get_allowed_knowledge_points_for_section", return_value=fake_points):
            specs = app_mod.build_section_question_plan(
                section_name="\u8a00\u8bed\u7406\u89e3\u4e0e\u8868\u8fbe",
                section_count=2,
                start_number=6,
                target_bands=["HIGH", "VERY_HIGH"],
            )

        self.assertEqual(specs[0]["knowledge_point_id"], "10000001")
        self.assertEqual(specs[0]["knowledge_point_name"], "\u4e2d\u5fc3\u7406\u89e3\u9898")
        self.assertEqual(specs[0]["knowledge_source_sheet"], "\u8a00\u8bed")
        self.assertIn("\u7247\u6bb5\u9605\u8bfb", specs[0]["knowledge_path"])
        self.assertEqual(specs[1]["knowledge_point_id"], "10000001")
        self.assertIn("\u4e2d\u5fc3\u7406\u89e3\u9898", specs[1]["knowledge_path"])

    def test_build_section_question_plan_uses_module_specific_global_roots(self):
        politics_spec = app_mod.build_section_question_plan(
            section_name="\u653f\u6cbb\u7406\u8bba",
            section_count=1,
            start_number=1,
            target_bands=["HIGH"],
        )[0]
        quantity_spec = app_mod.build_section_question_plan(
            section_name="\u6570\u91cf\u5173\u7cfb",
            section_count=1,
            start_number=11,
            target_bands=["HIGH"],
        )[0]
        data_spec = app_mod.build_section_question_plan(
            section_name="\u8d44\u6599\u5206\u6790",
            section_count=1,
            start_number=18,
            target_bands=["HIGH"],
        )[0]
        language_spec = app_mod.build_section_question_plan(
            section_name="\u8a00\u8bed\u7406\u89e3\u4e0e\u8868\u8fbe",
            section_count=1,
            start_number=6,
            target_bands=["HIGH"],
        )[0]

        self.assertTrue(politics_spec["knowledge_path"].startswith("\u653f\u6cbb\u7406\u8bba"))
        self.assertTrue(quantity_spec["knowledge_path"].startswith("\u6570\u91cf\u5173\u7cfb"))
        self.assertTrue(data_spec["knowledge_path"].startswith("\u8d44\u6599\u5206\u6790"))
        self.assertTrue(language_spec["knowledge_path"].startswith("\u8a00\u8bed\u7406\u89e3\u4e0e\u8868\u8fbe"))

    def test_section_generation_prompt_includes_catalog_knowledge_contract(self):
        question_specs = [
            {
                "number": 6,
                "band": "HIGH",
                "section_name": "\u8a00\u8bed\u7406\u89e3\u4e0e\u8868\u8fbe",
                "question_family": "passage_main_idea",
                "scenario": "\u6cbb\u7406\u8bc4\u8bba\u77ed\u6587",
                "ask_style": "best_summary",
                "distractor_rule": "partial_summary",
                "authenticity_rule": "natural_editorial_language",
                "construction_order": "point_then_boundary_then_two_strong_distractors_then_answer",
                "stem_rule": "facts_first_no_conclusion_leak",
                "tone_rule": "exam_voice_not_file_voice",
                "anti_repeat_rule": "same_core_scenario_and_near_duplicate_shell_forbidden",
                "ability_target": "main_idea_discrimination",
                "boundary_rule": "only_one_core_claim",
                "strong_distractors": ["partial_summary", "attitude_shift"],
                "uniqueness_rule": "prove_closest_wrong_option_fails_on_scope",
                "explanation_focus": "prove_why_best_summary_beats_closest_partial_summary",
                "knowledge_point_id": "10000001",
                "knowledge_point_name": "\u4e2d\u5fc3\u7406\u89e3\u9898",
                "knowledge_source_sheet": "\u8a00\u8bed",
                "knowledge_path": "\u7247\u6bb5\u9605\u8bfb > \u4e2d\u5fc3\u7406\u89e3\u9898",
            }
        ]

        prompt = app_mod.build_section_generation_prompt(
            focus=None,
            paper_id="mock-test",
            generated_at="2026-03-24T10:00:00+08:00",
            rulebook_version="test-version",
            section_name="\u8a00\u8bed\u7406\u89e3\u4e0e\u8868\u8fbe",
            section_count=1,
            start_number=6,
            target_bands=["HIGH"],
            question_specs=question_specs,
        )

        self.assertIn("knowledge_id=10000001", prompt)
        self.assertIn("knowledge_name=\u4e2d\u5fc3\u7406\u89e3\u9898", prompt)
        self.assertIn("knowledge_sheet=\u8a00\u8bed", prompt)
        self.assertIn("knowledge_path=\u7247\u6bb5\u9605\u8bfb > \u4e2d\u5fc3\u7406\u89e3\u9898", prompt)
        self.assertIn("\u8003\u70b9ID=", prompt)

    def test_evaluate_paper_questions_rejects_out_of_catalog_knowledge_point(self):
        paper = {
            "title": "# \u6d4b\u8bd5\u5377",
            "sections": [
                {
                    "name": "\u8a00\u8bed\u7406\u89e3\u4e0e\u8868\u8fbe",
                    "material_lines": [],
                    "questions": [
                        {
                            "number": 6,
                            "block_lines": [
                                "6. \u6587\u6bb5\u6307\u51fa\uff0c\u57fa\u5c42\u6cbb\u7406\u6570\u5b57\u5316\u5efa\u8bbe\u65e2\u8981\u63d0\u5347\u529e\u7406\u6548\u7387\uff0c\u4e5f\u8981\u907f\u514d\u6280\u672f\u66ff\u4ee3\u8d23\u4efb\u5224\u65ad\u3002\u6709\u7684\u5730\u65b9\u5728\u5f15\u5165\u5e73\u53f0\u540e\uff0c\u628a\u6240\u6709\u590d\u6742\u4e8b\u9879\u90fd\u7b80\u5355\u5f52\u5e76\u4e3a\u6d41\u7a0b\u8282\u70b9\uff0c\u5bfc\u81f4\u7fa4\u4f17\u8bc9\u6c42\u867d\u7136\u5f55\u5165\u66f4\u5feb\uff0c\u4f46\u771f\u6b63\u9700\u8981\u8de8\u90e8\u95e8\u7814\u5224\u7684\u95ee\u9898\u53cd\u800c\u66f4\u96be\u88ab\u8bc6\u522b\u3002\u586b\u5165\u753b\u6a2a\u7ebf\u90e8\u5206\u6700\u606d\u5f53\u7684\u4e00\u9879\u662f\uff1f",
                                "A. \u628a\u6548\u7387\u63d0\u5347\u7b49\u540c\u4e8e\u6cbb\u7406\u8d23\u4efb\u7684\u51cf\u8f7b",
                                "B. \u5e73\u53f0\u5efa\u8bbe\u9700\u8981\u540c\u65f6\u4fdd\u7559\u5bf9\u590d\u6742\u4e8b\u9879\u7684\u8bc6\u522b\u4e0e\u7814\u5224\u80fd\u529b",
                                "C. \u53ea\u8981\u5f55\u5165\u901f\u5ea6\u63d0\u5347\uff0c\u7fa4\u4f17\u8bc9\u6c42\u7684\u95ed\u73af\u8d28\u91cf\u5c31\u4f1a\u540c\u6b65\u63d0\u5347",
                                "D. \u6280\u672f\u5de5\u5177\u5e94\u5f53\u66ff\u4ee3\u4eba\u5de5\u5bf9\u8d23\u4efb\u5f52\u5c5e\u7684\u5224\u65ad",
                            ],
                            "stem": "\u6587\u6bb5\u6307\u51fa\uff0c\u57fa\u5c42\u6cbb\u7406\u6570\u5b57\u5316\u5efa\u8bbe\u65e2\u8981\u63d0\u5347\u529e\u7406\u6548\u7387\uff0c\u4e5f\u8981\u907f\u514d\u6280\u672f\u66ff\u4ee3\u8d23\u4efb\u5224\u65ad\u3002\u6709\u7684\u5730\u65b9\u5728\u5f15\u5165\u5e73\u53f0\u540e\uff0c\u628a\u6240\u6709\u590d\u6742\u4e8b\u9879\u90fd\u7b80\u5355\u5f52\u5e76\u4e3a\u6d41\u7a0b\u8282\u70b9\uff0c\u5bfc\u81f4\u7fa4\u4f17\u8bc9\u6c42\u867d\u7136\u5f55\u5165\u66f4\u5feb\uff0c\u4f46\u771f\u6b63\u9700\u8981\u8de8\u90e8\u95e8\u7814\u5224\u7684\u95ee\u9898\u53cd\u800c\u66f4\u96be\u88ab\u8bc6\u522b\u3002\u586b\u5165\u753b\u6a2a\u7ebf\u90e8\u5206\u6700\u606d\u5f53\u7684\u4e00\u9879\u662f\uff1f",
                            "answer_lines": ["6. B"],
                            "note_lines": [
                                "6. \u8003\u70b9ID=99999999\uff1b\u8003\u70b9=\u8868\u5916\u81ea\u9020\u8003\u70b9\uff1b\u8003\u70b9\u8def\u5f84=\u8868\u5916 > \u81ea\u9020\uff1b\u8003\u70b9\u662f\u4e3b\u65e8\u5224\u65ad\uff1b\u4f9d\u636e\u5728\u4e8e\u6587\u6bb5\u901a\u8fc7\u8f6c\u6298\u5f3a\u8c03\u6548\u7387\u4e0e\u8d23\u4efb\u7684\u5f20\u529b\uff1b\u6b63\u786e\u9879\u80fd\u540c\u65f6\u5bf9\u5e94\u4e24\u7aef\uff0c\u9519\u9879\u6392\u9664\u5219\u9519\u5728\u5c06\u5de5\u5177\u7b49\u540c\u4e8e\u5224\u65ad\u4e3b\u4f53\u3002"
                            ],
                        }
                    ],
                }
            ],
        }

        fake_catalog = {
            "entries": [
                {
                    "sheet_name": "\u8a00\u8bed",
                    "point_id": "10000001",
                    "point_name": "\u4e2d\u5fc3\u7406\u89e3\u9898",
                    "path": "\u7247\u6bb5\u9605\u8bfb > \u4e2d\u5fc3\u7406\u89e3\u9898",
                }
            ]
        }

        with patch.object(
            app_mod,
            "build_source_stem_index",
            return_value=[
                {
                    "normalized": "\u5b8c\u5168\u65e0\u5173\u7684\u539f\u9898\u6837\u672c\u7528\u4e8e\u539f\u521b\u6027\u6bd4\u5bf9",
                    "stem": "\u5b8c\u5168\u65e0\u5173\u7684\u539f\u9898\u6837\u672c\u7528\u4e8e\u539f\u521b\u6027\u6bd4\u5bf9",
                    "source_ref": "dummy",
                }
            ],
        ), patch.object(app_mod, "load_knowledge_point_catalog", return_value=fake_catalog):
            issues = app_mod.evaluate_paper_questions(paper)

        self.assertIn("\u8003\u70b9\u4e0d\u5728\u8003\u70b9\u8868\u767d\u540d\u5355\u5185", " | ".join(issues[(0, 0)]))

    def test_parse_generated_section_fragment_rewrites_model_note_tags_from_assigned_specs(self):
        question_specs = [
            {
                "number": 6,
                "knowledge_point_id": "10000001",
                "knowledge_point_name": "\u4e2d\u5fc3\u7406\u89e3\u9898",
                "knowledge_source_sheet": "\u8a00\u8bed",
                "knowledge_path": "\u7247\u6bb5\u9605\u8bfb > \u4e2d\u5fc3\u7406\u89e3\u9898",
            }
        ]
        fragment = (
            "## \u9898\u76ee\u7247\u6bb5\n"
            "### \u8a00\u8bed\u7406\u89e3\u4e0e\u8868\u8fbe\uff081\u9898\uff09\n"
            + build_question(6, build_section_stem("\u8a00\u8bed\u7406\u89e3\u4e0e\u8868\u8fbe", 6))
            + "\n## \u7b54\u6848\u7247\u6bb5\n"
            + build_answer(6)
            + "\n## \u547d\u9898\u8bf4\u660e\u7247\u6bb5\n"
            + "6. \u8003\u70b9ID=99999999\uff1b\u8003\u70b9=\u8868\u5916\u81ea\u9020\u8003\u70b9\uff1b\u8003\u70b9\u8def\u5f84=\u8868\u5916 > \u81ea\u9020\uff1b\u6761\u4ef6\u5224\u65ad\u662f\u89e3\u9898\u5173\u952e\uff0c\u9519\u9879\u6392\u9664\u5728\u4e8e\u8303\u56f4\u6269\u5f20\u3002\n"
        )

        section = app_mod.parse_generated_section_fragment(
            section_name="\u8a00\u8bed\u7406\u89e3\u4e0e\u8868\u8fbe",
            section_count=1,
            start_number=6,
            fragment=fragment,
            question_specs=question_specs,
        )

        note_text = app_mod.flatten_numbered_entry(section["questions"][0]["note_lines"])
        self.assertIn("\u8003\u70b9ID=10000001", note_text)
        self.assertIn("\u8003\u70b9=\u4e2d\u5fc3\u7406\u89e3\u9898", note_text)
        self.assertIn("\u6765\u6e90Sheet=\u8a00\u8bed", note_text)
        self.assertNotIn("99999999", note_text)
        self.assertIn("\u9519\u9879\u6392\u9664", note_text)

    def test_replace_question_from_payload_rewrites_model_note_tags_from_assigned_spec(self):
        paper = {
            "title": "# \u6d4b\u8bd5\u5377",
            "sections": [
                {
                    "name": "\u8a00\u8bed\u7406\u89e3\u4e0e\u8868\u8fbe",
                    "material_lines": [],
                    "questions": [
                        {
                            "number": 6,
                            "block_lines": build_question(6, build_section_stem("\u8a00\u8bed\u7406\u89e3\u4e0e\u8868\u8fbe", 6)).splitlines(),
                            "stem": build_section_stem("\u8a00\u8bed\u7406\u89e3\u4e0e\u8868\u8fbe", 6),
                            "answer_lines": [build_answer(6)],
                            "note_lines": [build_note(6)],
                        }
                    ],
                }
            ],
        }
        payload = (
            "## \u9898\u76ee\u7247\u6bb5\n"
            + build_question(6, build_section_stem("\u8a00\u8bed\u7406\u89e3\u4e0e\u8868\u8fbe", 6))
            + "\n## \u7b54\u6848\u7247\u6bb5\n"
            + build_answer(6)
            + "\n## \u547d\u9898\u8bf4\u660e\u7247\u6bb5\n"
            + "6. \u8003\u70b9ID=GJ2026_01\uff1b\u8003\u70b9=\u6a21\u578b\u81ea\u9020\u6807\u7b7e\uff1b\u8003\u70b9\u8def\u5f84=\u8868\u5916 > \u81ea\u9020\uff1b\u4f9d\u636e\u5728\u4e8e\u6587\u6bb5\u8f6c\u6298\uff0c\u9519\u9879\u6392\u9664\u5728\u4e8e\u66ff\u6362\u4e86\u4e3b\u65e8\u3002\n"
        )
        question_lines, answer_map, note_map = app_mod.parse_repair_payload(payload)
        assigned_spec = {
            "number": 6,
            "knowledge_point_id": "10000001",
            "knowledge_point_name": "\u4e2d\u5fc3\u7406\u89e3\u9898",
            "knowledge_source_sheet": "\u8a00\u8bed",
            "knowledge_path": "\u7247\u6bb5\u9605\u8bfb > \u4e2d\u5fc3\u7406\u89e3\u9898",
        }

        replaced = app_mod.replace_question_from_payload(
            paper=paper,
            section_index=0,
            question_index=0,
            question_lines=question_lines,
            answer_map=answer_map,
            note_map=note_map,
            assigned_spec=assigned_spec,
        )

        self.assertTrue(replaced)
        note_text = app_mod.flatten_numbered_entry(paper["sections"][0]["questions"][0]["note_lines"])
        self.assertIn("\u8003\u70b9ID=10000001", note_text)
        self.assertNotIn("GJ2026_01", note_text)
        self.assertIn("\u4f9d\u636e\u5728\u4e8e", note_text)

    def test_apply_question_plan_to_paper_rewrites_whole_paper_fallback_note_tags(self):
        markdown = (
            "---\n"
            "paper_id: mock-test\n"
            "generated_at: 2026-03-25T12:00:00+08:00\n"
            "rulebook_version: test-version\n"
            "generator_mode: locked_rulebook_only\n"
            "question_count: 1\n"
            "---\n\n"
            "# \u6d4b\u8bd5\u5377\n\n"
            "## \u9898\u76ee\n\n"
            "### \u8a00\u8bed\u7406\u89e3\u4e0e\u8868\u8fbe\uff081\u9898\uff09\n"
            + build_question(1, build_section_stem("\u8a00\u8bed\u7406\u89e3\u4e0e\u8868\u8fbe", 1))
            + "\n\n## \u7b54\u6848\n\n"
            + build_answer(1)
            + "\n\n## \u547d\u9898\u8bf4\u660e\n\n"
            + "1. \u8003\u70b9ID=J102\uff1b\u8003\u70b9=\u6a21\u578b\u81ea\u9020\uff1b\u8003\u70b9\u8def\u5f84=\u8868\u5916 > \u81ea\u9020\uff1b\u6b63\u786e\u9879\u4f9d\u636e\u6587\u610f\uff0c\u9519\u9879\u6392\u9664\u5728\u4e8e\u8303\u56f4\u504f\u79fb\u3002\n"
        )
        paper = app_mod.parse_markdown_paper(markdown)
        question_specs = [
            {
                "number": 1,
                "knowledge_point_id": "10000001",
                "knowledge_point_name": "\u4e2d\u5fc3\u7406\u89e3\u9898",
                "knowledge_source_sheet": "\u8a00\u8bed",
                "knowledge_path": "\u7247\u6bb5\u9605\u8bfb > \u4e2d\u5fc3\u7406\u89e3\u9898",
            }
        ]

        app_mod.apply_question_plan_to_paper(paper, question_specs)

        note_text = app_mod.flatten_numbered_entry(paper["sections"][0]["questions"][0]["note_lines"])
        self.assertIn("\u8003\u70b9ID=10000001", note_text)
        self.assertIn("\u6765\u6e90Sheet=\u8a00\u8bed", note_text)
        self.assertNotIn("J102", note_text)
        self.assertIn("\u9519\u9879\u6392\u9664", note_text)

    def test_resection_paper_by_blueprint_splits_unsectioned_candidate(self):
        paper = {
            "title": "# \u6d4b\u8bd5\u5377",
            "sections": [
                {
                    "name": "\u672a\u5206\u533a\uff0817\u9898\uff09",
                    "material_lines": [],
                    "questions": [
                        {
                            "number": number,
                            "block_lines": build_question(number, build_section_stem(section_name_for_number(number), number)).splitlines(),
                            "stem": build_section_stem(section_name_for_number(number), number),
                            "answer_lines": [build_answer(number)],
                            "note_lines": [build_note(number)],
                        }
                        for number in range(1, 18)
                    ],
                }
            ],
        }
        blueprint = [
            {"name": "\u653f\u6cbb\u7406\u8bba", "count": 2},
            {"name": "\u5e38\u8bc6\u5224\u65ad", "count": 3},
            {"name": "\u8a00\u8bed\u7406\u89e3\u4e0e\u8868\u8fbe", "count": 5},
            {"name": "\u6570\u91cf\u5173\u7cfb", "count": 2},
            {"name": "\u5224\u65ad\u63a8\u7406", "count": 5},
            {"name": "\u8d44\u6599\u5206\u6790", "count": 3},
        ]

        normalized = app_mod.resection_paper_by_blueprint(paper, blueprint)

        self.assertEqual(
            [section["name"] for section in normalized["sections"]],
            [
                "\u653f\u6cbb\u7406\u8bba",
                "\u5e38\u8bc6\u5224\u65ad",
                "\u8a00\u8bed\u7406\u89e3\u4e0e\u8868\u8fbe",
                "\u6570\u91cf\u5173\u7cfb",
                "\u5224\u65ad\u63a8\u7406",
            ],
        )
        self.assertEqual(
            [len(section["questions"]) for section in normalized["sections"]],
            [2, 3, 5, 2, 5],
        )

    def test_section_generation_prompt_hardens_language_real_exam_rules(self):
        prompt = app_mod.build_section_generation_prompt(
            focus=None,
            paper_id="mock-test",
            generated_at="2026-03-25T10:00:00+08:00",
            rulebook_version="test-version",
            section_name="言语理解与表达",
            section_count=3,
            start_number=6,
            target_bands=["HIGH", "HIGH", "VERY_HIGH"],
        )

        self.assertIn("two explicit discourse cues", prompt)
        self.assertIn("one-sentence toy passages", prompt)
        self.assertIn("two obvious absolute-word distractors", prompt)

    def test_build_section_question_plan_prefers_subtype_specific_knowledge_paths(self):
        language_points = [
            {"sheet_name": "言语", "point_id": "l1", "point_name": "中心理解题", "path": "片段阅读 > 中心理解题"},
            {"sheet_name": "言语", "point_id": "l2", "point_name": "搭配对象", "path": "逻辑填空 > 词的辨析 > 搭配对象"},
        ]
        judgment_points = [
            {"sheet_name": "判断", "point_id": "j1", "point_name": "定义判断", "path": "判断推理 > 定义判断"},
            {"sheet_name": "判断", "point_id": "j2", "point_name": "翻译推理", "path": "判断推理 > 逻辑判断 > 翻译推理"},
            {"sheet_name": "判断", "point_id": "j3", "point_name": "削弱题型", "path": "判断推理 > 逻辑判断 > 削弱题型"},
            {"sheet_name": "判断", "point_id": "j4", "point_name": "加强题型", "path": "判断推理 > 逻辑判断 > 加强题型"},
        ]
        quantity_points = [
            {"sheet_name": "数量", "point_id": "q1", "point_name": "数字推理", "path": "数量关系 > 数字推理"},
            {"sheet_name": "数量", "point_id": "q2", "point_name": "工程问题", "path": "数量关系 > 数学运算 > 工程问题"},
            {"sheet_name": "数量", "point_id": "q3", "point_name": "经济利润问题", "path": "数量关系 > 数学运算 > 经济利润问题"},
        ]

        with patch.object(app_mod, "get_allowed_knowledge_points_for_section", side_effect=[language_points, judgment_points, quantity_points]):
            language_specs = app_mod.build_section_question_plan(
                section_name="言语理解与表达",
                section_count=3,
                start_number=6,
                target_bands=["HIGH", "HIGH", "VERY_HIGH"],
            )
            judgment_specs = app_mod.build_section_question_plan(
                section_name="判断推理",
                section_count=4,
                start_number=13,
                target_bands=["HIGH", "HIGH", "VERY_HIGH", "VERY_HIGH"],
            )
            quantity_specs = app_mod.build_section_question_plan(
                section_name="数量关系",
                section_count=2,
                start_number=11,
                target_bands=["HIGH", "VERY_HIGH"],
            )

        language_by_subtype = {spec["question_subtype"]: spec["knowledge_path"] for spec in language_specs}
        self.assertIn("中心理解题", language_by_subtype["language_main_idea"])
        self.assertIn("中心理解题", language_by_subtype["language_detail_judgment"])
        self.assertIn("搭配对象", language_by_subtype["language_fill_blank"])

        judgment_by_subtype = {spec["question_subtype"]: spec["knowledge_path"] for spec in judgment_specs}
        self.assertIn("翻译推理", judgment_by_subtype["translation_reasoning"])
        self.assertIn("削弱题型", judgment_by_subtype["argument_weaken"])
        self.assertIn("加强题型", judgment_by_subtype["argument_strengthen"])

        quantity_by_subtype = {spec["question_subtype"]: spec["knowledge_path"] for spec in quantity_specs}
        self.assertIn("工程问题", quantity_by_subtype["engineering_optimization"])
        self.assertIn("经济利润问题", quantity_by_subtype["procurement_cost_comparison"])

    def test_find_delivery_gaps_flags_data_material_and_tag_only_notes(self):
        paper = {
            "title": "# 测试卷",
            "sections": [
                {
                    "name": "资料分析",
                    "material_lines": [],
                    "questions": [
                        {
                            "number": 18,
                            "block_lines": [
                                "18. 根据上述材料，下列哪项增长最快？",
                                "A. 税收收入",
                                "B. 非税收入",
                                "C. 转移收入",
                                "D. 其他收入",
                            ],
                            "stem": "根据上述材料，下列哪项增长最快？",
                            "answer_lines": ["18. B"],
                            "note_lines": ["18. 考点ID=10000004；考点=资料分析；考点路径=资料分析；来源Sheet=全局-基础考点树；"],
                        }
                    ],
                }
            ],
        }

        gaps = app_mod.find_delivery_gaps(paper)

        self.assertIn((0, 0), gaps)
        self.assertIn("material", gaps[(0, 0)])
        self.assertIn("note", gaps[(0, 0)])

    def test_generate_valid_paper_uses_cached_fallback_when_best_candidate_has_only_delivery_gaps(self):
        paper = app_mod.parse_markdown_paper(build_full_markdown())
        data_section = next(section for section in paper["sections"] if "资料" in section["name"])
        data_section["material_lines"] = []
        for row in app_mod.flatten_paper_questions(paper):
            number = int(row["question"]["number"])
            row["question"]["note_lines"] = [
                f"{number}. 考点ID=10000001；考点=中心理解题；考点路径=片段阅读 > 中心理解题；来源Sheet=言语；"
            ]

        rulebook = {
            "version": "test-version",
            "exam_profile": {
                "section_blueprint": [
                    {"name": "政治理论", "count": 2},
                    {"name": "常识判断", "count": 3},
                    {"name": "言语理解与表达", "count": 5},
                    {"name": "数量关系", "count": 2},
                    {"name": "判断推理", "count": 5},
                    {"name": "资料分析", "count": 3},
                ],
                "default_question_count": 20,
            },
        }
        cached_path = app_mod.OUTPUT_DIR / "cached-gap-fallback-paper.md"
        cached_markdown = build_full_markdown()
        cached_path.write_text(cached_markdown, encoding="utf-8")

        try:
            with patch.object(app_mod, "generate_initial_paper_by_sections", return_value=(paper, 20)), \
                 patch.object(app_mod, "evaluate_paper_questions", return_value={}), \
                 patch.object(app_mod, "read_json", return_value=rulebook), \
                 patch.object(app_mod, "call_provider", return_value=""), \
                 patch.object(app_mod, "load_latest_generated_paper", return_value=(cached_path, cached_markdown)):
                paper_path, markdown, validation = app_mod.generate_valid_paper(
                    provider="ollama",
                    api_key="",
                    model="dummy",
                    focus=None,
                )
        finally:
            if cached_path.exists():
                cached_path.unlink()

        self.assertEqual(paper_path.name, "cached-gap-fallback-paper.md")
        self.assertIn("question_count: 20", markdown)
        self.assertIn("回退到最近成功卷", validation)
    def test_generate_valid_paper_skips_repairs_for_soft_only_issues(self):
        paper = app_mod.parse_markdown_paper(build_full_markdown())
        soft_issues = {
            (2, 0): ["Q6 题目内容与言语理解模块不匹配，缺少语境/主旨/词语或文段信号。"],
            (2, 1): ["Q7 命题说明缺少依据或干扰项排除信息。"],
        }
        rulebook = {
            "version": "test-version",
            "exam_profile": {
                "section_blueprint": [
                    {"name": "政治理论", "count": 2},
                    {"name": "常识判断", "count": 3},
                    {"name": "言语理解与表达", "count": 5},
                    {"name": "数量关系", "count": 2},
                    {"name": "判断推理", "count": 5},
                    {"name": "资料分析", "count": 3},
                ],
                "default_question_count": 20,
            },
        }

        def fake_call_provider(provider: str, api_key: str, prompt: str, model: str) -> str:
            self.fail(f"soft-only issues should not trigger repair calls: {prompt[:80]}")

        with patch.object(app_mod, "generate_initial_paper_by_sections", return_value=(paper, 20)), \
             patch.object(app_mod, "evaluate_paper_questions", side_effect=[soft_issues, soft_issues, soft_issues]), \
             patch.object(app_mod, "read_json", return_value=rulebook), \
             patch.object(app_mod, "validate_paper", return_value=(True, "ok")), \
             patch.object(app_mod, "call_provider", side_effect=fake_call_provider):
            _paper_path, markdown, validation = app_mod.generate_valid_paper(
                provider="ollama",
                api_key="",
                model="dummy",
                focus=None,
            )

        self.assertIn("question_count: 20", markdown)
        self.assertIn("ok", validation)

    def test_reject_publish_when_some_repairs_fail(self):
        initial_markdown = build_full_markdown(bad_numbers={14, 15, 16, 17})

        def fake_call_provider(provider: str, api_key: str, prompt: str, model: str) -> str:
            if "单道题" in prompt:
                return "## 题目片段\n"
            return initial_markdown

        rulebook = {
            "version": "test-version",
            "exam_profile": {
                "section_blueprint": [
                    {"name": "政治理论", "count": 2},
                    {"name": "常识判断", "count": 3},
                    {"name": "言语理解与表达", "count": 5},
                    {"name": "数量关系", "count": 2},
                    {"name": "判断推理", "count": 5},
                    {"name": "资料分析", "count": 3},
                ],
                "default_question_count": 20,
            },
        }

        with patch.object(app_mod, "call_provider", side_effect=fake_call_provider), \
             patch.object(app_mod, "read_json", return_value=rulebook), \
             patch.object(app_mod, "validate_paper", return_value=(True, "ok")), \
             patch.object(app_mod, "INTERNAL_DUPLICATE_THRESHOLD", 1.01), \
             patch.object(
                 app_mod,
                 "build_source_stem_index",
                 return_value=[
                     {
                         "normalized": "完全无关的原题样本用于原创性比对",
                         "stem": "完全无关的原题样本用于原创性比对",
                         "source_ref": "dummy",
                     }
                 ],
             ):
            paper_path, markdown, validation = app_mod.generate_valid_paper(
                provider="ollama",
                api_key="",
                model="dummy",
                focus=None,
            )

        self.assertTrue(paper_path.exists())
        self.assertIn("question_count: 16", markdown)
        self.assertIn("降级输出", validation)


    def test_evaluate_paper_questions_rejects_policy_stage_regression_answer(self):
        paper = {
            "title": "# 测试卷",
            "sections": [
                {
                    "name": "常识判断",
                    "material_lines": [],
                    "questions": [
                        {
                            "number": 4,
                            "block_lines": [
                                "4. 某社区实行强制垃圾分类，对未按规定分类的居民，社区依次采取口头警告、书面警告，若再违规则处以200元罚款。张女士已两次未将有害垃圾单独投放，社区仅向她发出了两次书面警告。依据上述规定，下一步应如何处理张女士的违规行为？",
                                "A. 对张女士处以一次罚款，因为已累计两次违规。",
                                "B. 再次发出警告，并在下一次违规则处以罚款。",
                                "C. 直接对张女士处以罚款，因为已经违反分类规定。",
                                "D. 免除处罚。",
                            ],
                            "stem": "某社区实行强制垃圾分类，对未按规定分类的居民，社区依次采取口头警告、书面警告，若再违规则处以200元罚款。张女士已两次未将有害垃圾单独投放，社区仅向她发出了两次书面警告。依据上述规定，下一步应如何处理张女士的违规行为？",
                            "answer_lines": ["4. B"],
                            "note_lines": [
                                "4. 考点ID=10000005；考点=常识判断；考点路径=常识判断；来源Sheet=全局-基础考点树；B项正确，因为仍应先再次发出警告，再在下次违规则罚款。"
                            ],
                        }
                    ],
                }
            ],
        }

        issues = app_mod.evaluate_paper_questions(paper)

        self.assertIn((0, 0), issues)
        self.assertTrue(any("处罚阶段" in item or "警告阶段" in item for item in issues[(0, 0)]))

    def test_evaluate_paper_questions_rejects_procurement_option_mutation(self):
        paper = {
            "title": "# 测试卷",
            "sections": [
                {
                    "name": "数量关系",
                    "material_lines": [],
                    "questions": [
                        {
                            "number": 10,
                            "block_lines": [
                                "10. 公司计划采购5000件同型号零件。供应商X、Y、Z提供报价：X单价12元，订购≥3000件享9折，运输费200元；Y单价11元，订购≥4000件享85折，运输费300元；Z单价13元，订购≥2000件享95折，运输费150元。以下哪种采购方案的总费用最低",
                                "A. X全5000",
                                "B. Y全5000折9",
                                "C. Z全5000折85",
                                "D. Y全5000折85",
                            ],
                            "stem": "公司计划采购5000件同型号零件。供应商X、Y、Z提供报价：X单价12元，订购≥3000件享9折，运输费200元；Y单价11元，订购≥4000件享85折，运输费300元；Z单价13元，订购≥2000件享95折，运输费150元。以下哪种采购方案的总费用最低",
                            "answer_lines": ["10. D"],
                            "note_lines": [
                                "10. 考点ID=10000002；考点=数量关系；考点路径=数量关系；来源Sheet=全局-基础考点树；D项费用最低。"
                            ],
                        }
                    ],
                }
            ],
        }

        issues = app_mod.evaluate_paper_questions(paper)

        self.assertIn((0, 0), issues)
        self.assertTrue(any("采购方案选项" in item or "折扣" in item for item in issues[(0, 0)]))

    def test_evaluate_paper_questions_rejects_new_agency_in_must_true_answer(self):
        paper = {
            "title": "# 测试卷",
            "sections": [
                {
                    "name": "判断推理",
                    "material_lines": [],
                    "questions": [
                        {
                            "number": 11,
                            "block_lines": [
                                "11. 基层治理中心对居民诉求进行分类管理。环境卫生类事项必须交由城市环卫局办理；公共安全类事项除非涉及交通，否则交由公共安全分局办理；若事项同时涉及环境卫生和公共安全，则必须同时报送给上述两部门；民政类事项统一交由民政办公室办理。以下哪项一定为真",
                                "A. 涉及环境卫生且涉及公共安全的事项必须由城市环卫局单独处理",
                                "B. 涉及公共安全且涉及交通的事项由交通管理科负责处理",
                                "C. 所有民政事务均由公共安全分局负责",
                                "D. 仅涉及环境卫生的事项可以交由民政办公室处理",
                            ],
                            "stem": "基层治理中心对居民诉求进行分类管理。环境卫生类事项必须交由城市环卫局办理；公共安全类事项除非涉及交通，否则交由公共安全分局办理；若事项同时涉及环境卫生和公共安全，则必须同时报送给上述两部门；民政类事项统一交由民政办公室办理。以下哪项一定为真",
                            "answer_lines": ["11. B"],
                            "note_lines": [
                                "11. 考点ID=10000003；考点=判断推理；考点路径=判断推理；来源Sheet=全局-基础考点树；B项正确，因为涉及交通的公共安全事项应由交通管理科处理。"
                            ],
                        }
                    ],
                }
            ],
        }

        issues = app_mod.evaluate_paper_questions(paper)

        self.assertIn((0, 0), issues)
        self.assertTrue(any("新机构" in item or "新主体" in item for item in issues[(0, 0)]))

    def test_generate_valid_paper_emits_detailed_progress_logs(self):
        paper = app_mod.parse_markdown_paper(build_full_markdown())
        rulebook = {
            "version": "test-version",
            "exam_profile": {
                "section_blueprint": [
                    {"name": "政治理论", "count": 2},
                    {"name": "常识判断", "count": 3},
                    {"name": "言语理解与表达", "count": 5},
                    {"name": "数量关系", "count": 2},
                    {"name": "判断推理", "count": 5},
                    {"name": "资料分析", "count": 3},
                ],
                "default_question_count": 20,
            },
        }
        logs: list[str] = []

        with patch.object(app_mod, "generate_initial_paper_by_sections", return_value=(paper, 20)), \
             patch.object(app_mod, "evaluate_paper_questions", return_value={}), \
             patch.object(app_mod, "read_json", return_value=rulebook), \
             patch.object(app_mod, "validate_paper", return_value=(True, "校验通过\n候选题量: 20")):
            paper_path, markdown, validation = app_mod.generate_valid_paper(
                provider="ollama",
                api_key="",
                model="dummy",
                focus=None,
                progress_logger=logs.append,
            )

        self.assertTrue(paper_path.exists())
        self.assertIn("question_count: 20", markdown)
        self.assertIn("校验通过", validation)
        self.assertTrue(any("开始第 1 轮" in line for line in logs))
        self.assertTrue(any("分模块初稿" in line or "当前题量" in line for line in logs))
        self.assertTrue(any("最终校验通过" in line for line in logs))


    def test_section_generation_prompt_requires_data_material_provenance_tag(self):
        question_specs = app_mod.build_section_question_plan(
            section_name="资料分析",
            section_count=1,
            start_number=18,
            target_bands=["HIGH"],
        )
        prompt = app_mod.build_section_generation_prompt(
            focus=None,
            paper_id="mock-test",
            generated_at="2026-03-27T16:00:00+08:00",
            rulebook_version="test-version",
            section_name="资料分析",
            section_count=1,
            start_number=18,
            target_bands=["HIGH"],
            question_specs=question_specs,
        )

        self.assertIn("材料来源=库:", prompt)
        self.assertIn("材料来源=现抓:", prompt)

    def test_evaluate_paper_questions_rejects_data_item_without_material_provenance(self):
        paper = {
            "title": "# 测试卷",
            "sections": [
                {
                    "name": "资料分析",
                    "material_lines": [
                        "以下为2024-2025年甲乙两地财政收入统计材料：2024年甲地税收120亿元、乙地税收100亿元；"
                        "2025年甲地税收150亿元、乙地税收118亿元；2025年甲地非税44亿元、乙地非税39亿元，"
                        "据此比较同比增速与结构占比。"
                    ],
                    "questions": [
                        {
                            "number": 18,
                            "block_lines": [
                                "18. 根据上述材料，比较2025年两地税收同比增速，下列判断最准确的是哪项？",
                                "A. 甲乙两地增速完全相同",
                                "B. 甲地税收同比增速高于乙地",
                                "C. 乙地税收同比增速高于甲地",
                                "D. 两地税收均下降",
                            ],
                            "stem": "根据上述材料，比较2025年两地税收同比增速，下列判断最准确的是哪项？",
                            "answer_lines": ["18. B"],
                            "note_lines": [
                                "18. 考点ID=10000004；考点=资料分析；考点路径=资料分析；来源Sheet=全局-基础考点树；"
                                "依据在于同比增速比较，正确项与材料一致，错项可排除。"
                            ],
                        }
                    ],
                }
            ],
        }
        fake_catalog = {
            "entries": [
                {"sheet_name": "全局-基础考点树", "point_id": "10000004", "point_name": "资料分析", "path": "资料分析"}
            ],
            "by_id": {
                "10000004": {
                    "sheet_name": "全局-基础考点树",
                    "point_id": "10000004",
                    "point_name": "资料分析",
                    "path": "资料分析",
                }
            },
        }
        with patch.object(
            app_mod,
            "build_source_stem_index",
            return_value=[{"normalized": "无关样本", "stem": "无关样本", "source_ref": "dummy"}],
        ), patch.object(app_mod, "load_knowledge_point_catalog", return_value=fake_catalog):
            issues = app_mod.evaluate_paper_questions(paper)

        self.assertIn("材料来源", " | ".join(issues[(0, 0)]))

    def test_evaluate_paper_questions_rejects_data_item_marked_as_original_source(self):
        paper = {
            "title": "# 测试卷",
            "sections": [
                {
                    "name": "资料分析",
                    "material_lines": [
                        "以下为2024-2025年甲乙两地财政收入统计材料：2024年甲地税收120亿元、乙地税收100亿元；"
                        "2025年甲地税收150亿元、乙地税收118亿元；2025年甲地非税44亿元、乙地非税39亿元，"
                        "据此比较同比增速与结构占比。"
                    ],
                    "questions": [
                        {
                            "number": 18,
                            "block_lines": [
                                "18. 根据上述材料，比较2025年两地税收同比增速，下列判断最准确的是哪项？",
                                "A. 甲乙两地增速完全相同",
                                "B. 甲地税收同比增速高于乙地",
                                "C. 乙地税收同比增速高于甲地",
                                "D. 两地税收均下降",
                            ],
                            "stem": "根据上述材料，比较2025年两地税收同比增速，下列判断最准确的是哪项？",
                            "answer_lines": ["18. B"],
                            "note_lines": [
                                "18. 考点ID=10000004；考点=资料分析；考点路径=资料分析；来源Sheet=全局-基础考点树；"
                                "材料来源=原创编写；依据在于同比增速比较，正确项与材料一致，错项可排除。"
                            ],
                        }
                    ],
                }
            ],
        }
        fake_catalog = {
            "entries": [
                {"sheet_name": "全局-基础考点树", "point_id": "10000004", "point_name": "资料分析", "path": "资料分析"}
            ],
            "by_id": {
                "10000004": {
                    "sheet_name": "全局-基础考点树",
                    "point_id": "10000004",
                    "point_name": "资料分析",
                    "path": "资料分析",
                }
            },
        }
        with patch.object(
            app_mod,
            "build_source_stem_index",
            return_value=[{"normalized": "无关样本", "stem": "无关样本", "source_ref": "dummy"}],
        ), patch.object(app_mod, "load_knowledge_point_catalog", return_value=fake_catalog):
            issues = app_mod.evaluate_paper_questions(paper)

        self.assertIn("不允许", " | ".join(issues[(0, 0)]))

if __name__ == "__main__":
    unittest.main()
