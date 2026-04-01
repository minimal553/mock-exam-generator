import json
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


class RagExtractorTests(unittest.TestCase):
    def test_rag_config_contains_required_layers(self):
        config = json.loads((ROOT / "state" / "rag_config.json").read_text(encoding="utf-8"))
        self.assertIn("rules_rag", config)
        self.assertIn("style_rag", config)
        self.assertIn("type_rag", config)

    def test_extract_rule_chunks_marks_source_kind_rule(self):
        from standalone_app.rag.extractors import extract_rule_chunks

        chunks = extract_rule_chunks()
        self.assertTrue(chunks)
        self.assertTrue(all(chunk.source_kind == "rule" for chunk in chunks))
        self.assertTrue(all(chunk.content.strip() for chunk in chunks))

    def test_extract_question_chunks_have_module_and_type(self):
        from standalone_app.rag.extractors import extract_question_chunks

        chunks = extract_question_chunks(limit=5)
        self.assertTrue(chunks)
        self.assertTrue(all(chunk.source_kind == "question" for chunk in chunks))
        self.assertTrue(all(chunk.module for chunk in chunks))
        self.assertTrue(all(chunk.question_type for chunk in chunks))

    def test_build_rag_index_writes_manifest(self):
        from standalone_app.rag.index_builder import build_rag_index

        manifest = build_rag_index()
        self.assertGreater(manifest["chunk_count"], 0)
        self.assertTrue((ROOT / "state" / "rag_manifest.json").exists())
        self.assertTrue((ROOT / "data" / "rag_corpus.jsonl").exists())

    def test_extract_crawler_chunks_balances_modules_under_limit(self):
        from standalone_app.rag import extractors as ext

        rows = []
        for i in range(60):
            rows.append(
                {
                    "section": "言语理解与表达",
                    "title": f"言语材料{i}",
                    "summary": "评论材料",
                    "content": "文本" * 80,
                    "article_url": f"https://example.com/lang/{i}.html",
                    "source_domain": "example.com",
                    "source_name": "示例源",
                    "relevance_score": 5,
                    "fetched_at": "2026-03-27T10:00:00+08:00",
                    "last_seen_at": "2026-03-27T10:00:00+08:00",
                }
            )
        for i in range(4):
            rows.append(
                {
                    "section": "资料分析",
                    "title": f"数据材料{i}",
                    "summary": "统计数据",
                    "content": "2025年同比增长12% 环比增长1.2% 亿元 万人 指数" * 10,
                    "article_url": f"https://example.com/data/{i}.htm",
                    "source_domain": "example.com",
                    "source_name": "示例源",
                    "relevance_score": 9,
                    "fetched_at": "2026-03-27T10:00:00+08:00",
                    "last_seen_at": "2026-03-27T10:00:00+08:00",
                }
            )

        with patch.object(ext, "read_jsonl", return_value=rows):
            chunks = ext.extract_crawler_chunks(limit=20)

        self.assertEqual(len(chunks), 20)
        data_count = sum(1 for chunk in chunks if chunk.module == "资料分析")
        self.assertGreaterEqual(data_count, 2)


if __name__ == "__main__":
    unittest.main()
