import unittest
from unittest.mock import Mock, patch

import standalone_app.app as app_mod


class OllamaProviderTests(unittest.TestCase):
    def test_call_ollama_retries_transient_502_eof(self):
        first = Mock()
        first.status_code = 502
        first.json.return_value = {"error": 'Post "https://ollama.com:443/api/chat": unexpected EOF'}

        second = Mock()
        second.status_code = 200
        second.json.return_value = {"message": {"content": "ok"}}

        with patch("standalone_app.app.requests.post", side_effect=[first, second]) as post_mock, \
             patch("standalone_app.app.time.sleep") as sleep_mock:
            result = app_mod.call_ollama(prompt="test", model="gpt-oss:120b-cloud")

        self.assertEqual(result, "ok")
        self.assertEqual(post_mock.call_count, 2)
        sleep_mock.assert_called_once()

    def test_call_ollama_raises_clear_message_after_retry_exhausted(self):
        failing = Mock()
        failing.status_code = 502
        failing.json.return_value = {"error": 'Post "https://ollama.com:443/api/chat": unexpected EOF'}

        with patch("standalone_app.app.requests.post", side_effect=[failing] * app_mod.OLLAMA_MAX_RETRIES), \
             patch("standalone_app.app.time.sleep"):
            with self.assertRaises(RuntimeError) as ctx:
                app_mod.call_ollama(prompt="test", model="gpt-oss:120b-cloud")

        self.assertIn("Ollama Cloud", str(ctx.exception))
        self.assertIn("502", str(ctx.exception))

    def test_resolve_ollama_model_name_prefers_same_family_when_requested_missing(self):
        chosen, reason = app_mod.resolve_ollama_model_name(
            requested_model="qwen3:235b",
            available_models=["qwen3:8b", "gpt-oss:120b-cloud"],
        )
        self.assertEqual(chosen, "qwen3:8b")
        self.assertEqual(reason, "same-family-nearest-size")

    def test_resolve_ollama_model_name_falls_back_to_gpt_oss_cloud(self):
        chosen, reason = app_mod.resolve_ollama_model_name(
            requested_model="foo:1b",
            available_models=["gpt-oss:120b-cloud", "deepseek-r1:1.5b"],
        )
        self.assertEqual(chosen, "gpt-oss:120b-cloud")
        self.assertEqual(reason, "fallback-candidate")

    def test_list_ollama_models_reads_api_tags(self):
        tags_resp = Mock()
        tags_resp.status_code = 200
        tags_resp.json.return_value = {
            "models": [
                {"name": "qwen3:8b"},
                {"name": "gpt-oss:120b-cloud"},
                {"name": "QWEN3:8B"},
            ]
        }
        with patch("standalone_app.app.requests.get", return_value=tags_resp):
            models = app_mod.list_ollama_models()
        self.assertEqual(models, ["qwen3:8b", "gpt-oss:120b-cloud"])

    def test_build_ollama_call_candidates_includes_alias_and_fallback(self):
        with patch("standalone_app.app.list_ollama_models", return_value=["gpt-oss:120b-cloud"]), \
             patch("standalone_app.app.ollama_show_available", side_effect=lambda m: m == "qwen3-vl:235b-cloud"):
            candidates = app_mod.build_ollama_call_candidates("qwen3:235b")
        self.assertGreaterEqual(len(candidates), 2)
        self.assertEqual(candidates[0], "qwen3:235b")
        self.assertIn("qwen3-vl:235b-cloud", candidates)
        self.assertIn("gpt-oss:120b-cloud", candidates)

    def test_build_ollama_call_candidates_returns_requested_when_inventory_unavailable(self):
        with patch("standalone_app.app.list_ollama_models", side_effect=RuntimeError("boom")), \
             patch("standalone_app.app.ollama_show_available", return_value=False):
            candidates = app_mod.build_ollama_call_candidates("qwen3-vl:235b-cloud")
        self.assertEqual(candidates, ["qwen3-vl:235b-cloud"])

    def test_build_ollama_call_candidates_strict_primary_model_only(self):
        with patch("standalone_app.app.list_ollama_models", return_value=["gpt-oss:120b-cloud"]):
            candidates = app_mod.build_ollama_call_candidates("qwen3.5:397b-cloud")
        self.assertEqual(candidates, ["qwen3.5:397b-cloud"])

    def test_probe_ollama_model_ready_success(self):
        ok_resp = Mock()
        ok_resp.status_code = 200
        ok_resp.json.return_value = {"response": "OK"}
        with patch("standalone_app.app.requests.post", return_value=ok_resp):
            ok, detail = app_mod.probe_ollama_model_ready("qwen3.5:397b-cloud")
        self.assertTrue(ok)
        self.assertEqual(detail, "ok")


if __name__ == "__main__":
    unittest.main()
