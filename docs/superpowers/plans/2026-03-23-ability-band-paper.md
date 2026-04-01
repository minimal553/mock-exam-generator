# Ability-Band Paper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add whole-paper `LOW/MID/HIGH/VERY_HIGH` difficulty planning with an overall upward shift, ban graphic reasoning items, and improve release success rate without sacrificing paper quality.

**Architecture:** The paper pipeline will assign target bands per question slot, thread those targets into generation and repair prompts, preserve the mapping through repair, and evaluate final papers with a split hard-failure vs soft-warning quality model. Whole-paper distribution is soft-targeted but globally shifted upward by one level so release success stays high while paper difficulty more closely matches the user's target.

**Tech Stack:** Python, Flask app pipeline, unittest, Ollama/OpenAI provider abstraction

---

### Task 1: Add whole-paper band planning and mapping

**Files:**
- Modify: `C:\Users\ZhuanZ1\Desktop\学习机\standalone_app\app.py`
- Test: `C:\Users\ZhuanZ1\Desktop\学习机\tests\test_per_question_generation.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_plan_question_bands_soft_targets():
    bands = app_mod.plan_question_bands(20)
    assert len(bands) == 20
    assert bands.count("LOW") == 0
    assert bands.count("MID") == 6
    assert bands.count("HIGH") == 11
    assert bands.count("VERY_HIGH") == 3

def test_plan_question_bands_non_20_count_is_normalized():
    bands = app_mod.plan_question_bands(17)
    assert len(bands) == 17

def test_build_question_band_plan_maps_question_numbers():
    plan = app_mod.build_question_band_plan(20)
    assert plan[1] in {"LOW", "MID", "HIGH"}
    assert len(plan) == 20
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_per_question_generation.PerQuestionRepairTests.test_plan_question_bands_soft_targets tests.test_per_question_generation.PerQuestionRepairTests.test_plan_question_bands_non_20_count_is_normalized tests.test_per_question_generation.PerQuestionRepairTests.test_build_question_band_plan_maps_question_numbers -v`
Expected: FAIL because helpers do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
def plan_question_bands(question_count: int) -> list[str]:
    ...

def build_question_band_plan(question_count: int) -> dict[int, str]:
    ...
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_per_question_generation.PerQuestionRepairTests.test_plan_question_bands_soft_targets tests.test_per_question_generation.PerQuestionRepairTests.test_plan_question_bands_non_20_count_is_normalized tests.test_per_question_generation.PerQuestionRepairTests.test_build_question_band_plan_maps_question_numbers -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add standalone_app/app.py tests/test_per_question_generation.py
git commit -m "feat: add whole-paper ability band planning"
```

### Task 2: Ban graphic reasoning in prompts and validators

**Files:**
- Modify: `C:\Users\ZhuanZ1\Desktop\学习机\standalone_app\app.py`
- Test: `C:\Users\ZhuanZ1\Desktop\学习机\tests\test_per_question_generation.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_section_prompt_bans_graphic_reasoning():
    prompt = app_mod.build_section_generation_prompt(...)
    assert "图形推断" in prompt
    assert "禁止" in prompt

def test_evaluate_paper_questions_rejects_graphic_reasoning():
    paper = {...}
    issues = app_mod.evaluate_paper_questions(paper)
    assert "图形" in " | ".join(issues[(0, 0)])

def test_evaluate_paper_questions_allows_text_only_reasoning():
    paper = {...}
    issues = app_mod.evaluate_paper_questions(paper)
    assert "图形" not in " | ".join(issues.get((0, 0), []))

def test_evaluate_paper_questions_rejects_image_dependent_non_data_item():
    paper = {...}
    issues = app_mod.evaluate_paper_questions(paper)
    assert "图形" in " | ".join(issues[(0, 0)])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_per_question_generation.PerQuestionRepairTests.test_section_prompt_bans_graphic_reasoning tests.test_per_question_generation.PerQuestionRepairTests.test_evaluate_paper_questions_rejects_graphic_reasoning tests.test_per_question_generation.PerQuestionRepairTests.test_evaluate_paper_questions_allows_text_only_reasoning tests.test_per_question_generation.PerQuestionRepairTests.test_evaluate_paper_questions_rejects_image_dependent_non_data_item -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
def detect_banned_item_type(...):
    ...
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_per_question_generation.PerQuestionRepairTests.test_section_prompt_bans_graphic_reasoning tests.test_per_question_generation.PerQuestionRepairTests.test_evaluate_paper_questions_rejects_graphic_reasoning tests.test_per_question_generation.PerQuestionRepairTests.test_evaluate_paper_questions_allows_text_only_reasoning tests.test_per_question_generation.PerQuestionRepairTests.test_evaluate_paper_questions_rejects_image_dependent_non_data_item -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add standalone_app/app.py tests/test_per_question_generation.py
git commit -m "feat: ban graphic reasoning items"
```

### Task 3: Thread target bands into section generation and preserve mapping

**Files:**
- Modify: `C:\Users\ZhuanZ1\Desktop\学习机\standalone_app\app.py`
- Test: `C:\Users\ZhuanZ1\Desktop\学习机\tests\test_per_question_generation.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_section_generation_prompt_includes_band_targets():
    prompt = app_mod.build_section_generation_prompt(...)
    assert "LOW" in prompt or "MID" in prompt or "HIGH" in prompt

def test_generate_initial_paper_by_sections_preserves_band_mapping():
    paper, candidate_count, band_map = app_mod.generate_initial_paper_by_sections(...)
    assert candidate_count == 20
    assert len(band_map) == 20

def test_generate_valid_paper_preserves_band_mapping_through_repairs():
    ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_per_question_generation.PerQuestionRepairTests.test_section_generation_prompt_includes_band_targets tests.test_per_question_generation.PerQuestionRepairTests.test_generate_initial_paper_by_sections_preserves_band_mapping tests.test_per_question_generation.PerQuestionRepairTests.test_generate_valid_paper_preserves_band_mapping_through_repairs -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
def build_section_generation_prompt(..., target_bands: list[str]) -> str:
    ...

def generate_initial_paper_by_sections(...) -> tuple[dict[str, Any], int, dict[int, str]]:
    ...
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_per_question_generation.PerQuestionRepairTests.test_section_generation_prompt_includes_band_targets tests.test_per_question_generation.PerQuestionRepairTests.test_generate_initial_paper_by_sections_preserves_band_mapping tests.test_per_question_generation.PerQuestionRepairTests.test_generate_valid_paper_preserves_band_mapping_through_repairs -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add standalone_app/app.py tests/test_per_question_generation.py
git commit -m "feat: add band targets to section prompts"
```

### Task 4: Make repair prompts band-aware and ban-aware

**Files:**
- Modify: `C:\Users\ZhuanZ1\Desktop\学习机\standalone_app\app.py`
- Test: `C:\Users\ZhuanZ1\Desktop\学习机\tests\test_per_question_generation.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_single_question_repair_prompt_includes_target_band():
    prompt = app_mod.build_single_question_repair_prompt(...)
    assert "Target band" in prompt

def test_repair_prompt_restates_graphic_reasoning_ban():
    prompt = app_mod.build_single_question_repair_prompt(...)
    assert "图形推断" in prompt

def test_section_repair_prompt_includes_band_targets_and_graphic_ban():
    prompt = app_mod.build_section_repair_prompt(...)
    assert "Target bands" in prompt
    assert "图形推断" in prompt

def test_graphic_reasoning_issue_triggers_repair():
    ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_per_question_generation.PerQuestionRepairTests.test_single_question_repair_prompt_includes_target_band tests.test_per_question_generation.PerQuestionRepairTests.test_repair_prompt_restates_graphic_reasoning_ban tests.test_per_question_generation.PerQuestionRepairTests.test_section_repair_prompt_includes_band_targets_and_graphic_ban tests.test_per_question_generation.PerQuestionRepairTests.test_graphic_reasoning_issue_triggers_repair -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# pass band metadata and banned-type guidance into repair prompts
...
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_per_question_generation.PerQuestionRepairTests.test_single_question_repair_prompt_includes_target_band tests.test_per_question_generation.PerQuestionRepairTests.test_repair_prompt_restates_graphic_reasoning_ban tests.test_per_question_generation.PerQuestionRepairTests.test_section_repair_prompt_includes_band_targets_and_graphic_ban tests.test_per_question_generation.PerQuestionRepairTests.test_graphic_reasoning_issue_triggers_repair -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add standalone_app/app.py tests/test_per_question_generation.py
git commit -m "feat: make repairs band-aware and ban-aware"
```

### Task 5: Add band-estimation and release thresholds

**Files:**
- Modify: `C:\Users\ZhuanZ1\Desktop\学习机\standalone_app\app.py`
- Test: `C:\Users\ZhuanZ1\Desktop\学习机\tests\test_per_question_generation.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_evaluate_release_quality_warns_on_band_distribution_drift():
    ...

def test_evaluate_release_quality_blocks_on_excessive_band_drift():
    ...

def test_generate_valid_paper_does_not_fail_on_soft_band_drift_only():
    ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_per_question_generation.PerQuestionRepairTests.test_evaluate_release_quality_warns_on_band_distribution_drift tests.test_per_question_generation.PerQuestionRepairTests.test_evaluate_release_quality_blocks_on_excessive_band_drift tests.test_per_question_generation.PerQuestionRepairTests.test_generate_valid_paper_does_not_fail_on_soft_band_drift_only -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
def estimate_question_band(...):
    ...

def evaluate_band_distribution(...):
    ...
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_per_question_generation.PerQuestionRepairTests.test_evaluate_release_quality_warns_on_band_distribution_drift tests.test_per_question_generation.PerQuestionRepairTests.test_evaluate_release_quality_blocks_on_excessive_band_drift tests.test_per_question_generation.PerQuestionRepairTests.test_generate_valid_paper_does_not_fail_on_soft_band_drift_only -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add standalone_app/app.py tests/test_per_question_generation.py
git commit -m "feat: warn and block by band drift thresholds"
```

### Task 6: Verify parallel generation remains intact

**Files:**
- Modify: `C:\Users\ZhuanZ1\Desktop\学习机\standalone_app\app.py`
- Test: `C:\Users\ZhuanZ1\Desktop\学习机\tests\test_per_question_generation.py`

- [ ] **Step 1: Write the failing deterministic test**

```python
def test_generate_initial_paper_by_sections_keeps_parallel_section_generation():
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_per_question_generation.PerQuestionRepairTests.test_generate_initial_paper_by_sections_keeps_parallel_section_generation -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# preserve existing parallel batching while passing band targets
...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_per_question_generation.PerQuestionRepairTests.test_generate_initial_paper_by_sections_keeps_parallel_section_generation -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add standalone_app/app.py tests/test_per_question_generation.py
git commit -m "perf: preserve parallel section generation with band logic"
```

### Task 7: Run regression and optional live probe

**Files:**
- Modify: `C:\Users\ZhuanZ1\Desktop\学习机\standalone_app\app.py`
- Test: `C:\Users\ZhuanZ1\Desktop\学习机\tests\test_per_question_generation.py`

- [ ] **Step 1: Run targeted tests**

Run: `python -m unittest tests.test_per_question_generation -v`
Expected: PASS

- [ ] **Step 2: Run broader regression**

Run: `python -m unittest tests.test_per_question_generation tests.test_rag_extractors tests.test_rag_retriever tests.test_rag_bundle_integration tests.test_ollama_provider -v`
Expected: PASS

- [ ] **Step 3: Optionally run a live section probe**

Run:

```bash
python - <<'PY'
from pathlib import Path
import standalone_app.app as app
prompt = app.build_section_generation_prompt(
    focus='判断推理',
    paper_id='plan-probe',
    generated_at=app.now_iso(),
    rulebook_version='vplan',
    section_name='判断推理',
    section_count=2,
    start_number=13,
    target_bands=['MID', 'HIGH'],
)
text = app.call_ollama(prompt=prompt, model='gpt-oss:120b-cloud')
Path('output/mock_tests/_band_probe.md').write_text(text, encoding='utf-8')
print('saved')
PY
```

Expected: saved

- [ ] **Step 4: Optionally verify probe parses**

Run:

```bash
python - <<'PY'
from pathlib import Path
import standalone_app.app as app
text = Path('output/mock_tests/_band_probe.md').read_text(encoding='utf-8')
question_lines, answer_map, note_map = app.parse_repair_payload(text)
print(bool(question_lines), sorted(answer_map), sorted(note_map))
PY
```

Expected: `True` plus parsed answer/note keys

- [ ] **Step 5: Commit**

```bash
git add standalone_app/app.py tests/test_per_question_generation.py docs/superpowers/specs/2026-03-23-ability-band-paper-design.md docs/superpowers/plans/2026-03-23-ability-band-paper.md
git commit -m "feat: add ability-band paper generation"
```
