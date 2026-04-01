# RAG Quality Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a rule-aware, source-aware RAG pipeline to the 公考学习机 so simulated questions are grounded in high-quality retrieved context and generate with higher stability and closer-to-real-exam style.

**Architecture:** Build a three-layer retrieval system: rules RAG, style/source RAG, and question-type RAG. Normalize local and crawled materials into a searchable corpus, index them with lightweight metadata-first retrieval first and optional vector retrieval second, then inject only small, high-value evidence bundles into the existing per-question generation and repair pipeline.

**Tech Stack:** Python, Flask, JSONL/SQLite, existing `standalone_app/app.py`, existing `scripts/gongkao_workflow.py`, optional embeddings layer later, unittest/pytest-style regression tests.

---

## File Structure

### New files

- `C:/Users/ZhuanZ1/Desktop/学习机/standalone_app/rag/__init__.py`
  - RAG package marker.
- `C:/Users/ZhuanZ1/Desktop/学习机/standalone_app/rag/schema.py`
  - Dataclasses / typed structures for chunks, retrieval requests, retrieval results, source bundles.
- `C:/Users/ZhuanZ1/Desktop/学习机/standalone_app/rag/extractors.py`
  - Turn rulebook, memory, question bank, crawled materials, and PDFs/docx summaries into normalized records.
- `C:/Users/ZhuanZ1/Desktop/学习机/standalone_app/rag/index_builder.py`
  - Build local retrieval corpus and indexes.
- `C:/Users/ZhuanZ1/Desktop/学习机/standalone_app/rag/retriever.py`
  - Metadata-first retrieval; later vector retrieval adapter.
- `C:/Users/ZhuanZ1/Desktop/学习机/standalone_app/rag/bundles.py`
  - Compose final prompt bundles per module/question type.
- `C:/Users/ZhuanZ1/Desktop/学习机/standalone_app/rag/storage.py`
  - Read/write retrieval corpus and optional SQLite index.
- `C:/Users/ZhuanZ1/Desktop/学习机/state/rag_config.json`
  - Retrieval settings, source weights, per-module policies.
- `C:/Users/ZhuanZ1/Desktop/学习机/state/rag_manifest.json`
  - Build metadata: version, last build time, chunk counts, source counts.
- `C:/Users/ZhuanZ1/Desktop/学习机/data/rag_corpus.jsonl`
  - Normalized chunk corpus.
- `C:/Users/ZhuanZ1/Desktop/学习机/tests/test_rag_extractors.py`
  - Tests for normalization and chunk metadata.
- `C:/Users/ZhuanZ1/Desktop/学习机/tests/test_rag_retriever.py`
  - Tests for retrieval behavior and filtering.
- `C:/Users/ZhuanZ1/Desktop/学习机/tests/test_rag_bundle_integration.py`
  - Tests for prompt bundle assembly and integration with generation flow.

### Files to modify

- `C:/Users/ZhuanZ1/Desktop/学习机/standalone_app/app.py`
  - Call retrieval at the right points and pass compact evidence bundles into learning-plan generation, paper generation, and per-question repair.
- `C:/Users/ZhuanZ1/Desktop/学习机/scripts/gongkao_workflow.py`
  - Add commands to rebuild RAG corpus/index after material refresh.
- `C:/Users/ZhuanZ1/Desktop/学习机/scripts/source_crawler.py`
  - Ensure crawled materials carry retrieval-friendly metadata.
- `C:/Users/ZhuanZ1/Desktop/学习机/state/locked_rulebook.json`
  - Add retrieval policy section if needed.
- `C:/Users/ZhuanZ1/Desktop/学习机/README.md`
  - Document build, refresh, and troubleshooting flow.

### Existing files RAG must read

- `C:/Users/ZhuanZ1/Desktop/学习机/state/rulebook.md`
- `C:/Users/ZhuanZ1/Desktop/学习机/state/locked_rulebook.json`
- `C:/Users/ZhuanZ1/Desktop/学习机/state/meta_memory.json`
- `C:/Users/ZhuanZ1/Desktop/学习机/state/applied_ability_a_meta_rules.md`
- `C:/Users/ZhuanZ1/Desktop/学习机/state/learning_packet.md`
- `C:/Users/ZhuanZ1/Desktop/学习机/data/questions.jsonl`
- `C:/Users/ZhuanZ1/Desktop/学习机/data/material_summary.md`
- `C:/Users/ZhuanZ1/Desktop/学习机/data/web_materials.jsonl`
- `C:/Users/ZhuanZ1/Desktop/学习机/data/web_material_summary.md`
- `C:/Users/ZhuanZ1/Desktop/学习机/联考A+国省考（共50套）`
- `C:/Users/ZhuanZ1/Desktop/学习机/20250916-事业单位考试辅导用书·综合应用能力（综合管理A类）2026版-印刷文件.pdf`

## Design Decisions

### Recommended approach

Use staged retrieval in this order:

1. Rules RAG
2. Module/type-specific style RAG
3. Limited source evidence bundle
4. Existing generation + validation + repair

This is the right order because the current problem is not missing content alone. The system needs stronger control over style, structure, source domain, and question-type fit.

### What not to do first

- Do not start with model fine-tuning.
- Do not dump the entire question bank into every prompt.
- Do not retrieve the “most similar question text” directly for generation.
- Do not replace current validation gates with RAG. Retrieval improves input quality; validation still decides release.

### Retrieval layers

#### Layer 1: Rules RAG

Retrieve:

- rulebook constraints
- recent reinforce / avoid signals
- source restrictions
- applied ability meta-rules

Purpose:

- Tell the model what kind of question to generate.
- Tell the model what not to do.

#### Layer 2: Style/source RAG

Retrieve:

- short excerpts from official or target-style materials
- writing style signatures
- source-domain evidence by module

Purpose:

- Make the text feel like real exam materials.

#### Layer 3: Question-type RAG

Retrieve:

- examples of the correct ability skeleton, not near-duplicate wording
- metadata describing the target type such as “定义判断”, “逻辑填空”, “现期比重”, “加强削弱”

Purpose:

- Ground the generation in the right testing pattern.

## Retrieval Policy

### Corpus chunk types

Every chunk should carry:

- `chunk_id`
- `source_path`
- `source_kind` (`rule`, `memory`, `question`, `article`, `crawler`, `pdf_summary`, `learning_packet`)
- `module` (`常识`, `言语`, `数量`, `判断`, `资料`, `综合`)
- `question_type`
- `source_domain`
- `style_tags`
- `difficulty_hint`
- `content`
- `anti_copy_risk`
- `usable_for_generation`

### Source-domain mapping

- 言语: 人民网 / 新华网 / 光明网 / 求是网 / 中国政府网 / 半月谈 / 中青报 / 经济日报 / 澎湃 / 果壳
- 资料: 统计局 / 部委网站 / CNNIC / 政府工作报告 / 行业协会 / 产业信息网站
- 判断-定义: MBA 智库 / 规范释义 / 百科类定义材料
- 判断-论证: 官媒评论 / 科普中国 / 中国政府网 / 新华网 / 光明网 / 人民网
- 常识: 法规、政策、历史文化、科技原理类来源

### Prompt budget policy

Per generation unit, retrieve:

- 规则片段: 3-5 条
- 样式片段: 2-4 条
- 题型骨架片段: 2-3 条

Hard cap:

- Never exceed a compact evidence bundle of roughly 1,200 to 1,800 Chinese characters per question group.

### Anti-copy policy

- Do not retrieve high-overlap raw question text as direct generation context.
- Prefer structure summaries and style excerpts over entire original question stems.
- Keep the existing originality checker after generation.

## Implementation Tasks

### Task 1: Define RAG spec and retrieval boundaries

**Files:**
- Create: `C:/Users/ZhuanZ1/Desktop/学习机/standalone_app/rag/schema.py`
- Create: `C:/Users/ZhuanZ1/Desktop/学习机/state/rag_config.json`
- Modify: `C:/Users/ZhuanZ1/Desktop/学习机/README.md`
- Test: `C:/Users/ZhuanZ1/Desktop/学习机/tests/test_rag_extractors.py`

- [ ] **Step 1: Write the failing schema/config test**

```python
def test_rag_config_contains_required_layers():
    from pathlib import Path
    import json
    config = json.loads(Path("state/rag_config.json").read_text(encoding="utf-8"))
    assert "rules_rag" in config
    assert "style_rag" in config
    assert "type_rag" in config
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_rag_extractors -v`
Expected: FAIL because config/schema do not exist yet.

- [ ] **Step 3: Add minimal schema/config**

Define retrieval request/result objects and initial `rag_config.json` with:

- enabled flag
- source weights
- per-module retrieval counts
- anti-copy settings

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_rag_extractors -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add standalone_app/rag/schema.py state/rag_config.json tests/test_rag_extractors.py README.md
git commit -m "feat: add rag schema and config scaffold"
```

### Task 2: Normalize rule and memory sources into corpus records

**Files:**
- Create: `C:/Users/ZhuanZ1/Desktop/学习机/standalone_app/rag/extractors.py`
- Create: `C:/Users/ZhuanZ1/Desktop/学习机/data/rag_corpus.jsonl`
- Test: `C:/Users/ZhuanZ1/Desktop/学习机/tests/test_rag_extractors.py`

- [ ] **Step 1: Write failing extraction tests for rulebook and memory**

```python
def test_extract_rule_chunks_marks_source_kind_rule():
    from standalone_app.rag.extractors import extract_rule_chunks
    chunks = extract_rule_chunks()
    assert chunks
    assert all(chunk.source_kind == "rule" for chunk in chunks)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_rag_extractors -v`
Expected: FAIL because extractor does not exist.

- [ ] **Step 3: Implement minimal rule/memory extraction**

Extract from:

- `state/rulebook.md`
- `state/locked_rulebook.json`
- `state/meta_memory.json`
- `state/applied_ability_a_meta_rules.md`
- `state/learning_packet.md`

Chunk by short sections, not whole files.

- [ ] **Step 4: Run tests**

Run: `python -m unittest tests.test_rag_extractors -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add standalone_app/rag/extractors.py data/rag_corpus.jsonl tests/test_rag_extractors.py
git commit -m "feat: extract rule and memory chunks for rag"
```

### Task 3: Normalize question bank and source materials into typed chunks

**Files:**
- Modify: `C:/Users/ZhuanZ1/Desktop/学习机/standalone_app/rag/extractors.py`
- Modify: `C:/Users/ZhuanZ1/Desktop/学习机/data/rag_corpus.jsonl`
- Test: `C:/Users/ZhuanZ1/Desktop/学习机/tests/test_rag_extractors.py`

- [ ] **Step 1: Write failing tests for question and web material extraction**

```python
def test_question_chunks_have_module_and_type():
    from standalone_app.rag.extractors import extract_question_chunks
    chunks = extract_question_chunks(limit=5)
    assert chunks
    assert all(chunk.module for chunk in chunks)
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m unittest tests.test_rag_extractors -v`
Expected: FAIL for missing extraction paths.

- [ ] **Step 3: Implement extraction**

Sources:

- `data/questions.jsonl`
- `data/web_materials.jsonl`
- `data/material_summary.md`
- optionally summary slices for PDF/docx materials

Rules:

- question chunks should store skeleton summaries, not full near-copy stems where anti-copy risk is high
- article chunks should preserve source-domain/style metadata

- [ ] **Step 4: Run tests**

Run: `python -m unittest tests.test_rag_extractors -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add standalone_app/rag/extractors.py data/rag_corpus.jsonl tests/test_rag_extractors.py
git commit -m "feat: add question and source material extraction for rag"
```

### Task 4: Build local retrieval index and manifest

**Files:**
- Create: `C:/Users/ZhuanZ1/Desktop/学习机/standalone_app/rag/storage.py`
- Create: `C:/Users/ZhuanZ1/Desktop/学习机/standalone_app/rag/index_builder.py`
- Create: `C:/Users/ZhuanZ1/Desktop/学习机/state/rag_manifest.json`
- Modify: `C:/Users/ZhuanZ1/Desktop/学习机/scripts/gongkao_workflow.py`
- Test: `C:/Users/ZhuanZ1/Desktop/学习机/tests/test_rag_extractors.py`

- [ ] **Step 1: Write failing tests for corpus build**

```python
def test_build_rag_corpus_writes_manifest(tmp_path):
    from standalone_app.rag.index_builder import build_rag_index
    manifest = build_rag_index()
    assert manifest["chunk_count"] > 0
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m unittest tests.test_rag_extractors -v`
Expected: FAIL

- [ ] **Step 3: Implement builder**

Requirements:

- rebuild `data/rag_corpus.jsonl`
- write `state/rag_manifest.json`
- include chunk counts by source kind/module
- add a workflow CLI command like `build-rag`

- [ ] **Step 4: Run tests**

Run: `python -m unittest tests.test_rag_extractors -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add standalone_app/rag/storage.py standalone_app/rag/index_builder.py scripts/gongkao_workflow.py state/rag_manifest.json tests/test_rag_extractors.py
git commit -m "feat: add rag index builder and manifest"
```

### Task 5: Implement metadata-first retrieval

**Files:**
- Create: `C:/Users/ZhuanZ1/Desktop/学习机/standalone_app/rag/retriever.py`
- Test: `C:/Users/ZhuanZ1/Desktop/学习机/tests/test_rag_retriever.py`

- [ ] **Step 1: Write failing retrieval tests**

```python
def test_retriever_filters_by_module_and_source_kind():
    from standalone_app.rag.retriever import RagRetriever
    retriever = RagRetriever()
    results = retriever.retrieve(module="资料", layer="style_rag", top_k=3)
    assert len(results) <= 3
    assert all(result.module in ("资料", "综合") for result in results)
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m unittest tests.test_rag_retriever -v`
Expected: FAIL

- [ ] **Step 3: Implement retriever**

Phase 1 behavior:

- exact filter by module/question type/source domain
- simple ranking with weighted keyword matches and source priority
- suppress chunks with `anti_copy_risk` above threshold when generation mode is `creative`

- [ ] **Step 4: Run tests**

Run: `python -m unittest tests.test_rag_retriever -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add standalone_app/rag/retriever.py tests/test_rag_retriever.py
git commit -m "feat: add metadata-first rag retriever"
```

### Task 6: Implement bundle composer for each generation stage

**Files:**
- Create: `C:/Users/ZhuanZ1/Desktop/学习机/standalone_app/rag/bundles.py`
- Test: `C:/Users/ZhuanZ1/Desktop/学习机/tests/test_rag_bundle_integration.py`

- [ ] **Step 1: Write failing bundle tests**

```python
def test_question_bundle_contains_rule_style_and_type_sections():
    from standalone_app.rag.bundles import build_question_bundle
    bundle = build_question_bundle(module="判断", question_type="定义判断")
    assert "规则约束" in bundle
    assert "样式参考" in bundle
    assert "题型骨架" in bundle
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m unittest tests.test_rag_bundle_integration -v`
Expected: FAIL

- [ ] **Step 3: Implement bundle composer**

Required bundle shapes:

- learning-plan bundle
- whole-paper planning bundle
- per-question generation bundle
- per-question repair bundle
- data-analysis material bundle

- [ ] **Step 4: Run tests**

Run: `python -m unittest tests.test_rag_bundle_integration -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add standalone_app/rag/bundles.py tests/test_rag_bundle_integration.py
git commit -m "feat: add rag bundle composer"
```

### Task 7: Integrate RAG into learning-plan generation

**Files:**
- Modify: `C:/Users/ZhuanZ1/Desktop/学习机/standalone_app/app.py`
- Test: `C:/Users/ZhuanZ1/Desktop/学习机/tests/test_rag_bundle_integration.py`

- [ ] **Step 1: Write failing integration test**

```python
def test_learning_plan_prompt_receives_rag_bundle():
    # assert prompt assembly includes retrieved bundle text
    ...
```

- [ ] **Step 2: Run test to verify failure**

Run: `python -m unittest tests.test_rag_bundle_integration -v`
Expected: FAIL

- [ ] **Step 3: Minimal implementation**

Inject:

- rules RAG
- current feedback summary
- target source-domain hints

Do not inject raw huge corpora.

- [ ] **Step 4: Run tests**

Run: `python -m unittest tests.test_rag_bundle_integration -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add standalone_app/app.py tests/test_rag_bundle_integration.py
git commit -m "feat: add rag support to learning plan generation"
```

### Task 8: Integrate RAG into whole-paper planning, not direct whole-paper wording

**Files:**
- Modify: `C:/Users/ZhuanZ1/Desktop/学习机/standalone_app/app.py`
- Test: `C:/Users/ZhuanZ1/Desktop/学习机/tests/test_rag_bundle_integration.py`

- [ ] **Step 1: Write failing test**

```python
def test_paper_planning_uses_module_specific_rag():
    ...
```

- [ ] **Step 2: Run test**

Run: `python -m unittest tests.test_rag_bundle_integration -v`
Expected: FAIL

- [ ] **Step 3: Implement**

Use RAG to plan:

- section blueprint
- style constraints
- module-specific source hints

Do not use this stage to retrieve near-duplicate raw questions.

- [ ] **Step 4: Run test**

Run: `python -m unittest tests.test_rag_bundle_integration -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add standalone_app/app.py tests/test_rag_bundle_integration.py
git commit -m "feat: add rag to paper planning stage"
```

### Task 9: Integrate RAG into per-question generation and repair

**Files:**
- Modify: `C:/Users/ZhuanZ1/Desktop/学习机/standalone_app/app.py`
- Test: `C:/Users/ZhuanZ1/Desktop/学习机/tests/test_per_question_generation.py`
- Test: `C:/Users/ZhuanZ1/Desktop/学习机/tests/test_rag_bundle_integration.py`

- [ ] **Step 1: Write failing tests**

```python
def test_failed_question_repair_uses_question_specific_rag_bundle():
    ...
```

- [ ] **Step 2: Run tests**

Run: `python -m unittest discover -s tests -p "test_*.py"`
Expected: FAIL

- [ ] **Step 3: Implement**

Per-question generation must receive:

- exact module/type rule bundle
- style/source excerpts
- anti-pattern warnings from recent feedback

Per-question repair must receive:

- original failure reason
- tighter question-specific retrieval
- instruction to preserve intent while fixing only the failing property

- [ ] **Step 4: Run tests**

Run: `python -m unittest discover -s tests -p "test_*.py"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add standalone_app/app.py tests/test_per_question_generation.py tests/test_rag_bundle_integration.py
git commit -m "feat: add rag to per-question generation and repair"
```

### Task 10: Add retrieval build hooks to material refresh workflow

**Files:**
- Modify: `C:/Users/ZhuanZ1/Desktop/学习机/scripts/gongkao_workflow.py`
- Modify: `C:/Users/ZhuanZ1/Desktop/学习机/standalone_app/app.py`
- Test: `C:/Users/ZhuanZ1/Desktop/学习机/tests/test_rag_extractors.py`

- [ ] **Step 1: Write failing test**

```python
def test_refresh_workflow_rebuilds_rag_manifest():
    ...
```

- [ ] **Step 2: Run test**

Run: `python -m unittest tests.test_rag_extractors -v`
Expected: FAIL

- [ ] **Step 3: Implement**

Trigger order:

1. refresh materials
2. sync learning packet
3. rebuild rag corpus/index
4. update manifest timestamp

- [ ] **Step 4: Run tests**

Run: `python -m unittest tests.test_rag_extractors -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/gongkao_workflow.py standalone_app/app.py tests/test_rag_extractors.py
git commit -m "feat: rebuild rag index during refresh workflow"
```

### Task 11: Add observability for retrieval decisions

**Files:**
- Modify: `C:/Users/ZhuanZ1/Desktop/学习机/standalone_app/app.py`
- Possibly create: `C:/Users/ZhuanZ1/Desktop/学习机/output/rag_debug/`
- Test: `C:/Users/ZhuanZ1/Desktop/学习机/tests/test_rag_bundle_integration.py`

- [ ] **Step 1: Write failing test**

```python
def test_generation_result_contains_rag_debug_summary():
    ...
```

- [ ] **Step 2: Run test**

Run: `python -m unittest tests.test_rag_bundle_integration -v`
Expected: FAIL

- [ ] **Step 3: Implement**

Record for each generation:

- selected chunk ids
- layer counts
- source domains used
- whether anti-copy suppression triggered

Expose a compact summary to the frontend/session state.

- [ ] **Step 4: Run tests**

Run: `python -m unittest tests.test_rag_bundle_integration -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add standalone_app/app.py tests/test_rag_bundle_integration.py
git commit -m "feat: add rag debug summary to generation flow"
```

### Task 12: Optional vector retrieval phase

**Files:**
- Modify: `C:/Users/ZhuanZ1/Desktop/学习机/standalone_app/rag/retriever.py`
- Possibly create: `C:/Users/ZhuanZ1/Desktop/学习机/standalone_app/rag/embeddings.py`
- Modify: `C:/Users/ZhuanZ1/Desktop/学习机/state/rag_config.json`
- Test: `C:/Users/ZhuanZ1/Desktop/学习机/tests/test_rag_retriever.py`

- [ ] **Step 1: Write a skipped/pending test for vector mode**

```python
def test_vector_mode_respects_same_filters():
    ...
```

- [ ] **Step 2: Keep disabled by default**

No production switch until metadata-first retrieval is stable.

- [ ] **Step 3: Implement only if phase 1 is stable**

Support:

- optional embeddings build
- blended score = metadata score + vector score

- [ ] **Step 4: Run tests**

Run: `python -m unittest tests.test_rag_retriever -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add standalone_app/rag/retriever.py standalone_app/rag/embeddings.py state/rag_config.json tests/test_rag_retriever.py
git commit -m "feat: add optional vector retrieval mode"
```

## Acceptance Criteria

The RAG upgrade is complete only when all of the following are true:

1. Material refresh also rebuilds the retrieval corpus and manifest.
2. Generation logs show which rule/style/type chunks were used.
3. Each module retrieves only module-appropriate evidence.
4. The originality checker still passes on generated papers.
5. Current length and structure validators still run unchanged.
6. Whole-paper success rate improves versus the current baseline.
7. At least one real generated paper is published with RAG enabled and passes final validation.

## Rollout Strategy

### Phase 1

- Metadata-first retrieval only
- No vectors
- RAG enabled for learning plan and per-question repair first

### Phase 2

- Enable per-question generation RAG
- Keep paper-planning RAG lightweight

### Phase 3

- Add vector retrieval only if phase 2 quality gains plateau

## Risks and Mitigations

### Risk: Retrieval makes copying worse

Mitigation:

- Store anti-copy risk on chunks
- Suppress high-overlap raw question text
- Keep originality check mandatory

### Risk: Prompt becomes too long

Mitigation:

- Strict evidence bundle caps
- Separate retrieval by layer
- Summarize chunks before prompt injection

### Risk: Retrieval returns wrong module/style

Mitigation:

- Strong metadata schema
- Per-module filtering tests
- Source-domain whitelists

### Risk: Engineering complexity balloons

Mitigation:

- Phase 1 stays metadata-first
- Use JSONL/SQLite before any heavier infrastructure
- No fine-tuning in this project stage

## Verification Commands

Run all of these before claiming completion:

```bash
python -m unittest tests.test_rag_extractors -v
python -m unittest tests.test_rag_retriever -v
python -m unittest tests.test_rag_bundle_integration -v
python -m unittest discover -s tests -p "test_*.py"
python -m py_compile standalone_app/app.py scripts/gongkao_workflow.py
python scripts/gongkao_workflow.py build-rag
```

If a real-model verification run is available, also run:

```bash
@'
import standalone_app.app as app_mod
paper_path, _paper_content, validation = app_mod.generate_valid_paper(
    provider='ollama',
    api_key='',
    model='gpt-oss:120b-cloud',
    focus=None,
)
print(str(paper_path))
print(validation)
'@ | python -
```

## Recommended Execution Order

1. Task 1 through Task 4
2. Task 5 and Task 6
3. Task 7 through Task 10
4. Task 11
5. Task 12 only if needed

## Expected Outcome

After this plan is implemented, the system should no longer rely on “the model vaguely remembers what a公考题 looks like.” Instead, every generation step will receive targeted, rule-aware, source-aware, question-type-aware evidence, while the existing validation stack continues to reject short, structurally bad, or overly derivative questions.
