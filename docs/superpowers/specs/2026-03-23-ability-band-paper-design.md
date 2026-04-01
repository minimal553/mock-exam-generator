# Ability-Band Paper Design

**Date:** 2026-03-23

**Goal:** Make 20-question mock papers feel closer to real public-service aptitude exams by controlling whole-paper difficulty distribution, banning graphic-reasoning items, and preserving release success rate.

## Scope

This design changes only the mock-paper generation pipeline in `standalone_app/app.py` and its tests. It does not redesign the UI, RAG pipeline, or external model provider abstraction.

## Decisions

### 1. Difficulty model

The system will not use IQ labels in prompts or output. Internally it will use four whole-paper ability bands:

- `LOW`
- `MID`
- `HIGH`
- `VERY_HIGH`

Default target distribution for a 20-question paper:

- `LOW`: `0` questions by default after the global difficulty shift
- `MID`: 30% (`6` questions)
- `HIGH`: 55% (`11` questions)
- `VERY_HIGH`: 15% (`3` questions)

This is a soft target, not a hard lock. The default paper is intentionally shifted upward by one band overall, and whole-paper generation may drift slightly when needed to preserve release success rate.

Target tolerance:

- For 20-question papers, each band may drift by up to `±1` question without warning.
- Drift beyond `±1` but within `±2` becomes a soft warning.
- Drift beyond `±2` becomes a release-blocking hard failure.

For non-20-question papers, counts are derived by rounded proportions, then normalized to total count, with the same tolerance semantics scaled to at least `1` question.

### 2. Whole-paper control, not per-module hard quotas

Distribution is controlled at the whole-paper level. Modules do not each receive their own strict band quotas. This avoids distorting small modules such as data analysis and keeps papers closer to real exam structure.

### 3. Banned item types

Graphic reasoning is banned outright. The system must reject or avoid:

- 图形推断
- 看图推理
- 依赖图像或图形本体才能作答的非资料分析题

Judgment/reasoning remains text-only:

- 定义判断
- 类比推理
- 逻辑判断
- 论证类题

### 4. Generation strategy

Each generated question slot receives a target band before generation. Section prompts and repair prompts should explicitly mention the slot band and the ban on graphic reasoning when relevant.

The pipeline must maintain a concrete `question_number -> target_band` mapping through:

- initial section generation
- question repair
- section repair
- final release evaluation

### 5. Review strategy

Difficulty mismatch is treated as a soft quality issue, not an automatic release blocker. True structural/content failures remain hard blockers:

- missing answers
- placeholder options
- missing explanations
- broken section/material structure
- wrong question count
- banned graphic reasoning

### 6. Success-rate protection

The release gate must preserve quality without turning every heuristic miss into a full-paper failure. Band mismatch and some explanation-style misses should be warnings unless combined with hard failures.

Band distribution is evaluated at whole-paper level using:

- planned target counts
- estimated final counts
- warning threshold
- hard-fail threshold

### 7. Speed strategy

Section generation should remain parallelized. New band logic must not reintroduce unnecessary serial model calls.

## Implementation shape

1. Add whole-paper band planning helpers.
2. Add per-question band mapping helpers.
3. Add band-aware prompt text for section generation and single-question repair.
4. Add explicit banned-type rules for judgment/reasoning prompts and validators.
5. Add a lightweight difficulty estimator used for release warnings.
6. Preserve question-number-to-band mapping after repair and renumbering.
7. Add deterministic verification that section generation remains parallelized.

## Acceptance criteria

- A 20-question paper plans around `LOW=0`, `MID=6`, `HIGH=11`, `VERY_HIGH=3`, with controlled drift.
- The system retains explicit target-band metadata for each question slot end-to-end.
- Graphic reasoning is never intentionally generated.
- Graphic reasoning in generated output is repaired or blocked before release.
- Allowed text-only judgment/reasoning items are not falsely rejected as graphic reasoning.
- Soft band mismatches do not tank release success on their own.
- Hard failures still block release.
- Parallel section generation still works after band logic is added.
- Existing generation and RAG tests continue to pass.
