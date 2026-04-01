# 

## 目录结构

- `scripts/gongkao_workflow.py`: 统一 CLI。
- `data/material_index.json`: 每套材料的概览索引。
- `data/questions.jsonl`: 结构化题目明细。
- `data/material_summary.md`: 材料结构摘要。
- `state/rulebook.md`: 人可读规则簿。
- `state/locked_rulebook.json`: 机器可校验的锁定规则。
- `state/meta_memory.json`: 好/坏反馈累积形成的元记忆。
- `state/learning_packet.md`: 供学习自动化读取的最新摘要。
- `prompts/learning_prompt.md`: 学习自动化执行说明。
- `prompts/generation_prompt.md`: 出题自动化执行说明。
- `output/mock_tests/`: 模拟卷输出目录。

## 本地命令

先抽取材料：

```powershell
python scripts/gongkao_workflow.py index-materials
```

查看状态：

```powershell
python scripts/gongkao_workflow.py status
```

当学习自动化更新完 `state/locked_rulebook.json` 后，先校验规则簿：

```powershell
python scripts/gongkao_workflow.py validate-rulebook
```

人工审核某份模拟卷后，记录好/坏标签：

```powershell
python scripts/gongkao_workflow.py record-feedback --paper output/mock_tests/xxx.md --label good --tags 贴近真题,干扰项自然 --notes "数量关系难度合适"
```

校验某份模拟卷是否遵循当前锁定规则：

```powershell
python scripts/gongkao_workflow.py validate-paper --paper output/mock_tests/xxx.md
```

## 学习与出题的边界

- 学习流程允许读取：`data/`、`state/meta_memory.json`、`state/learning_packet.md`。
- 学习流程允许写入：`state/rulebook.md`、`state/locked_rulebook.json`。
- 出题流程必须先通过 `validate-rulebook`。
- 出题流程只允许把当前 `state/locked_rulebook.json` 当作规则来源，不能在出题时临时发明新规则。
- 反馈流程只追加 `state/feedback_log.jsonl`，并重建 `state/meta_memory.json`。

## 推荐的模拟卷 frontmatter

出题自动化生成 Markdown 时，文件顶部使用下面这种头部，便于校验和反馈：

```md
---
paper_id: mock-2026-03-11-am
generated_at: 2026-03-11T08:00:00+08:00
rulebook_version: v2026.03.11-1
generator_mode: locked_rulebook_only
question_count: 20
---
```

正文里至少保留 `## 答案` 段落，`validate-paper` 会检查。

## 独立一键学习应用（无需依赖本工作流对话）

已提供本地独立应用：`standalone_app/`。

一键启动：

```powershell
.\start_app.bat
```

启动后打开：`http://127.0.0.1:18765`

使用方式：

1. 打开后默认材料目录指向 `联考A+国省考（共50套）`。
2. 选择模型来源与模型名。
3. 点击“开始学习并生成模拟题”。
4. 应用会自动完成：刷新材料索引、生成学习方案、生成并校验模拟卷、写入 `output/mock_tests/`。
5. 做完后可直接点击 `好` / `坏`，把反馈写回 `state/meta_memory.json`。

免费/低成本模型建议：

- `ollama`：本地运行，最适合免费使用。先安装 Ollama，再执行例如 `ollama pull qwen3:8b`。
- `dashscope`：可接入千问云端模型，是否有免费额度取决于当前账户策略。
- `openai`：继续保留；若额度不足，应用会自动切到离线学习方案。

当前默认配置：

- 默认 provider：`ollama`
- 默认模型：`gpt-oss:120b-cloud`
- 这意味着应用启动后会优先走 Ollama Cloud 模型，不再默认要求先下载本地模型。

当前一键流程输出：

- 学习方案：页面右侧“学习方案”区域即时展示。
- 模拟卷文件：自动写入 `output/mock_tests/`，并在页面显示绝对路径与正文。
- 反馈记忆：`good` / `bad` 通过 `record-feedback` 回写到 `state/meta_memory.json`，供下一轮继续强化/规避。

代码位置：

- `standalone_app/app.py`: 后端 API 与 OpenAI 调用。
- `standalone_app/templates/index.html`: 前端页面（含粘贴 Key 入口）。
- `start_app.bat`: 创建虚拟环境、安装依赖并启动。

## ??????

- ?????`scripts/source_crawler.py`
- ?????`state/source_catalog.json`
- ?????`data/web_materials.jsonl`
- ?????`data/web_material_summary.md`
- ??????????????????????????????????????
- ?????? 12 ?????????????????
- ??????? `state/source_catalog.json` ??????????????

