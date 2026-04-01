#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree as ET
import zipfile

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from standalone_app.material_library import (  # noqa: E402
    build_material_library_manifest,
    load_material_library,
    material_char_count,
    merge_material_rows,
    save_material_library,
)


DATA_DIR = ROOT / "data"
STATE_DIR = ROOT / "state"
CATALOG_PATH = STATE_DIR / "source_catalog.json"
CRAWL_STATE_PATH = STATE_DIR / "web_crawl_state.json"
OUTPUT_JSONL = DATA_DIR / "web_materials.jsonl"
OUTPUT_SUMMARY = DATA_DIR / "web_material_summary.md"
EXTRA_SOURCE_XLSX_PATH = ROOT / "模拟题资料库搜集.xlsx"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 GongkaoBot/1.0"
)
SEED_TIMEOUT_SECONDS = 8
ARTICLE_TIMEOUT_SECONDS = 10
TOTAL_BUDGET_SECONDS = 25
DEFAULT_TARGET_CHARS = 30000

SECTION_LANGUAGE = "言语理解与表达"
SECTION_DATA = "资料分析"
SECTION_JUDGMENT = "判断推理"
SECTION_COMMON = "常识判断"


DEFAULT_SOURCES: list[dict[str, Any]] = [
    {
        "name": "人民网",
        "section": SECTION_LANGUAGE,
        "seed_urls": [
            "https://www.people.com.cn/",
            "https://opinion.people.com.cn/",
            "https://edu.people.com.cn/",
            "https://health.people.com.cn/",
            "https://finance.people.com.cn/",
        ],
        "allow_domains": ["people.com.cn", "people.cn"],
        "keywords": ["评论", "时评", "教育", "科技", "治理", "消费", "就业", "健康"],
        "path_hints": ["opinion", "n1", "rmrb", "content", "article"],
    },
    {
        "name": "新华网",
        "section": SECTION_LANGUAGE,
        "seed_urls": [
            "https://www.xinhuanet.com/",
            "https://www.news.cn/comments/",
            "https://www.news.cn/fortune/",
            "https://www.news.cn/tech/",
            "https://www.news.cn/politics/",
        ],
        "allow_domains": ["xinhuanet.com", "news.cn"],
        "keywords": ["评论", "观察", "教育", "科技", "经济", "治理", "生态"],
        "path_hints": ["comments", "fortune", "tech", "politics", "detail"],
    },
    {
        "name": "光明网",
        "section": SECTION_LANGUAGE,
        "seed_urls": [
            "https://www.gmw.cn/",
            "https://guancha.gmw.cn/",
            "https://culture.gmw.cn/",
            "https://edu.gmw.cn/",
            "https://theory.gmw.cn/",
        ],
        "allow_domains": ["gmw.cn"],
        "keywords": ["评论", "教育", "文化", "科技", "时评", "理论"],
        "path_hints": ["content", "culture", "edu", "theory", "article"],
    },
    {
        "name": "求是网",
        "section": SECTION_LANGUAGE,
        "seed_urls": [
            "https://www.qstheory.cn/",
            "https://www.qstheory.cn/dukan/",
            "https://www.qstheory.cn/llwx/",
        ],
        "allow_domains": ["qstheory.cn"],
        "keywords": ["理论", "治理", "改革", "发展", "现代化"],
        "path_hints": ["dukan", "llwx", "article"],
    },
    {
        "name": "半月谈",
        "section": SECTION_LANGUAGE,
        "seed_urls": ["http://www.banyuetan.org/"],
        "allow_domains": ["banyuetan.org"],
        "keywords": ["评论", "观察", "基层", "治理", "青年", "就业"],
        "path_hints": ["detail", "article"],
    },
    {
        "name": "中国青年报",
        "section": SECTION_LANGUAGE,
        "seed_urls": ["http://www.cyol.com/"],
        "allow_domains": ["cyol.com"],
        "keywords": ["青年", "就业", "教育", "评论", "观察"],
        "path_hints": ["content", "node", "article"],
    },
    {
        "name": "经济日报",
        "section": SECTION_LANGUAGE,
        "seed_urls": [
            "http://www.ce.cn/",
            "http://www.ce.cn/xwzx/",
            "http://www.ce.cn/fortune/",
            "http://www.ce.cn/macro/",
        ],
        "allow_domains": ["ce.cn"],
        "keywords": ["经济", "评论", "产业", "消费", "企业", "就业"],
        "path_hints": ["fortune", "macro", "rolling", "article"],
    },
    {
        "name": "文汇报",
        "section": SECTION_LANGUAGE,
        "seed_urls": ["https://www.whb.cn/"],
        "allow_domains": ["whb.cn"],
        "keywords": ["评论", "教育", "科技", "文化", "治理"],
        "path_hints": ["content", "article", "detail"],
    },
    {
        "name": "三联生活周刊",
        "section": SECTION_LANGUAGE,
        "seed_urls": ["https://www.lifeweek.com.cn/"],
        "allow_domains": ["lifeweek.com.cn"],
        "keywords": ["观察", "社会", "科技", "健康", "教育"],
        "path_hints": ["article", "detail"],
    },
    {
        "name": "澎湃新闻",
        "section": SECTION_LANGUAGE,
        "seed_urls": ["https://www.thepaper.cn/"],
        "allow_domains": ["thepaper.cn"],
        "keywords": ["观察", "教育", "科技", "环境", "评论"],
        "path_hints": ["newsDetail", "detail"],
    },
    {
        "name": "果壳网",
        "section": SECTION_LANGUAGE,
        "seed_urls": ["https://www.guokr.com/"],
        "allow_domains": ["guokr.com"],
        "keywords": ["科普", "地震", "生物", "物理", "天文", "健康"],
        "path_hints": ["article", "science"],
    },
    {
        "name": "中国教育报",
        "section": SECTION_LANGUAGE,
        "seed_urls": ["http://www.jyb.cn/"],
        "allow_domains": ["jyb.cn"],
        "keywords": ["教育", "课堂", "教师", "育人", "思政"],
        "path_hints": ["content", "node"],
    },
    {
        "name": "科技日报",
        "section": SECTION_LANGUAGE,
        "seed_urls": ["http://www.stdaily.com/"],
        "allow_domains": ["stdaily.com"],
        "keywords": ["科技", "科普", "创新", "航天", "人工智能", "生物"],
        "path_hints": ["index", "article", "cehua"],
    },
    {
        "name": "央广网",
        "section": SECTION_LANGUAGE,
        "seed_urls": ["https://www.cnr.cn/"],
        "allow_domains": ["cnr.cn"],
        "keywords": ["评论", "心理", "教育", "消费", "观察"],
        "path_hints": ["comment", "news", "edu"],
    },
    {
        "name": "中国政府网",
        "section": SECTION_COMMON,
        "seed_urls": ["https://www.gov.cn/"],
        "allow_domains": ["gov.cn"],
        "keywords": ["政策", "通知", "意见", "措施", "改革", "服务", "教育", "消费"],
        "path_hints": ["zhengce", "yaowen", "xinwen"],
    },
    {
        "name": "国家统计局",
        "section": SECTION_DATA,
        "seed_urls": [
            "https://www.stats.gov.cn/",
            "https://www.stats.gov.cn/sj/",
            "https://www.stats.gov.cn/zs/tjws/",
        ],
        "allow_domains": ["stats.gov.cn"],
        "keywords": ["统计公报", "月度", "同比", "增长", "工业", "消费", "固定资产", "就业"],
        "path_hints": ["sj", "tjsj", "zxfb", "sjjd"],
    },
    {
        "name": "中国互联网络信息中心",
        "section": SECTION_DATA,
        "seed_urls": ["https://www.cnnic.cn/hlwfzyj/hlwxzbg/hlwtjbg/"],
        "allow_domains": ["cnnic.cn"],
        "keywords": ["报告", "统计", "互联网", "用户", "网民", "普及率"],
        "path_hints": ["hlwfzyj", "hlwxzbg", "tjbg"],
    },
    {
        "name": "中国产业经济信息网",
        "section": SECTION_DATA,
        "seed_urls": ["http://www.cinic.org.cn/"],
        "allow_domains": ["cinic.org.cn"],
        "keywords": ["产业", "经济运行", "数据", "行业", "报告"],
        "path_hints": ["hangye", "hybg", "index"],
    },
    {
        "name": "中国汽车工业协会",
        "section": SECTION_DATA,
        "seed_urls": ["http://www.caam.org.cn/"],
        "allow_domains": ["caam.org.cn"],
        "keywords": ["产销", "汽车", "同比", "新能源", "月报", "行业"],
        "path_hints": ["statistics", "news", "chn"],
    },
    {
        "name": "中国就业网",
        "section": SECTION_DATA,
        "seed_urls": ["https://www.chinajob.gov.cn/"],
        "allow_domains": ["chinajob.gov.cn"],
        "keywords": ["就业", "招聘", "统计", "岗位", "报告"],
        "path_hints": ["article", "content", "zcfg"],
    },
    {
        "name": "中国政府网-数据解读",
        "section": SECTION_DATA,
        "seed_urls": [
            "https://www.gov.cn/shuju/index.htm",
            "https://www.gov.cn/lianbo/bumen/index.htm",
            "https://www.gov.cn/zhengce/jiedu/index.htm",
        ],
        "allow_domains": ["gov.cn"],
        "keywords": ["统计", "数据", "同比", "环比", "增长", "投资", "就业", "财政", "解读"],
        "path_hints": ["shuju", "jiedu", "bumen", "content"],
    },
    {
        "name": "新华网-经济数据",
        "section": SECTION_DATA,
        "seed_urls": [
            "https://www.news.cn/fortune/",
            "https://www.news.cn/tech/",
            "https://www.news.cn/politics/",
        ],
        "allow_domains": ["news.cn", "xinhuanet.com"],
        "keywords": ["统计", "月度", "季度", "同比", "环比", "指数", "投资", "消费", "就业"],
        "path_hints": ["fortune", "detail", "article", "economy"],
    },
    {
        "name": "人民网-经济数据",
        "section": SECTION_DATA,
        "seed_urls": [
            "https://finance.people.com.cn/",
            "https://lianghui.people.com.cn/",
            "https://politics.people.com.cn/",
        ],
        "allow_domains": ["people.com.cn", "people.cn"],
        "keywords": ["统计", "经济运行", "同比", "环比", "就业", "财政", "工业", "消费"],
        "path_hints": ["finance", "politics", "n1", "article"],
    },
    {
        "name": "经济日报-数据频道",
        "section": SECTION_DATA,
        "seed_urls": [
            "http://www.ce.cn/macro/",
            "http://www.ce.cn/xwzx/",
            "http://www.ce.cn/fortune/",
        ],
        "allow_domains": ["ce.cn"],
        "keywords": ["统计", "宏观", "数据", "指数", "同比", "环比", "投资", "就业"],
        "path_hints": ["macro", "fortune", "rolling", "article"],
    },
    {
        "name": "科普中国",
        "section": SECTION_JUDGMENT,
        "seed_urls": ["https://www.kepuchina.cn/"],
        "allow_domains": ["kepuchina.cn"],
        "keywords": ["科普", "实验", "机制", "原理", "解释"],
        "path_hints": ["article", "science", "edu"],
    },
    {
        "name": "央视网",
        "section": SECTION_JUDGMENT,
        "seed_urls": ["https://news.cctv.com/"],
        "allow_domains": ["cctv.com"],
        "keywords": ["评论", "调查", "观察", "科技", "治理"],
        "path_hints": ["article", "special", "202"],
    },
    {
        "name": "MBA智库",
        "section": SECTION_JUDGMENT,
        "seed_urls": ["https://wiki.mbalib.com/"],
        "allow_domains": ["mbalib.com"],
        "keywords": ["效应", "理论", "定律", "概念", "定义"],
        "path_hints": ["wiki"],
    },
    {
        "name": "百度百科",
        "section": SECTION_JUDGMENT,
        "seed_urls": ["https://baike.baidu.com/"],
        "allow_domains": ["baike.baidu.com"],
        "keywords": ["概念", "定义", "效应", "定律", "原理"],
        "path_hints": ["item"],
    },
]


def now_iso() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _xlsx_shared_strings(path: Path) -> list[str]:
    with zipfile.ZipFile(path, "r") as archive:
        if "xl/sharedStrings.xml" not in archive.namelist():
            return []
        root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    values: list[str] = []
    for si in root.findall("x:si", ns):
        texts = [node.text or "" for node in si.findall(".//x:t", ns)]
        values.append(normalize_ws("".join(texts)))
    return values


def _extract_urls_from_xlsx(path: Path) -> list[str]:
    if not path.exists():
        return []
    urls: list[str] = []
    try:
        shared = _xlsx_shared_strings(path)
        with zipfile.ZipFile(path, "r") as archive:
            sheet_names = [name for name in archive.namelist() if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")]
            for sheet_name in sheet_names:
                root = ET.fromstring(archive.read(sheet_name))
                ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                for cell in root.findall(".//x:c", ns):
                    cell_type = (cell.attrib.get("t") or "").strip()
                    value_node = cell.find("x:v", ns)
                    if value_node is None:
                        continue
                    raw = normalize_ws(value_node.text or "")
                    if not raw:
                        continue
                    if cell_type == "s":
                        try:
                            idx = int(raw)
                        except ValueError:
                            continue
                        if idx < 0 or idx >= len(shared):
                            continue
                        raw = shared[idx]
                    for match in re.findall(r"https?://[^\s\"'<>]+", raw):
                        urls.append(match.strip().rstrip("，,；;。)）]】"))
    except Exception:  # noqa: BLE001
        return []
    deduped: list[str] = []
    seen: set[str] = set()
    for url in urls:
        if not url or url in seen:
            continue
        seen.add(url)
        deduped.append(url)
    return deduped


def _infer_section_from_domain(domain: str) -> str:
    lowered = domain.lower()
    if any(key in lowered for key in ("stats.gov.cn", "cnnic.cn", "cinic.org.cn", "caam.org.cn", "gov.cn")):
        return SECTION_DATA
    if any(key in lowered for key in ("people.com.cn", "xinhuanet.com", "news.cn", "gmw.cn", "qstheory.cn", "banyuetan.org", "cyol.com", "ce.cn", "thepaper.cn", "guokr.com", "jyb.cn", "stdaily.com", "cnr.cn")):
        return SECTION_LANGUAGE
    if any(key in lowered for key in ("cctv.com", "mbalib.com", "baike.baidu.com")):
        return SECTION_JUDGMENT
    return SECTION_LANGUAGE


def _build_sources_from_seed_urls(urls: list[str]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[str]] = defaultdict(list)
    for url in urls:
        parsed = urlparse(url)
        domain = normalize_ws(parsed.netloc.lower())
        if not domain:
            continue
        section = _infer_section_from_domain(domain)
        key = (section, domain)
        grouped[key].append(url)

    sources: list[dict[str, Any]] = []
    for (section, domain), seed_urls in grouped.items():
        uniq_urls: list[str] = []
        seen: set[str] = set()
        for item in seed_urls:
            if item not in seen:
                seen.add(item)
                uniq_urls.append(item)
        sources.append(
            {
                "name": f"表格种子-{domain}",
                "section": section,
                "seed_urls": uniq_urls[:20],
                "allow_domains": [domain],
                "keywords": [],
                "path_hints": [],
            }
        )
    return sources


def ensure_catalog() -> dict[str, Any]:
    default_catalog = {"generated_at": now_iso(), "sources": DEFAULT_SOURCES}
    if not CATALOG_PATH.exists():
        write_json(CATALOG_PATH, default_catalog)
        return default_catalog
    catalog = read_json(CATALOG_PATH, default_catalog)
    changed = False

    def merge_unique_strings(existing: list[str], defaults: list[str]) -> list[str]:
        merged = [item for item in existing if item]
        seen = {item for item in merged}
        for item in defaults:
            if item and item not in seen:
                merged.append(item)
                seen.add(item)
        return merged

    existing_sources = catalog.setdefault("sources", [])
    xlsx_sources = _build_sources_from_seed_urls(_extract_urls_from_xlsx(EXTRA_SOURCE_XLSX_PATH))
    for source in [*DEFAULT_SOURCES, *xlsx_sources]:
        matched = None
        for existing_source in existing_sources:
            same_name = normalize_ws(existing_source.get("name", "")) == normalize_ws(source.get("name", ""))
            overlap_domains = set(existing_source.get("allow_domains", [])) & set(source.get("allow_domains", []))
            same_section = normalize_ws(existing_source.get("section", "")) == normalize_ws(source.get("section", ""))
            if same_name or (overlap_domains and same_section):
                matched = existing_source
                break
        if matched is None:
            existing_sources.append(source)
            changed = True
            continue

        for key in ("allow_domains", "seed_urls", "keywords", "path_hints"):
            merged_values = merge_unique_strings(list(matched.get(key, [])), list(source.get(key, [])))
            if merged_values != list(matched.get(key, [])):
                matched[key] = merged_values
                changed = True
        if not matched.get("section") and source.get("section"):
            matched["section"] = source["section"]
            changed = True
    if changed:
        catalog["generated_at"] = now_iso()
        write_json(CATALOG_PATH, catalog)
    return catalog


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.7",
        }
    )
    return session


def parse_focus_tokens(focus: str | None) -> list[str]:
    return [token.strip() for token in re.split(r"[\s,，、/]+", focus or "") if token.strip()]


def infer_requested_sections(focus_tokens: list[str]) -> set[str]:
    if not focus_tokens:
        return {SECTION_LANGUAGE, SECTION_DATA, SECTION_JUDGMENT, SECTION_COMMON}
    mapping = {
        "言语": SECTION_LANGUAGE,
        "资料": SECTION_DATA,
        "判断": SECTION_JUDGMENT,
        "定义": SECTION_JUDGMENT,
        "论证": SECTION_JUDGMENT,
        "常识": SECTION_COMMON,
        "政治": SECTION_COMMON,
    }
    sections: set[str] = set()
    for token in focus_tokens:
        for key, section in mapping.items():
            if key in token:
                sections.add(section)
    return sections or {SECTION_LANGUAGE, SECTION_DATA, SECTION_JUDGMENT, SECTION_COMMON}


def score_text(text: str, keywords: list[str], focus_tokens: list[str]) -> int:
    score = 0
    for token in keywords + focus_tokens:
        if token and token in text:
            score += 2
    return score


def is_same_domain(url: str, allow_domains: list[str]) -> bool:
    hostname = urlparse(url).netloc.lower()
    return any(hostname == domain or hostname.endswith("." + domain) for domain in allow_domains)


def is_allowed_link(url: str) -> bool:
    lowered = url.lower()
    if not lowered.startswith("http"):
        return False
    blocked_suffixes = (".jpg", ".jpeg", ".png", ".gif", ".svg", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip")
    return not lowered.endswith(blocked_suffixes)


def is_noise_article_url(url: str) -> bool:
    lowered = url.lower()
    noise_signals = [
        "forum.",
        "/forum/",
        "/bbs/",
        "/comment/",
        "/video/",
        "/live/",
    ]
    return any(signal in lowered for signal in noise_signals)


def looks_like_article_url(url: str) -> bool:
    lowered = url.lower()
    if lowered.endswith("/index.html") or lowered.endswith("/index.htm"):
        return False
    article_patterns = [
        r"/20\d{2}[-/]\d{2}[-/]\d{2}/",
        r"/n\d+/",
        r"content[_-]\d+",
        r"\d{6,}\.html",
        r"\d{6,}\.htm",
        r"/20\d{6}/[^/]+\.htm",
        r"/article/",
        r"/detail/",
        r"/item/",
    ]
    return any(re.search(pattern, lowered) for pattern in article_patterns)


def extract_candidate_links(
    html: str,
    source: dict[str, Any],
    focus_tokens: list[str],
    max_candidates: int,
) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    candidates: dict[str, dict[str, Any]] = {}
    for anchor in soup.find_all("a", href=True):
        href = urljoin(source["seed_urls"][0], anchor["href"].strip())
        if not is_allowed_link(href) or not is_same_domain(href, source["allow_domains"]):
            continue
        if is_noise_article_url(href):
            continue
        text = normalize_ws(anchor.get_text(" ", strip=True))
        if len(text) < 6:
            continue

        score = score_text(text, source.get("keywords", []), focus_tokens)
        for hint in source.get("path_hints", []):
            if hint and hint.lower() in href.lower():
                score += 1
        score += 3 if looks_like_article_url(href) else -2
        current_year = datetime.now().year
        if str(current_year) in href or str(current_year - 1) in href:
            score += 1
        if text.endswith("...") or "更多" in text:
            score -= 1
        if score <= 1:
            continue

        existing = candidates.get(href)
        if existing is None or score > existing["score"]:
            candidates[href] = {"url": href, "title": text, "score": score}
    return sorted(candidates.values(), key=lambda item: item["score"], reverse=True)[:max_candidates]


def extract_listing_links(html: str, source: dict[str, Any], max_pages: int) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    listings: dict[str, int] = {}
    for anchor in soup.find_all("a", href=True):
        href = urljoin(source["seed_urls"][0], anchor["href"].strip())
        if not is_allowed_link(href) or not is_same_domain(href, source["allow_domains"]):
            continue
        if looks_like_article_url(href):
            continue
        score = 0
        for hint in source.get("path_hints", []):
            if hint and hint.lower() in href.lower():
                score += 2
        text = normalize_ws(anchor.get_text(" ", strip=True))
        if text:
            score += 1
        if score <= 0:
            continue
        listings[href] = max(listings.get(href, 0), score)
    return [item[0] for item in sorted(listings.items(), key=lambda pair: pair[1], reverse=True)[:max_pages]]


def extract_sitemap_urls(xml_text: str, allow_domains: list[str], max_urls: int) -> list[str]:
    urls: list[str] = []
    for match in re.finditer(r"<loc>(.*?)</loc>", xml_text, flags=re.I | re.S):
        url = normalize_ws(match.group(1))
        if not url or not is_allowed_link(url) or not is_same_domain(url, allow_domains):
            continue
        if is_noise_article_url(url):
            continue
        if not looks_like_article_url(url):
            continue
        urls.append(url)
        if max_urls > 0 and len(urls) >= max_urls:
            break
    return urls


def extract_sitemap_index_urls(xml_text: str, allow_domains: list[str], max_urls: int) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for match in re.finditer(r"<loc>(.*?)</loc>", xml_text, flags=re.I | re.S):
        url = normalize_ws(match.group(1))
        lowered = url.lower()
        if not url or url in seen or not is_allowed_link(url) or not is_same_domain(url, allow_domains):
            continue
        if not lowered.endswith(".xml"):
            continue
        seen.add(url)
        urls.append(url)
        if len(urls) >= max_urls:
            break
    return urls


def extract_search_result_links(html: str, allow_domains: list[str], max_urls: int) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = normalize_ws(anchor.get("href", ""))
        if not href or href in seen:
            continue
        if not is_allowed_link(href) or not is_same_domain(href, allow_domains):
            continue
        if not looks_like_article_url(href):
            continue
        seen.add(href)
        urls.append(href)
        if len(urls) >= max_urls:
            break
    return urls


def fetch_search_article_urls(
    session: requests.Session,
    source: dict[str, Any],
    focus_tokens: list[str],
    max_urls: int,
) -> list[str]:
    domain = source["allow_domains"][0]
    current_year = datetime.now().year
    query_tokens = [*focus_tokens[:2], *source.get("keywords", [])[:4]]
    query_tokens = [token for token in query_tokens if token]
    if not query_tokens:
        query_tokens = ["评论"]
    queries = []
    for token in query_tokens:
        queries.append(f"site:{domain} {token} {current_year}")
        queries.append(f"site:{domain} {token} {current_year - 1}")
    urls: list[str] = []
    seen: set[str] = set()
    for query in queries:
        try:
            resp = session.get(
                "https://www.bing.com/search",
                params={"q": query, "count": max_urls},
                timeout=SEED_TIMEOUT_SECONDS,
            )
            resp.raise_for_status()
        except requests.RequestException:
            continue
        if getattr(resp, "apparent_encoding", None):
            resp.encoding = resp.apparent_encoding
        for url in extract_search_result_links(resp.text, source["allow_domains"], max_urls=max_urls):
            if url in seen:
                continue
            seen.add(url)
            urls.append(url)
            if len(urls) >= max_urls:
                return urls
    return urls


def fetch_sitemap_article_urls(
    session: requests.Session,
    source: dict[str, Any],
    max_urls: int,
    skip_urls: set[str] | None = None,
) -> list[str]:
    seed = source["seed_urls"][0]
    parsed = urlparse(seed)
    base = f"{parsed.scheme}://{parsed.netloc}"
    sitemap_candidates = [
        f"{base}/sitemap.xml",
        f"{base}/sitemap_index.xml",
        f"{base}/sitemap-index.xml",
    ]
    urls: list[str] = []
    seen: set[str] = set()
    explored_sitemaps: set[str] = set()
    skipped = skip_urls or set()

    def harvest_sitemap(sitemap_url: str, remaining: int) -> list[str]:
        if remaining <= 0 or sitemap_url in explored_sitemaps:
            return []
        explored_sitemaps.add(sitemap_url)
        try:
            resp = session.get(sitemap_url, timeout=SEED_TIMEOUT_SECONDS)
            resp.raise_for_status()
        except requests.RequestException:
            return []
        if getattr(resp, "apparent_encoding", None):
            resp.encoding = resp.apparent_encoding

        found_urls = extract_sitemap_urls(resp.text, source["allow_domains"], max_urls=0)
        if found_urls:
            return [url for url in found_urls if url not in skipped][:remaining]

        nested_urls: list[str] = []
        child_sitemaps = extract_sitemap_index_urls(resp.text, source["allow_domains"], max_urls=remaining)
        for child_url in child_sitemaps:
            for article_url in harvest_sitemap(child_url, remaining - len(nested_urls)):
                nested_urls.append(article_url)
                if len(nested_urls) >= remaining:
                    return nested_urls
        return nested_urls

    for sitemap_url in sitemap_candidates:
        fetched = harvest_sitemap(sitemap_url, max_urls - len(urls))
        for url in fetched:
            if url in seen:
                continue
            seen.add(url)
            urls.append(url)
            if len(urls) >= max_urls:
                return urls
    return urls


def extract_date(text: str) -> str:
    patterns = [
        r"(20\d{2}-\d{1,2}-\d{1,2})",
        r"(20\d{2}/\d{1,2}/\d{1,2})",
        r"(20\d{2}年\d{1,2}月\d{1,2}日)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return ""


def extract_article(
    session: requests.Session,
    source: dict[str, Any],
    candidate: dict[str, Any],
    focus_tokens: list[str],
) -> dict[str, Any] | None:
    try:
        resp = session.get(candidate["url"], timeout=ARTICLE_TIMEOUT_SECONDS)
        resp.raise_for_status()
    except requests.RequestException:
        return None

    if getattr(resp, "apparent_encoding", None):
        resp.encoding = resp.apparent_encoding
    soup = BeautifulSoup(resp.text, "html.parser")

    title = ""
    og_title = soup.find("meta", attrs={"property": "og:title"})
    if og_title:
        title = normalize_ws(og_title.get("content", ""))
    if not title and soup.title:
        title = normalize_ws(soup.title.get_text(" ", strip=True))
    if not title:
        title = candidate["title"]

    publish_text = " ".join(
        normalize_ws(tag.get("content", ""))
        for tag in soup.find_all("meta")
        if any(name in str(tag.attrs).lower() for name in ["publish", "date", "time"])
    )
    publish_text = publish_text or normalize_ws(soup.get_text(" ", strip=True)[:300])
    published_at = extract_date(publish_text)

    article_node = soup.find("article")
    paragraphs: list[str] = []
    if article_node:
        paragraphs = [
            normalize_ws(node.get_text(" ", strip=True))
            for node in article_node.find_all(["p", "div"])
            if len(normalize_ws(node.get_text(" ", strip=True))) >= 18
        ]
    if not paragraphs:
        selectors = ["div[class*=content]", "div[class*=article]", "div[id*=content]", "div[id*=article]", "main", "body"]
        for selector in selectors:
            node = soup.select_one(selector)
            if not node:
                continue
            paragraphs = [
                normalize_ws(p.get_text(" ", strip=True))
                for p in node.find_all("p")
                if len(normalize_ws(p.get_text(" ", strip=True))) >= 18
            ]
            if paragraphs:
                break

    table_lines: list[str] = []
    if normalize_ws(source.get("section", "")) == SECTION_DATA:
        for table in soup.find_all("table")[:12]:
            for row in table.find_all("tr")[:40]:
                cells = [normalize_ws(cell.get_text(" ", strip=True)) for cell in row.find_all(["th", "td"])]
                cells = [cell for cell in cells if len(cell) >= 1]
                if len(cells) < 2:
                    continue
                line = " | ".join(cells[:8])
                if len(line) >= 10:
                    table_lines.append(line)

        if not paragraphs:
            list_lines = [normalize_ws(li.get_text(" ", strip=True)) for li in soup.find_all("li")]
            list_lines = [line for line in list_lines if len(line) >= 18]
            if list_lines:
                paragraphs = list_lines[:20]

    combined_lines = [*paragraphs[:20], *table_lines[:60]]
    content = "\n".join(combined_lines).strip()
    source_section = normalize_ws(source.get("section", ""))
    min_content_chars = 80 if source_section == SECTION_DATA else 180
    if len(content) < min_content_chars:
        return None

    if source_section == SECTION_DATA:
        data_text = f"{title}\n{content}"
        numeric_tokens = len(re.findall(r"\d+(?:\.\d+)?", data_text))
        statistic_terms = len(
            re.findall(
                r"(亿元|万亿元|亿元人民币|万人|万台|万吨|个百分点|同比|环比|增长率|下降|上升|累计|占比|比重|指数|增速|季度|月度)",
                data_text,
            )
        )
        if numeric_tokens < 10 and statistic_terms < 2 and len(table_lines) < 3:
            return None

    combined = f"{title}\n{content}"
    relevance = candidate["score"] + score_text(combined, source.get("keywords", []), focus_tokens)
    return {
        "section": source["section"],
        "source_name": source["name"],
        "source_domain": urlparse(candidate["url"]).netloc,
        "seed_url": source["seed_urls"][0],
        "article_url": candidate["url"],
        "title": title,
        "published_at": published_at,
        "summary": normalize_ws(content[:180]),
        "content": content[:8000],
        "relevance_score": relevance,
        "fetched_at": now_iso(),
    }


def choose_sources(
    catalog: dict[str, Any],
    focus_tokens: list[str],
    section: str | None = None,
) -> list[dict[str, Any]]:
    requested_sections = {section} if section else infer_requested_sections(focus_tokens)
    candidates = [source for source in catalog.get("sources", []) if source.get("section") in requested_sections]
    if not candidates:
        candidates = list(catalog.get("sources", []))
    priority_names = {
        SECTION_LANGUAGE: ["人民网", "新华网", "光明网", "经济日报", "求是网", "中国青年报", "半月谈"],
        SECTION_JUDGMENT: ["科普中国", "央视网", "MBA智库", "百度百科"],
        SECTION_COMMON: ["中国政府网", "新华网", "人民网"],
    }
    data_domain_rank = {
        "stats.gov.cn": 0,
        "cinic.org.cn": 1,
        "caam.org.cn": 2,
        "ce.cn": 3,
        "gov.cn": 4,
        "news.cn": 5,
        "xinhuanet.com": 5,
        "cnnic.cn": 6,
        "people.com.cn": 7,
        "people.cn": 7,
        "chinajob.gov.cn": 8,
    }

    def primary_domain(source: dict[str, Any]) -> str:
        allow_domains = [normalize_ws(item).lower() for item in source.get("allow_domains", []) if normalize_ws(item)]
        if allow_domains:
            return allow_domains[0]
        seed_urls = source.get("seed_urls", [])
        if not seed_urls:
            return ""
        return urlparse(str(seed_urls[0])).netloc.lower()

    scored: list[tuple[int, int, dict[str, Any]]] = []
    for source in candidates:
        score = 0
        joined_keywords = " ".join(source.get("keywords", []))
        for token in focus_tokens:
            score += score_text(joined_keywords, source.get("keywords", []), [token])
        source_section = normalize_ws(source.get("section", ""))
        if source.get("name") in priority_names.get(source_section, []):
            score += 3
        domain = primary_domain(source)
        rank = 99
        if source_section == SECTION_DATA:
            rank = data_domain_rank.get(domain, 99)
            if rank < 99:
                # Data section needs stable high-yield domains first.
                score += max(12, 90 - rank * 8)
            else:
                score -= 6
        scored.append((score, rank, source))
    if section == SECTION_DATA:
        scored.sort(key=lambda item: (item[1], -item[0], item[2].get("name", "")))
    else:
        scored.sort(key=lambda item: (-item[0], item[1], item[2].get("name", "")))
    max_sources = 3 if section == SECTION_DATA else 16
    return [item[2] for item in scored[:max_sources]]


def load_recent_cache(hours: int, section: str | None = None) -> list[dict[str, Any]]:
    rows = load_material_library()
    if section:
        rows = [row for row in rows if normalize_ws(row.get("section", "")) == normalize_ws(section)]
    if hours <= 0:
        return []
    threshold = datetime.now().astimezone() - timedelta(hours=hours)
    cached: list[dict[str, Any]] = []
    for row in rows:
        fetched_raw = str(row.get("last_seen_at") or row.get("fetched_at") or "").strip()
        try:
            fetched = datetime.fromisoformat(fetched_raw)
        except ValueError:
            continue
        if fetched >= threshold:
            cached.append(row)
    return cached


def build_summary(
    rows: list[dict[str, Any]],
    focus: str | None,
    *,
    library_manifest: dict[str, Any] | None = None,
    live_stats: dict[str, int] | None = None,
) -> str:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["section"]].append(row)

    lines = [
        "# 联网抓取材料摘要",
        "",
        f"- 更新时间: {now_iso()}",
        f"- 本轮重点: {focus or '未指定'}",
        f"- 本轮样本数: {len(rows)}",
    ]
    if live_stats:
        lines.extend(
            [
                f"- 本轮新增入库: {live_stats.get('added_count', 0)}",
                f"- 本轮命中去重: {live_stats.get('updated_count', 0)}",
            ]
        )
    if library_manifest:
        lines.extend(
            [
                f"- 材料库累计条数: {library_manifest.get('row_count', 0)}",
                f"- 材料库累计字数: {library_manifest.get('total_chars', 0)}",
            ]
        )
    lines.append("")

    for section in [SECTION_COMMON, SECTION_LANGUAGE, SECTION_JUDGMENT, SECTION_DATA]:
        items = sorted(grouped.get(section, []), key=lambda item: item["relevance_score"], reverse=True)
        if not items:
            continue
        lines.extend([f"## {section}", ""])
        for item in items[:4]:
            lines.append(
                f"- [{item['source_name']}] {item['title']} | {item['published_at'] or '日期未识别'} | {item['article_url']}"
            )
            lines.append(f"  摘要：{item['summary']}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def crawl_sources(
    focus: str | None,
    limit: int,
    cache_hours: int,
    target_chars: int,
    section: str | None = None,
    budget_seconds: int | None = None,
    sitemap_max_urls: int = 48,
) -> tuple[list[dict[str, Any]], str]:
    existing_rows = load_material_library()
    cached_rows = load_recent_cache(hours=cache_hours, section=section)
    if cached_rows:
        library_manifest = build_material_library_manifest(existing_rows)
        summary = build_summary(cached_rows[:limit], focus, library_manifest=library_manifest)
        OUTPUT_SUMMARY.write_text(summary, encoding="utf-8")
        write_json(CRAWL_STATE_PATH, {"updated_at": now_iso(), "mode": "cache", "count": len(cached_rows[:limit])})
        return cached_rows[:limit], f"使用 {cache_hours} 小时内缓存抓取材料 {len(cached_rows[:limit])} 条"

    catalog = ensure_catalog()
    focus_tokens = parse_focus_tokens(focus)
    sources = choose_sources(catalog, focus_tokens, section=section)
    session = build_session()
    articles: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    known_urls: set[str] = set()
    for row in existing_rows:
        row_section = normalize_ws(str(row.get("section", "")))
        if section and row_section != normalize_ws(section):
            continue
        article_url = normalize_ws(str(row.get("article_url", "")))
        if article_url:
            known_urls.add(article_url)
        for extra_url in row.get("seen_urls", []) or []:
            normalized = normalize_ws(str(extra_url))
            if normalized:
                known_urls.add(normalized)
    started_at = datetime.now()
    collected_chars = 0
    if section == SECTION_LANGUAGE:
        max_candidates = 36
    elif section == SECTION_DATA:
        max_candidates = 42
    else:
        max_candidates = 10
    effective_budget_seconds = budget_seconds if (budget_seconds and budget_seconds > 0) else TOTAL_BUDGET_SECONDS
    if section == SECTION_DATA:
        per_source_budget_seconds = max(24, min(58, effective_budget_seconds // max(len(sources), 1) + 12))
        max_article_attempts_per_source = 140
        max_articles_per_source = 64
    elif section == SECTION_LANGUAGE:
        per_source_budget_seconds = max(12, min(28, effective_budget_seconds // max(len(sources), 1) + 6))
        max_article_attempts_per_source = 55
        max_articles_per_source = 28
    else:
        per_source_budget_seconds = max(8, min(18, effective_budget_seconds // max(len(sources), 1) + 4))
        max_article_attempts_per_source = 32
        max_articles_per_source = 16
    source_stats: list[dict[str, Any]] = []

    for source in sources:
        if (datetime.now() - started_at).total_seconds() >= effective_budget_seconds:
            break
        source_started_at = datetime.now()
        source_attempts = 0
        source_added = 0
        source_skipped_known = 0
        source_errors = 0

        def hit_source_limits() -> bool:
            return (
                source_attempts >= max_article_attempts_per_source
                or source_added >= max_articles_per_source
                or (datetime.now() - source_started_at).total_seconds() >= per_source_budget_seconds
            )

        sitemap_candidates: list[dict[str, Any]] = []
        if section in {SECTION_LANGUAGE, SECTION_DATA}:
            for sitemap_url in fetch_sitemap_article_urls(
                session,
                source,
                max_urls=max(sitemap_max_urls, 12),
                skip_urls=known_urls,
            ):
                sitemap_candidates.append(
                    {
                        "url": sitemap_url,
                        "title": sitemap_url.rsplit("/", 1)[-1],
                        "score": 7 if section == SECTION_DATA else 5,
                    }
                )
            search_limit = 40 if section == SECTION_DATA else 18
            for search_url in fetch_search_article_urls(session, source, focus_tokens, max_urls=search_limit):
                sitemap_candidates.append(
                    {
                        "url": search_url,
                        "title": search_url.rsplit("/", 1)[-1],
                        "score": 8 if section == SECTION_DATA else 6,
                    }
                )
        for seed_url in source.get("seed_urls", []):
            if (datetime.now() - started_at).total_seconds() >= effective_budget_seconds:
                break
            if hit_source_limits():
                break
            scoped_source = {**source, "seed_urls": [seed_url]}
            try:
                resp = session.get(seed_url, timeout=SEED_TIMEOUT_SECONDS)
                resp.raise_for_status()
            except requests.RequestException:
                source_errors += 1
                continue

            if getattr(resp, "apparent_encoding", None):
                resp.encoding = resp.apparent_encoding
            candidate_pages: list[tuple[str, str]] = [(seed_url, resp.text)]
            shared_candidates = list(sitemap_candidates)
            if section == SECTION_LANGUAGE:
                max_listing_pages = 10
            elif section == SECTION_DATA:
                max_listing_pages = 16
            else:
                max_listing_pages = 2
            for listing_url in extract_listing_links(resp.text, scoped_source, max_pages=max_listing_pages):
                if (datetime.now() - started_at).total_seconds() >= effective_budget_seconds:
                    break
                if hit_source_limits():
                    break
                try:
                    listing_resp = session.get(listing_url, timeout=SEED_TIMEOUT_SECONDS)
                    listing_resp.raise_for_status()
                except requests.RequestException:
                    source_errors += 1
                    continue
                if getattr(listing_resp, "apparent_encoding", None):
                    listing_resp.encoding = listing_resp.apparent_encoding
                candidate_pages.append((listing_url, listing_resp.text))

            for page_url, page_html in candidate_pages:
                if hit_source_limits():
                    break
                page_source = {**scoped_source, "seed_urls": [page_url]}
                candidates = extract_candidate_links(page_html, page_source, focus_tokens, max_candidates=max_candidates)
                if shared_candidates:
                    candidates = [*shared_candidates, *candidates]
                    shared_candidates = []
                for candidate in candidates:
                    if (datetime.now() - started_at).total_seconds() >= effective_budget_seconds:
                        break
                    if hit_source_limits():
                        break
                    if candidate["url"] in seen_urls:
                        continue
                    if candidate["url"] in known_urls:
                        source_skipped_known += 1
                        continue
                    source_attempts += 1
                    article = extract_article(session, page_source, candidate, focus_tokens)
                    if article is None:
                        continue
                    seen_urls.add(candidate["url"])
                    known_urls.add(candidate["url"])
                    articles.append(article)
                    source_added += 1
                    collected_chars += len(article.get("content", ""))
                    if len(articles) >= limit or collected_chars >= target_chars:
                        break
                if len(articles) >= limit or collected_chars >= target_chars:
                    break
            if len(articles) >= limit or collected_chars >= target_chars:
                break
        source_stats.append(
            {
                "name": source.get("name", "unknown"),
                "attempts": source_attempts,
                "added": source_added,
                "skipped_known": source_skipped_known,
                "errors": source_errors,
                "seconds": round((datetime.now() - source_started_at).total_seconds(), 2),
            }
        )
        if len(articles) >= limit or collected_chars >= target_chars:
            break

    articles.sort(key=lambda item: item["relevance_score"], reverse=True)
    articles = articles[:limit]
    merged_rows, merge_stats = merge_material_rows(existing_rows, articles, seen_at=now_iso())
    library_manifest = save_material_library(merged_rows)
    summary = build_summary(
        articles or merged_rows[:limit],
        focus,
        library_manifest=library_manifest,
        live_stats=merge_stats,
    )
    OUTPUT_SUMMARY.write_text(summary, encoding="utf-8")
    write_json(
        CRAWL_STATE_PATH,
        {
            "updated_at": now_iso(),
            "mode": "live",
            "count": len(articles),
            "added_count": merge_stats["added_count"],
            "updated_count": merge_stats["updated_count"],
            "target_chars": target_chars,
            "collected_chars": collected_chars,
            "library_total_count": library_manifest["row_count"],
            "section": section or "",
            "budget_seconds": effective_budget_seconds,
            "sitemap_max_urls": sitemap_max_urls,
        },
    )
    message = (
        f"实时抓取材料 {len(articles)} 条，新增入库 {merge_stats['added_count']} 条，"
        f"命中去重 {merge_stats['updated_count']} 条，累计材料 {library_manifest['row_count']} 条 / "
        f"{library_manifest['total_chars']} 字"
    )
    if source_stats:
        detail_lines = [
            (
                f"[{item['name']}] +{item['added']} / try={item['attempts']} "
                f"skip_known={item['skipped_known']} err={item['errors']} t={item['seconds']}s"
            )
            for item in source_stats[:10]
            if item["attempts"] > 0 or item["added"] > 0 or item["errors"] > 0
        ]
        if detail_lines:
            message = message + "\n" + "\n".join(detail_lines)
    return articles, message


def crawl_until_library_chars(
    *,
    section: str,
    min_chars: int,
    focus: str | None,
    per_round_limit: int,
    target_chars_per_round: int,
    round_limit: int,
    budget_seconds: int = TOTAL_BUDGET_SECONDS,
    sitemap_max_urls: int = 48,
    load_rows: Callable[[], list[dict[str, Any]]] = load_material_library,
    crawl_round: Callable[..., tuple[list[dict[str, Any]], str]] = crawl_sources,
) -> dict[str, Any]:
    rounds = 0
    previous_chars = material_char_count(load_rows(), section=section)
    current_chars = previous_chars
    messages: list[str] = []

    while current_chars < min_chars and rounds < round_limit:
        rounds += 1
        _rows, message = crawl_round(
            focus=focus,
            limit=per_round_limit,
            cache_hours=0,
            target_chars=target_chars_per_round,
            section=section,
            budget_seconds=budget_seconds,
            sitemap_max_urls=sitemap_max_urls,
        )
        current_chars = material_char_count(load_rows(), section=section)
        messages.append(f"round {rounds}: {message} | section_chars={current_chars}")
        previous_chars = current_chars

    return {
        "section": section,
        "rounds": rounds,
        "final_chars": current_chars,
        "target_chars": min_chars,
        "completed": current_chars >= min_chars,
        "messages": messages,
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(errors="replace")
        except Exception:
            pass
    parser = argparse.ArgumentParser(description="抓取公考模拟题材料来源")
    parser.add_argument("--focus", default="", help="本轮重点关键词")
    parser.add_argument("--section", default="", help="仅抓取指定模块材料")
    parser.add_argument("--limit", type=int, default=18, help="最多抓取文章数")
    parser.add_argument("--cache-hours", type=int, default=0, help="缓存有效时长")
    parser.add_argument("--target-chars", type=int, default=DEFAULT_TARGET_CHARS, help="本轮增量抓取目标字数")
    parser.add_argument("--min-library-chars", type=int, default=0, help="将指定模块材料库回填到目标字数")
    parser.add_argument("--round-limit", type=int, default=20, help="批量回填最多轮数")
    parser.add_argument("--budget-seconds", type=int, default=TOTAL_BUDGET_SECONDS, help="单轮抓取总时长预算（秒）")
    parser.add_argument("--sitemap-max-urls", type=int, default=48, help="每个来源sitemap候选URL上限")
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    focus = args.focus.strip() or None
    section = args.section.strip() or None

    if args.min_library_chars > 0:
        if not section:
            raise SystemExit("--min-library-chars 必须配合 --section 使用")
        summary = crawl_until_library_chars(
            section=section,
            min_chars=max(args.min_library_chars, 1),
            focus=focus or section,
            per_round_limit=max(args.limit, 1),
            target_chars_per_round=max(args.target_chars, 1000),
            round_limit=max(args.round_limit, 1),
            budget_seconds=max(args.budget_seconds, 1),
            sitemap_max_urls=max(args.sitemap_max_urls, 12),
        )
        print(
            f"bulk backfill: section={summary['section']} rounds={summary['rounds']} "
            f"final_chars={summary['final_chars']} target={summary['target_chars']} completed={summary['completed']}"
        )
        for line in summary["messages"][-10:]:
            print(line)
        return 0

    rows, message = crawl_sources(
        focus=focus,
        limit=max(args.limit, 1),
        cache_hours=max(args.cache_hours, 0),
        target_chars=max(args.target_chars, 1000),
        section=section,
        budget_seconds=max(args.budget_seconds, 1),
        sitemap_max_urls=max(args.sitemap_max_urls, 12),
    )
    print(message)
    print(f"实际落盘样本: {len(rows)}")
    print(f"输出文件: {OUTPUT_JSONL}")
    print(f"摘要文件: {OUTPUT_SUMMARY}")
    if rows:
        print("样本来源:")
        for row in rows[:5]:
            print(f"- {row['section']} | {row['source_name']} | {row['title']}")
    else:
        print("本轮未新增可入库材料（继续使用已有材料库）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
