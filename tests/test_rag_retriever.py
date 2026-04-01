import unittest


class RagRetrieverTests(unittest.TestCase):
    def test_retriever_filters_by_module_and_layer(self):
        from standalone_app.rag.retriever import RagRetriever
        from standalone_app.rag.schema import RagChunk

        chunks = [
            RagChunk(
                chunk_id="style-1",
                source_path="crawler://1",
                source_kind="crawler",
                module="资料分析",
                question_type="材料风格",
                source_domain="stats.gov.cn",
                style_tags=["公报"],
                difficulty_hint="medium",
                content="统计公报式资料分析材料片段。",
                normalized_content="统计公报式资料分析材料片段",
                anti_copy_risk=0.1,
                usable_for_generation=True,
                metadata={},
            ),
            RagChunk(
                chunk_id="style-2",
                source_path="crawler://2",
                source_kind="crawler",
                module="言语理解与表达",
                question_type="评论风格",
                source_domain="people.com.cn",
                style_tags=["时评"],
                difficulty_hint="medium",
                content="官媒评论式言语材料片段。",
                normalized_content="官媒评论式言语材料片段",
                anti_copy_risk=0.1,
                usable_for_generation=True,
                metadata={},
            ),
        ]

        retriever = RagRetriever(chunks=chunks)
        results = retriever.retrieve(module="资料分析", layer="style_rag", top_k=3)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].chunk.module, "资料分析")

    def test_retriever_suppresses_high_copy_risk_in_creative_mode(self):
        from standalone_app.rag.retriever import RagRetriever
        from standalone_app.rag.schema import RagChunk

        chunks = [
            RagChunk(
                chunk_id="question-1",
                source_path="question://1",
                source_kind="question",
                module="判断推理",
                question_type="定义判断",
                source_domain="question_bank",
                style_tags=["真题"],
                difficulty_hint="medium",
                content="高重复风险题干摘要。",
                normalized_content="高重复风险题干摘要",
                anti_copy_risk=0.95,
                usable_for_generation=True,
                metadata={},
            ),
            RagChunk(
                chunk_id="question-2",
                source_path="question://2",
                source_kind="question",
                module="判断推理",
                question_type="定义判断",
                source_domain="question_bank",
                style_tags=["真题骨架"],
                difficulty_hint="medium",
                content="低重复风险题型骨架摘要。",
                normalized_content="低重复风险题型骨架摘要",
                anti_copy_risk=0.2,
                usable_for_generation=True,
                metadata={},
            ),
        ]

        retriever = RagRetriever(chunks=chunks)
        results = retriever.retrieve(
            module="判断推理",
            question_type="定义判断",
            layer="type_rag",
            top_k=5,
            generation_mode="creative",
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].chunk.chunk_id, "question-2")

    def test_retriever_prefers_recent_crawler_materials(self):
        from standalone_app.rag.retriever import RagRetriever
        from standalone_app.rag.schema import RagChunk

        chunks = [
            RagChunk(
                chunk_id="style-old",
                source_path="crawler://old",
                source_kind="crawler",
                module="言语理解与表达",
                question_type="材料风格",
                source_domain="people.com.cn",
                style_tags=["时评"],
                difficulty_hint="medium",
                content="较旧官媒评论材料。",
                normalized_content="较旧官媒评论材料",
                anti_copy_risk=0.1,
                usable_for_generation=True,
                metadata={"last_seen_at": "2025-01-01T00:00:00+08:00"},
            ),
            RagChunk(
                chunk_id="style-new",
                source_path="crawler://new",
                source_kind="crawler",
                module="言语理解与表达",
                question_type="材料风格",
                source_domain="people.com.cn",
                style_tags=["时评"],
                difficulty_hint="medium",
                content="较新官媒评论材料。",
                normalized_content="较新官媒评论材料",
                anti_copy_risk=0.1,
                usable_for_generation=True,
                metadata={"last_seen_at": "2026-03-25T00:00:00+08:00"},
            ),
        ]

        retriever = RagRetriever(chunks=chunks)
        results = retriever.retrieve(module="言语理解与表达", layer="style_rag", top_k=2)

        self.assertEqual(results[0].chunk.chunk_id, "style-new")


if __name__ == "__main__":
    unittest.main()
