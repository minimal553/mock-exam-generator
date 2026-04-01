# Gongkao Generator Rebuild Design

**Date:** 2026-03-25

**Goal:** Rebuild the mock-paper generation core from a generic content generator into a route-driven exam-item generator that follows real public-service exam module boundaries, item templates, distractor rules, and release gates.

## Why Rebuild

Teacher comments on [【王·模拟题】](/C:/Users/ZhuanZ1/Desktop/【王·模拟题】.docx) converge on one conclusion: the current system can often hit a nominal knowledge point, but it still fails to produce items that behave like real exam questions.

The main defects are structural:

- module/type mismatch: rule items drifting into language, hybrid items drifting across judgment subtypes
- fake authenticity: stems are too short, too oral, too narrative, or too template-like
- weak distractors: obvious wrong answers, absolute wording, and zero-competition options
- unstable ask/option pairing: the question stem asks one thing while the options compete on another axis
- data unreliability: fabricated statistics, inconsistent indicator names, and nonstandard analysis terms

This means the problem is not wording polish. The generator needs a new command structure.

## Scope

This rebuild changes the generation core in [app.py](/C:/Users/ZhuanZ1/Desktop/学习机/standalone_app/app.py) and related tests in [test_per_question_generation.py](/C:/Users/ZhuanZ1/Desktop/学习机/tests/test_per_question_generation.py).

It does not redesign the Flask UI. It preserves the existing paper assembly, section parallelism, knowledge-point whitelist, and repair pipeline.

## Target Architecture

The generator will move from:

- module name -> loose prompt -> candidate -> validator

to:

- module -> subtype route -> mother-template contract -> candidate -> veto validators -> repair -> release audit

## Layer 1: Type Router

Every question slot must be assigned:

- module
- subtype
- stem form
- ask-form family
- distractor factory
- explanation proof obligation

The route must be deterministic before the model writes content.

### Initial subtype map

- `政治理论`
  - `policy_principle_application`
- `常识判断`
  - `policy_execution_judgment`
  - `legal_rule_application`
- `言语理解与表达`
  - `language_main_idea`
  - `language_detail_judgment`
  - `language_fill_blank`
- `数量关系`
  - `quantitative_equation`
  - `quantitative_arrangement`
- `判断推理`
  - `translation_reasoning`
  - `definition_judgment`
  - `argument_evaluation`
- `资料分析`
  - `data_single_fact`
  - `data_growth_compare`
  - `data_comprehensive_judgment`

## Layer 2: Mother Templates

Each subtype gets a hard template contract.

The contract includes:

- source form
- stem length range
- official voice requirement
- allowed ask styles
- option length range
- distractor patterns
- explanation proof shape
- banned constructions

Examples:

- `language_main_idea`
  - 180-300 Chinese characters
  - commentary/governance/report voice
  - must include logical hooks such as contrast, progression, causal pivot, or conclusion cue
  - options must be close summaries, not obvious opposites
- `translation_reasoning`
  - 120-200 Chinese characters
  - explicit logic operators or translated governance/workplace rules
  - ask style limited to `一定为真 / 一定不能推出 / 不能推出`
  - strongest distractor patterns include `肯后推前`, `否前推否后`, `且或偷换`
- `definition_judgment`
  - 150-250 Chinese characters
  - definition must encode 2-4 key elements
  - options must be parallel short cases
  - exactly one option fully matches, strongest distractor misses one key element
- `data_comprehensive_judgment`
  - material must use real template data and standard statistical language
  - option subjects and tested points should be dispersed
  - banned terms include nonstandard phrases such as `增幅率`

## Layer 3: Source Classes

Question materials are divided into three source classes:

- `strict_real_source`
  - data analysis materials
  - legal and policy facts that require real documents
- `template_rewrite_source`
  - language passages
  - definition and reasoning backgrounds
- `abstract_generation_source`
  - some quantity shells
  - some formal reasoning shells

Initial enforcement in phase 1:

- data-analysis prompts must declare `strict_real_source_template_only`
- policy/legal items must forbid fabricated file wording
- language items must forbid rule-clause stems and numbered-condition stems

## Layer 4: Distractor Factory

Wrong options cannot be free-written.

They must come from per-subtype distractor families.

Examples:

- language
  - `partial_summary`
  - `scope_shift`
  - `causal_swap`
  - `over_inference`
- translation reasoning
  - `affirm_consequent`
  - `deny_antecedent`
  - `and_or_swap`
  - `scope_swap`
- definition judgment
  - `missing_key_element`
  - `wrong_subject`
  - `opposite_purpose`
  - `partial_match`
- data analysis
  - `base_period_swap`
  - `percentage_point_swap`
  - `unit_swap`
  - `indicator_scope_drift`

## Layer 5: Veto Validators

Post-generation validators become explicit fail-fast guards.

Phase-1 veto rules:

- language stem uses rule/condition style such as `①②③`, `已知条件`, `根据规定`
- language options use punctuation at the end
- two or more obvious absolute distractors in a language item
- rule item whose correct option near-repeats a clause already stated in the stem
- subtype ask-style mismatch
- quantity item with unclosed parameter set or options outside announced scheme set
- data-analysis item using banned fake terms or inconsistent indicator naming signals

## Layer 6: Release Audit

Release quality still uses:

- hard failures for structural and item-quality blockers
- soft warnings for lower-severity style misses

But the new subtype contracts should move more quality enforcement forward into planning and prompting so fewer bad items reach repair.

## Phase Plan

### Phase 1

- add subtype route contracts
- add mother-template metadata to section planning
- emit these contracts into generation prompts and repair prompts
- add veto validators for the most common teacher-reported failures
- keep current paper assembly and repair loop

### Phase 2

- add real-source template registry for data analysis and policy/legal items
- move data-analysis generation from freeform material creation to template-backed material selection
- add stronger option-distribution and distractor-balance validators

### Phase 3

- add explicit human-review queue / audit output
- produce subtype-specific review summaries for editors

## Acceptance Criteria For Phase 1

- language items can no longer be generated from numbered-rule or condition-list stems without being vetoed
- prompts contain subtype-specific constraints rather than only module-level guidance
- quantity prompts explicitly ban extra unannounced schemes and mixed cost assumptions
- judgment prompts explicitly distinguish translation reasoning, definition judgment, and argument evaluation
- validator catches rule-restatement pseudo-items
- tests cover subtype routing, prompt contracts, and veto validators

