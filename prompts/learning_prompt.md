# 学习自动化提示词

目标：从当前目录中的真题材料中学习稳定规律，并把规律锁定成一份可供出题流程严格执行的规则簿。这个流程不能产出模拟卷。

## 必须遵守

1. 只做学习，不出题。
2. 学习结果必须写入 `state/rulebook.md` 和 `state/locked_rulebook.json`。
3. 规则必须同时吸收两类输入：
   - `data/` 中的真题结构与题型分布。
   - `state/meta_memory.json` 中累计的好/坏反馈信号。
4. 更新 `state/locked_rulebook.json` 时，`status` 必须写成 `locked`，并且版本号必须递增。
5. 不要改写 `state/meta_memory.json`，它只能由反馈流程更新。

## 执行顺序

1. 运行：
   ```powershell
   python scripts/gongkao_workflow.py index-materials
   python scripts/gongkao_workflow.py sync-learning-packet
   ```
2. 阅读：
   - `data/material_summary.md`
   - `data/questions.jsonl`
   - `state/meta_memory.json`
   - `state/learning_packet.md`
3. 归纳并写出：
   - 题量蓝图
   - 各部分题型与风格规则
   - 选项设计规则
   - 解析写法规则
   - 明确的反模式
   - 来自好/坏反馈的强化项和规避项
4. 更新 `state/rulebook.md`。
5. 更新 `state/locked_rulebook.json`。

## `state/locked_rulebook.json` 必须包含

- `version`
- `generated_at`
- `status`
- `source_materials`
- `exam_profile.section_blueprint`
- `hard_constraints`
- `soft_preferences`
- `option_design_rules`
- `explanation_rules`
- `anti_patterns`
- `memory_effects.reinforce`
- `memory_effects.avoid`

## 完成后必须执行

```powershell
python scripts/gongkao_workflow.py validate-rulebook
```

如果校验失败，继续修正直到通过。最后在 inbox 里汇报：

- 新规则版本
- 本次吸收了哪些材料
- 哪些好/坏反馈被写进了规则
