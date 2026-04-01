# Gongkao Generator Rebuild Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement phase 1 of the generator rebuild by adding explicit subtype routing, mother-template prompt contracts, and veto validators for the most common teacher-reported failures.

**Architecture:** The current section planner will be upgraded so each slot carries a subtype route contract instead of only a loose family/scenario pair. Generation and repair prompts will render that route contract directly. Post-generation validators will reject language-rule mismatches, weak distractor signatures, ask-style mismatches, and pseudo-rule restatement items before release.

**Tech Stack:** Python, Flask pipeline, unittest

---

### Task 1: Add subtype route contracts

**Files:**
- Modify: `C:\Users\ZhuanZ1\Desktop\学习机\standalone_app\app.py`
- Test: `C:\Users\ZhuanZ1\Desktop\学习机\tests\test_per_question_generation.py`

- [ ] Add a route contract registry keyed by subtype.
- [ ] Extend section planning profiles to use explicit subtype ids for language, judgment, quantity, and data-analysis slots.
- [ ] Thread subtype contract fields into `build_section_question_plan()`.
- [ ] Add tests that each module now plans subtype-specific route metadata.

### Task 2: Render mother-template constraints in prompts

**Files:**
- Modify: `C:\Users\ZhuanZ1\Desktop\学习机\standalone_app\app.py`
- Test: `C:\Users\ZhuanZ1\Desktop\学习机\tests\test_per_question_generation.py`

- [ ] Extend `render_section_question_plan_block()` with subtype route details.
- [ ] Extend `build_section_generation_prompt()` and `build_single_question_repair_prompt()` with subtype-specific material form, ask-style, option, and distractor constraints.
- [ ] Add tests for language, quantity, and judgment prompt contracts.

### Task 3: Add phase-1 veto validators

**Files:**
- Modify: `C:\Users\ZhuanZ1\Desktop\学习机\standalone_app\app.py`
- Test: `C:\Users\ZhuanZ1\Desktop\学习机\tests\test_per_question_generation.py`

- [ ] Add validators for:
- [ ] language-rule-style mismatch
- [ ] language option punctuation
- [ ] multiple obvious weak distractors in language items
- [ ] ask-style mismatch for definition / translation / argument items
- [ ] quantity closure mismatch signals
- [ ] data-analysis fake-term / indicator drift signals
- [ ] Wire them into `evaluate_paper_questions()`.

### Task 4: Verify phase 1 end to end

**Files:**
- Modify: `C:\Users\ZhuanZ1\Desktop\学习机\standalone_app\app.py`
- Test: `C:\Users\ZhuanZ1\Desktop\学习机\tests\test_per_question_generation.py`

- [ ] Run targeted unit tests for the new route and validator logic.
- [ ] Run the full current regression suite.
- [ ] Run one live paper generation and inspect whether the previous common failures are reduced.

