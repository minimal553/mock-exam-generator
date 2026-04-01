import unittest
from datetime import datetime, timedelta
from unittest.mock import patch


class RagBundleIntegrationTests(unittest.TestCase):
    def test_question_bundle_contains_rule_style_and_type_sections(self):
        from standalone_app.rag.bundles import build_question_bundle
        from standalone_app.rag.retriever import RagRetriever
        from standalone_app.rag.schema import RagChunk

        chunks = [
            RagChunk(
                chunk_id="rule-1",
                source_path="state://rule",
                source_kind="rule",
                module="综合",
                question_type="hard_constraints",
                source_domain="local_state",
                style_tags=["rulebook"],
                difficulty_hint="guide",
                content="题干要完整，不得靠选项凑字数。",
                normalized_content="题干要完整不得靠选项凑字数",
                anti_copy_risk=0.1,
                usable_for_generation=True,
                metadata={},
            ),
            RagChunk(
                chunk_id="style-1",
                source_path="crawler://style",
                source_kind="crawler",
                module="判断推理",
                question_type="材料风格",
                source_domain="people.com.cn",
                style_tags=["评论"],
                difficulty_hint="medium",
                content="正式评论风格材料片段。",
                normalized_content="正式评论风格材料片段",
                anti_copy_risk=0.1,
                usable_for_generation=True,
                metadata={},
            ),
            RagChunk(
                chunk_id="type-1",
                source_path="question://type",
                source_kind="question",
                module="判断推理",
                question_type="定义判断",
                source_domain="question_bank",
                style_tags=["真题骨架"],
                difficulty_hint="medium",
                content="定义判断需要必要条件全满足。",
                normalized_content="定义判断需要必要条件全满足",
                anti_copy_risk=0.2,
                usable_for_generation=True,
                metadata={},
            ),
        ]

        bundle = build_question_bundle(
            module="判断推理",
            question_type="定义判断",
            retriever=RagRetriever(chunks=chunks),
        )

        self.assertIn("规则约束", bundle)
        self.assertIn("样式参考", bundle)
        self.assertIn("题型骨架", bundle)

    def test_learning_prompt_receives_rag_bundle(self):
        import standalone_app.app as app_mod

        with patch.object(app_mod, "read_json", return_value={"version": "test"}), \
             patch.object(app_mod, "read_text", return_value="stub"), \
             patch.object(app_mod, "read_web_summary", return_value="web"), \
             patch.object(app_mod, "read_applied_rules_summary", return_value="applied"), \
             patch.object(app_mod, "build_learning_rag_context", return_value="## RAG 学习上下文\n- 命中"):
            prompt = app_mod.build_learning_prompt("判断推理")

        self.assertIn("## RAG 学习上下文", prompt)

    def test_single_question_repair_prompt_includes_rag_context(self):
        import standalone_app.app as app_mod

        with patch.object(app_mod, "build_question_rag_context", return_value="## RAG 题目上下文\n- 命中"):
            prompt = app_mod.build_single_question_repair_prompt(
                section_name="判断推理",
                question_number=14,
                question_block=["14. 示例题干", "A. 甲", "B. 乙", "C. 丙", "D. 丁"],
                answer_lines=["14. A"],
                note_lines=["14. 示例说明"],
                failure_reasons=["题干过短"],
            )

        self.assertIn("## RAG 题目上下文", prompt)


    def test_question_bundle_includes_recent_crawler_block_for_data_module(self):
        from standalone_app.rag.bundles import build_question_bundle
        from standalone_app.rag.retriever import RagRetriever
        from standalone_app.rag.schema import RagChunk

        recent_time = datetime.now().astimezone().replace(microsecond=0).isoformat()
        old_time = (datetime.now().astimezone() - timedelta(days=30)).replace(microsecond=0).isoformat()
        data_module = "\u8d44\u6599\u5206\u6790"

        chunks = [
            RagChunk(
                chunk_id="style-new",
                source_path="crawler://new",
                source_kind="crawler",
                module=data_module,
                question_type="\u6750\u6599\u98ce\u683c",
                source_domain="stats.gov.cn",
                style_tags=["data"],
                difficulty_hint="medium",
                content="2026-03 \u7edf\u8ba1\u5feb\u62a5 \u6570\u636e\u540c\u6bd4\u589e\u957f",
                normalized_content="2026-03 \u7edf\u8ba1\u5feb\u62a5 \u6570\u636e\u540c\u6bd4\u589e\u957f",
                anti_copy_risk=0.1,
                usable_for_generation=True,
                metadata={"last_seen_at": recent_time},
            ),
            RagChunk(
                chunk_id="style-old",
                source_path="crawler://old",
                source_kind="crawler",
                module=data_module,
                question_type="\u6750\u6599\u98ce\u683c",
                source_domain="stats.gov.cn",
                style_tags=["data"],
                difficulty_hint="medium",
                content="2023 \u5386\u53f2\u6570\u636e",
                normalized_content="2023 \u5386\u53f2\u6570\u636e",
                anti_copy_risk=0.1,
                usable_for_generation=True,
                metadata={"last_seen_at": old_time},
            ),
            RagChunk(
                chunk_id="rule-1",
                source_path="state://rule",
                source_kind="rule",
                module="\u7efc\u5408",
                question_type="hard_constraints",
                source_domain="local_state",
                style_tags=["rulebook"],
                difficulty_hint="guide",
                content="\u89c4\u5219",
                normalized_content="\u89c4\u5219",
                anti_copy_risk=0.1,
                usable_for_generation=True,
                metadata={},
            ),
            RagChunk(
                chunk_id="type-1",
                source_path="question://type",
                source_kind="question",
                module=data_module,
                question_type=data_module,
                source_domain="question_bank",
                style_tags=["skeleton"],
                difficulty_hint="medium",
                content="\u9898\u578b\u9aa8\u67b6",
                normalized_content="\u9898\u578b\u9aa8\u67b6",
                anti_copy_risk=0.1,
                usable_for_generation=True,
                metadata={},
            ),
        ]

        bundle = build_question_bundle(
            module=data_module,
            question_type=data_module,
            retriever=RagRetriever(chunks=chunks),
        )

        self.assertIn("\u8fd1\u671f\u6293\u53d6\u7d20\u6750", bundle)


if __name__ == "__main__":
    unittest.main()
