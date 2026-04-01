import unittest
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]


class MaterialLibraryTests(unittest.TestCase):
    def test_source_crawler_cli_help_runs_from_repo_root(self):
        result = subprocess.run(
            [sys.executable, "scripts/source_crawler.py", "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("--target-chars", result.stdout)
        self.assertIn("--min-library-chars", result.stdout)
        self.assertIn("--section", result.stdout)

    def test_material_library_counts_chars_by_section(self):
        from standalone_app.material_library import material_char_count

        rows = [
            {"section": "言语理解与表达", "content_chars": 1200, "content": "a" * 1200},
            {"section": "言语理解与表达", "content_chars": 800, "content": "b" * 800},
            {"section": "资料分析", "content_chars": 500, "content": "c" * 500},
        ]

        self.assertEqual(material_char_count(rows, section="言语理解与表达"), 2000)
        self.assertEqual(material_char_count(rows, section="资料分析"), 500)
        self.assertEqual(material_char_count(rows), 2500)

    def test_bulk_backfill_stops_once_section_reaches_target_chars(self):
        import scripts.source_crawler as crawler

        state = {"chars": 0, "rounds": 0}

        def fake_load_material_library():
            return [
                {
                    "section": "言语理解与表达",
                    "content_chars": state["chars"],
                    "content": "x" * state["chars"],
                }
            ]

        def fake_crawl_round(*, focus, limit, cache_hours, target_chars, section, budget_seconds, sitemap_max_urls):
            state["rounds"] += 1
            state["chars"] += 600000
            return ([{"section": section, "content": "x" * 600000, "content_chars": 600000}], f"round {state['rounds']}")

        summary = crawler.crawl_until_library_chars(
            section="言语理解与表达",
            min_chars=2000000,
            focus="言语理解",
            per_round_limit=20,
            target_chars_per_round=600000,
            round_limit=10,
            load_rows=fake_load_material_library,
            crawl_round=fake_crawl_round,
        )

        self.assertGreaterEqual(summary["final_chars"], 2000000)
        self.assertEqual(summary["rounds"], 4)

    def test_bulk_backfill_does_not_stop_early_on_temporary_stalls(self):
        import scripts.source_crawler as crawler

        state = {"chars": 0, "rounds": 0}
        per_round_growth = [0, 0, 500000, 500000, 500000, 500000]

        def fake_load_material_library():
            return [
                {
                    "section": "言语理解与表达",
                    "content_chars": state["chars"],
                    "content": "x" * state["chars"],
                }
            ]

        def fake_crawl_round(*, focus, limit, cache_hours, target_chars, section, budget_seconds, sitemap_max_urls):
            growth = per_round_growth[state["rounds"]] if state["rounds"] < len(per_round_growth) else 0
            state["rounds"] += 1
            state["chars"] += growth
            return (
                [{"section": section, "content": "x" * growth, "content_chars": growth}],
                f"round {state['rounds']}",
            )

        summary = crawler.crawl_until_library_chars(
            section="言语理解与表达",
            min_chars=2000000,
            focus="言语理解",
            per_round_limit=20,
            target_chars_per_round=500000,
            round_limit=10,
            load_rows=fake_load_material_library,
            crawl_round=fake_crawl_round,
        )

        self.assertTrue(summary["completed"])
        self.assertGreaterEqual(summary["rounds"], 6)

    def test_extract_listing_links_keeps_same_domain_index_pages(self):
        import scripts.source_crawler as crawler

        html = """
        <html><body>
        <a href="https://www.people.com.cn/">首页</a>
        <a href="https://opinion.people.com.cn/">观点</a>
        <a href="https://health.people.com.cn/">健康</a>
        <a href="https://opinion.people.com.cn/n1/2026/0326/c1003-12345678.html">文章</a>
        <a href="https://other.example.com/list">外链</a>
        </body></html>
        """
        source = {
            "seed_urls": ["https://www.people.com.cn/"],
            "allow_domains": ["people.com.cn"],
            "path_hints": ["opinion", "health", "edu"],
        }

        listings = crawler.extract_listing_links(html, source, max_pages=5)

        self.assertIn("https://opinion.people.com.cn/", listings)
        self.assertIn("https://health.people.com.cn/", listings)
        self.assertNotIn("https://opinion.people.com.cn/n1/2026/0326/c1003-12345678.html", listings)

    def test_extract_sitemap_urls_keeps_article_links_on_allowed_domains(self):
        import scripts.source_crawler as crawler

        xml_text = """
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url><loc>https://opinion.people.com.cn/n1/2026/0326/c1003-12345678.html</loc></url>
          <url><loc>https://opinion.people.com.cn/n1/2026/0325/c1003-12345679.html</loc></url>
          <url><loc>https://other.example.com/a.html</loc></url>
        </urlset>
        """

        urls = crawler.extract_sitemap_urls(xml_text, ["people.com.cn"], max_urls=10)

        self.assertEqual(len(urls), 2)
        self.assertTrue(all(url.endswith(".html") for url in urls))

    def test_extract_sitemap_urls_filters_forum_noise_links(self):
        import scripts.source_crawler as crawler

        xml_text = """
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url><loc>http://forum.home.news.cn/detail/140106843/1.html</loc></url>
          <url><loc>https://www.news.cn/fortune/20260301/abcdef1234567890.htm</loc></url>
        </urlset>
        """

        urls = crawler.extract_sitemap_urls(xml_text, ["news.cn"], max_urls=10)

        self.assertEqual(urls, ["https://www.news.cn/fortune/20260301/abcdef1234567890.htm"])

    def test_extract_sitemap_index_urls_keeps_child_sitemaps_on_allowed_domains(self):
        import scripts.source_crawler as crawler

        xml_text = """
        <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <sitemap><loc>https://www.people.com.cn/sitemap/news.xml</loc></sitemap>
          <sitemap><loc>https://opinion.people.com.cn/sitemap/opinion.xml</loc></sitemap>
          <sitemap><loc>https://other.example.com/sitemap.xml</loc></sitemap>
        </sitemapindex>
        """

        urls = crawler.extract_sitemap_index_urls(xml_text, ["people.com.cn"], max_urls=10)

        self.assertEqual(
            urls,
            [
                "https://www.people.com.cn/sitemap/news.xml",
                "https://opinion.people.com.cn/sitemap/opinion.xml",
            ],
        )

    def test_fetch_sitemap_article_urls_recurses_into_sitemap_index(self):
        import scripts.source_crawler as crawler

        class FakeResponse:
            def __init__(self, text):
                self.text = text
                self.apparent_encoding = None

            def raise_for_status(self):
                return None

        class FakeSession:
            def __init__(self, payloads):
                self.payloads = payloads

            def get(self, url, timeout=None):
                payload = self.payloads.get(url)
                if payload is None:
                    raise crawler.requests.RequestException("missing")
                return FakeResponse(payload)

        session = FakeSession(
            {
                "https://www.people.com.cn/sitemap_index.xml": """
                <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
                  <sitemap><loc>https://www.people.com.cn/sitemaps/a.xml</loc></sitemap>
                  <sitemap><loc>https://opinion.people.com.cn/sitemaps/b.xml</loc></sitemap>
                </sitemapindex>
                """,
                "https://www.people.com.cn/sitemaps/a.xml": """
                <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
                  <url><loc>https://opinion.people.com.cn/n1/2026/0326/c1003-12345678.html</loc></url>
                </urlset>
                """,
                "https://opinion.people.com.cn/sitemaps/b.xml": """
                <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
                  <url><loc>https://opinion.people.com.cn/n1/2026/0325/c1003-12345679.html</loc></url>
                </urlset>
                """,
            }
        )
        source = {
            "seed_urls": ["https://www.people.com.cn/"],
            "allow_domains": ["people.com.cn"],
        }

        urls = crawler.fetch_sitemap_article_urls(session, source, max_urls=10)

        self.assertEqual(
            urls,
            [
                "https://opinion.people.com.cn/n1/2026/0326/c1003-12345678.html",
                "https://opinion.people.com.cn/n1/2026/0325/c1003-12345679.html",
            ],
        )

    def test_fetch_sitemap_article_urls_skips_known_urls_and_keeps_scanning(self):
        import scripts.source_crawler as crawler

        class FakeResponse:
            def __init__(self, text):
                self.text = text
                self.apparent_encoding = None

            def raise_for_status(self):
                return None

        class FakeSession:
            def __init__(self, payloads):
                self.payloads = payloads

            def get(self, url, timeout=None):
                payload = self.payloads.get(url)
                if payload is None:
                    raise crawler.requests.RequestException("missing")
                return FakeResponse(payload)

        session = FakeSession(
            {
                "https://www.people.com.cn/sitemap_index.xml": """
                <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
                  <sitemap><loc>https://www.people.com.cn/sitemaps/a.xml</loc></sitemap>
                </sitemapindex>
                """,
                "https://www.people.com.cn/sitemaps/a.xml": """
                <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
                  <url><loc>https://opinion.people.com.cn/n1/2026/0326/c1003-12345678.html</loc></url>
                  <url><loc>https://opinion.people.com.cn/n1/2026/0325/c1003-12345679.html</loc></url>
                  <url><loc>https://opinion.people.com.cn/n1/2026/0324/c1003-12345680.html</loc></url>
                </urlset>
                """,
            }
        )
        source = {
            "seed_urls": ["https://www.people.com.cn/"],
            "allow_domains": ["people.com.cn"],
        }

        urls = crawler.fetch_sitemap_article_urls(
            session,
            source,
            max_urls=2,
            skip_urls={"https://opinion.people.com.cn/n1/2026/0326/c1003-12345678.html"},
        )

        self.assertEqual(
            urls,
            [
                "https://opinion.people.com.cn/n1/2026/0325/c1003-12345679.html",
                "https://opinion.people.com.cn/n1/2026/0324/c1003-12345680.html",
            ],
        )

    def test_extract_search_result_links_keeps_allowed_article_urls(self):
        import scripts.source_crawler as crawler

        html = """
        <html><body>
        <a href="https://opinion.people.com.cn/n1/2026/0326/c1003-12345678.html">结果1</a>
        <a href="https://opinion.people.com.cn/n1/2026/0325/c1003-12345679.html">结果2</a>
        <a href="https://other.example.com/a.html">外链</a>
        </body></html>
        """

        urls = crawler.extract_search_result_links(html, ["people.com.cn"], max_urls=10)

        self.assertEqual(len(urls), 2)
        self.assertTrue(all("people.com.cn" in url for url in urls))

    def test_merge_material_rows_updates_existing_url_entry(self):
        from standalone_app.material_library import merge_material_rows

        existing = [
            {
                "section": "言语理解与表达",
                "source_name": "人民网",
                "source_domain": "people.com.cn",
                "article_url": "https://www.people.com.cn/a1.html",
                "title": "旧文章",
                "summary": "旧摘要",
                "content": "这是一篇用于测试的长材料。" * 20,
                "published_at": "2026-03-20",
                "fetched_at": "2026-03-20T09:00:00+08:00",
                "first_seen_at": "2026-03-20T09:00:00+08:00",
                "last_seen_at": "2026-03-20T09:00:00+08:00",
                "fetch_count": 1,
            }
        ]
        incoming = [
            {
                "section": "言语理解与表达",
                "source_name": "人民网",
                "source_domain": "people.com.cn",
                "article_url": "https://www.people.com.cn/a1.html",
                "title": "旧文章",
                "summary": "新摘要",
                "content": "这是一篇用于测试的长材料。" * 22,
                "published_at": "2026-03-20",
                "fetched_at": "2026-03-26T10:00:00+08:00",
            }
        ]

        merged, stats = merge_material_rows(
            existing,
            incoming,
            seen_at="2026-03-26T10:00:00+08:00",
        )

        self.assertEqual(len(merged), 1)
        self.assertEqual(stats["updated_count"], 1)
        self.assertEqual(merged[0]["fetch_count"], 2)
        self.assertEqual(merged[0]["first_seen_at"], "2026-03-20T09:00:00+08:00")
        self.assertEqual(merged[0]["last_seen_at"], "2026-03-26T10:00:00+08:00")
        self.assertEqual(merged[0]["summary"], "新摘要")

    def test_merge_material_rows_dedupes_same_content_from_new_url(self):
        from standalone_app.material_library import merge_material_rows

        body = "统计公报材料示例。" * 40
        existing = [
            {
                "section": "资料分析",
                "source_name": "国家统计局",
                "source_domain": "stats.gov.cn",
                "article_url": "https://www.stats.gov.cn/a.html",
                "title": "公报甲",
                "summary": "摘要甲",
                "content": body,
                "published_at": "2026-03-10",
                "fetched_at": "2026-03-10T09:00:00+08:00",
                "first_seen_at": "2026-03-10T09:00:00+08:00",
                "last_seen_at": "2026-03-10T09:00:00+08:00",
                "fetch_count": 1,
            }
        ]
        incoming = [
            {
                "section": "资料分析",
                "source_name": "国家统计局",
                "source_domain": "stats.gov.cn",
                "article_url": "https://www.stats.gov.cn/b.html",
                "title": "公报乙",
                "summary": "摘要乙",
                "content": body,
                "published_at": "2026-03-10",
                "fetched_at": "2026-03-26T12:00:00+08:00",
            }
        ]

        merged, stats = merge_material_rows(
            existing,
            incoming,
            seen_at="2026-03-26T12:00:00+08:00",
        )

        self.assertEqual(len(merged), 1)
        self.assertEqual(stats["updated_count"], 1)
        self.assertEqual(merged[0]["fetch_count"], 2)
        self.assertIn("https://www.stats.gov.cn/b.html", merged[0]["seen_urls"])

    def test_ensure_catalog_enriches_existing_source_domains_from_defaults(self):
        import scripts.source_crawler as crawler

        with tempfile.TemporaryDirectory() as tmpdir:
            original_catalog_path = crawler.CATALOG_PATH
            catalog_path = Path(tmpdir) / "catalog.json"
            crawler.CATALOG_PATH = catalog_path
            try:
                crawler.write_json(
                    catalog_path,
                    {
                        "generated_at": "2026-03-26T12:00:00+08:00",
                        "sources": [
                            {
                                "name": "人民网",
                                "section": "言语理解与表达",
                                "seed_urls": ["https://www.people.com.cn/"],
                                "allow_domains": ["people.com.cn"],
                                "keywords": ["评论"],
                                "path_hints": ["opinion"],
                            }
                        ],
                    },
                )

                catalog = crawler.ensure_catalog()
                source = next(item for item in catalog["sources"] if item["name"] == "人民网")
                self.assertIn("people.cn", source["allow_domains"])
            finally:
                crawler.CATALOG_PATH = original_catalog_path

    def test_ensure_catalog_keeps_same_domain_sources_when_sections_differ(self):
        import scripts.source_crawler as crawler

        with tempfile.TemporaryDirectory() as tmpdir:
            original_catalog_path = crawler.CATALOG_PATH
            original_defaults = crawler.DEFAULT_SOURCES
            catalog_path = Path(tmpdir) / "catalog.json"
            crawler.CATALOG_PATH = catalog_path
            crawler.DEFAULT_SOURCES = [
                {
                    "name": "语言源",
                    "section": "言语理解与表达",
                    "seed_urls": ["https://a.example.com/lang"],
                    "allow_domains": ["a.example.com"],
                    "keywords": ["语言"],
                    "path_hints": ["lang"],
                },
                {
                    "name": "数据源",
                    "section": "资料分析",
                    "seed_urls": ["https://a.example.com/data"],
                    "allow_domains": ["a.example.com"],
                    "keywords": ["数据"],
                    "path_hints": ["data"],
                },
            ]
            try:
                crawler.write_json(
                    catalog_path,
                    {
                        "generated_at": "2026-03-26T12:00:00+08:00",
                        "sources": [
                            {
                                "name": "语言源",
                                "section": "言语理解与表达",
                                "seed_urls": ["https://a.example.com/lang"],
                                "allow_domains": ["a.example.com"],
                                "keywords": ["语言"],
                                "path_hints": ["lang"],
                            }
                        ],
                    },
                )

                catalog = crawler.ensure_catalog()
                sections = sorted(item["section"] for item in catalog["sources"])
                self.assertEqual(sections, ["言语理解与表达", "资料分析"])
                self.assertEqual(len(catalog["sources"]), 2)
            finally:
                crawler.CATALOG_PATH = original_catalog_path
                crawler.DEFAULT_SOURCES = original_defaults

    def test_extract_article_supports_table_heavy_data_page(self):
        import scripts.source_crawler as crawler

        class FakeResponse:
            def __init__(self, text):
                self.text = text
                self.apparent_encoding = None

            def raise_for_status(self):
                return None

        class FakeSession:
            def __init__(self, html):
                self.html = html

            def get(self, url, timeout=None):
                return FakeResponse(self.html)

        html = """
        <html>
          <head><title>2025年主要经济指标</title></head>
          <body>
            <table>
              <tr><th>指标</th><th>2024</th><th>2025</th></tr>
              <tr><td>工业增加值</td><td>102.1</td><td>106.4</td></tr>
              <tr><td>固定资产投资</td><td>98.3</td><td>101.9</td></tr>
              <tr><td>社会消费品零售总额</td><td>103.4</td><td>107.8</td></tr>
              <tr><td>城镇新增就业</td><td>1200</td><td>1280</td></tr>
            </table>
          </body>
        </html>
        """
        source = {
            "section": "资料分析",
            "name": "测试来源",
            "seed_urls": ["https://example.com/"],
            "keywords": ["统计", "指标", "同比"],
        }
        candidate = {"url": "https://example.com/data.html", "title": "数据公报", "score": 5}

        article = crawler.extract_article(FakeSession(html), source, candidate, ["统计", "指标"])

        self.assertIsNotNone(article)
        self.assertIn("工业增加值", article["content"])
        self.assertGreaterEqual(len(article["content"]), 80)

    def test_extract_article_rejects_narrative_only_data_page(self):
        import scripts.source_crawler as crawler

        class FakeResponse:
            def __init__(self, text):
                self.text = text
                self.apparent_encoding = None

            def raise_for_status(self):
                return None

        class FakeSession:
            def __init__(self, html):
                self.html = html

            def get(self, url, timeout=None):
                return FakeResponse(self.html)

        html = """
        <html>
          <head><title>某地发展观察</title></head>
          <body>
            <p>近年来，当地持续优化营商环境，推动产业升级与创新发展，取得积极成效。围绕现代服务业和先进制造业协同发展，相关部门持续推进流程再造、制度优化和服务升级，进一步夯实高质量发展基础。</p>
            <p>下一步将继续完善治理机制，提升公共服务水平，增强群众获得感。有关方面表示，将以系统化思维推进改革协同，强化政策执行和服务供给，持续提升区域综合竞争力和城市治理现代化水平。</p>
          </body>
        </html>
        """
        source = {
            "section": "资料分析",
            "name": "测试来源",
            "seed_urls": ["https://example.com/"],
            "keywords": ["统计", "指标", "同比"],
        }
        candidate = {"url": "https://example.com/narrative.html", "title": "发展观察", "score": 5}

        article = crawler.extract_article(FakeSession(html), source, candidate, ["统计", "指标"])

        self.assertIsNone(article)


    def test_choose_sources_prioritizes_high_yield_data_domains(self):
        import scripts.source_crawler as crawler

        catalog = {
            "sources": [
                {
                    "name": "A",
                    "section": crawler.SECTION_DATA,
                    "seed_urls": ["https://www.gov.cn/shuju/"],
                    "allow_domains": ["gov.cn"],
                    "keywords": ["统计"],
                    "path_hints": ["shuju"],
                },
                {
                    "name": "B",
                    "section": crawler.SECTION_DATA,
                    "seed_urls": ["https://www.stats.gov.cn/"],
                    "allow_domains": ["stats.gov.cn"],
                    "keywords": ["统计公报"],
                    "path_hints": ["sj"],
                },
                {
                    "name": "C",
                    "section": crawler.SECTION_DATA,
                    "seed_urls": ["http://www.cinic.org.cn/"],
                    "allow_domains": ["cinic.org.cn"],
                    "keywords": ["产业数据"],
                    "path_hints": ["hangye"],
                },
                {
                    "name": "D",
                    "section": crawler.SECTION_DATA,
                    "seed_urls": ["https://www.cnnic.cn/"],
                    "allow_domains": ["cnnic.cn"],
                    "keywords": ["网络报告"],
                    "path_hints": ["bg"],
                },
            ]
        }

        selected = crawler.choose_sources(
            catalog,
            crawler.parse_focus_tokens("资料分析 统计 公报 同比 环比"),
            section=crawler.SECTION_DATA,
        )
        domains = [item.get("allow_domains", [""])[0] for item in selected]
        self.assertIn("stats.gov.cn", domains)
        self.assertIn("cinic.org.cn", domains)
        if "gov.cn" in domains:
            self.assertLess(domains.index("stats.gov.cn"), domains.index("gov.cn"))
        if "cnnic.cn" in domains:
            self.assertLess(domains.index("cinic.org.cn"), domains.index("cnnic.cn"))


if __name__ == "__main__":
    unittest.main()
