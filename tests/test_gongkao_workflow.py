import unittest

import scripts.gongkao_workflow as workflow


class GongkaoWorkflowTests(unittest.TestCase):
    def test_parse_docx_html_falls_back_without_lxml(self):
        soup = workflow.parse_docx_html(
            "<html><body><h1>测试材料</h1><section class='question-section'></section></body></html>"
        )

        self.assertEqual(soup.select_one("h1").get_text(strip=True), "测试材料")


if __name__ == "__main__":
    unittest.main()
