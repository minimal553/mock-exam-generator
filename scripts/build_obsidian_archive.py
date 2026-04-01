from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[1]
VAULT = ROOT / "obsidian_gongkao_archive"


FILES = {
    ".obsidian/app.json": """{
  "legacyEditor": false,
  "spellcheck": false,
  "showLineNumber": false,
  "trashOption": "local"
}
""",
    "00 首页.md": dedent(
        """
        # 公考学习机 Obsidian 档案库

        这是为 `C:/Users/ZhuanZ1/Desktop/学习机` 项目建立的 Obsidian 库，用于记录该项目从规则学习自动化、独立应用改造、模型接入、材料体系扩展、故障修复到当前可运行状态的全过程。

        ## 阅读入口

        - [[01 项目总述]]：项目是什么、解决什么问题、当前形成了什么系统。
        - [[02 目标与约束]]：初始目标、用户追加要求、工程约束。
        - [[03 目录与组件]]：目录结构、脚本职责、状态文件、前后端组成。
        - [[04 规则系统演化]]：规则簿、记忆、元规则、来源规则、长度规则等如何演化。
        - [[05 独立应用演化]]：从依赖工作流到独立一键应用的演化过程。
        - [[06 模型接入与策略]]：OpenAI、DashScope、Ollama、本地模型、云端模型的接入与选择。
        - [[07 材料体系与来源]]：本地材料、联网抓料、来源域设计、材料索引体系。
        - [[08 故障与修复时间线]]：关键故障、定位过程、真实修复点与结果。
        - [[09 当前状态与验证]]：项目当前状态、已验证能力、当前可用结论。
        - [[10 对话重建记录]]：基于现有工作区与执行记录重建的完整过程记录。
        - [[11 局限与下一步]]：当前边界、已知问题、建议的下一步重构方向。
        - [[附录/文件索引]]：重要文件索引。

        ## 当前结论

        - 项目已从“依赖 Codex 手工工作流”改造成“本地一键启动的独立学习应用”。
        - 规则系统已沉淀为 `rulebook + locked_rulebook + meta_memory + learning_packet` 的组合。
        - 独立应用已具备：刷新材料、生成学习方案、生成原创模拟题、回收 good / bad 反馈、一键打包分享。
        - 模拟题生成链路已经从“整卷失败”重构到“逐题校验、逐题修复、16 题阈值发布”。
        - 最新一次真实成功生成的模拟卷为：`C:/Users/ZhuanZ1/Desktop/学习机/output/mock_tests/2026-03-20-170434-公考职测一键模拟卷.md`。

        ## 重要说明

        用户要求“把全过程所有细节一字不落地记录进去”。工程上需要如实说明边界：

        - 本库能够完整覆盖当前工作区中存在的代码、配置、状态文件、生成物、规则演化结果，以及本轮会话中可确认的关键决策与修复过程。
        - 本库不能替代真正的聊天数据库导出，因此无法保证恢复所有历史聊天的逐字逐句原文。
        - 对于无法从本地文件系统直接验证的细节，本库会明确标记为“对话重建”或“基于当前证据可确认”。
        - 不会把用户曾贴出的已泄露 API Key 原样抄入归档，避免把风险再次固化到仓库里。
        """
    ),
    "01 项目总述.md": dedent(
        """
        # 项目总述

        `公考学习机` 是一个围绕公职类考试训练构建的本地化学习系统。它的目标不是做一个静态题库，而是形成下面这条闭环：

        1. 学习真实材料与真题。
        2. 提炼稳定规则、元规则、偏好与规避项。
        3. 用规则约束大模型生成学习方案与原创模拟题。
        4. 对生成结果做结构、长度、原创性、校验一致性检查。
        5. 收集用户 good / bad 反馈继续反哺记忆与规则。

        ## 第一阶段：规则学习自动化

        最早的任务是“公考规则学习”自动化。核心动作是：

        - 打开 `prompts/learning_prompt.md` 并执行整套学习流程。
        - 刷新材料索引。
        - 更新 `state/rulebook.md`。
        - 更新 `state/locked_rulebook.json`。
        - 运行 `validate-rulebook`。
        - 把结果写回 inbox 和 automation memory。

        当时的重点是把真题、学习包和规则总结成可锁定的规则簿。那一阶段形成了：

        - `scripts/gongkao_workflow.py`
        - `state/rulebook.md`
        - `state/locked_rulebook.json`
        - `state/meta_memory.json`
        - `state/learning_packet.md`

        ## 第二阶段：独立应用化

        用户明确提出一个方向：不能继续依赖当前对话工作流存在，而要做成一个“一键开始与学习”的独立应用。

        于是项目被扩展为：

        - 本地后端：`standalone_app/app.py`
        - 本地前端：`standalone_app/templates/index.html`
        - 启动脚本：`start_app.bat`
        - 独立状态与输出：`state/*`、`output/*`

        这个阶段的关键目标变成：

        - 一键启动
        - 粘贴 Key 或改用 Ollama / Cloud model
        - 自动刷新材料
        - 自动生成学习方案
        - 自动生成原创模拟题
        - good / bad 反馈写回记忆
        - 一键打包分享整个项目

        ## 当前系统不是单一脚本，而是四层结构

        - 材料层：`data/`、本地题库、PDF、docx、联网抓料摘要。
        - 规则层：`state/rulebook.md`、`state/locked_rulebook.json`、`state/meta_memory.json`。
        - 生成层：`standalone_app/app.py` 中的 prompt、校验器、重试器、修复器。
        - 应用层：浏览器前端、启动脚本、分享包输出。

        ## 当前项目定位

        它不是“万能题目生成器”，而是“围绕公考命题规律和用户反馈持续迭代的训练系统”。
        """
    ),
    "02 目标与约束.md": dedent(
        """
        # 目标与约束

        ## 用户连续提出的关键目标

        1. 执行规则学习自动化，持续吸收真题与材料。
        2. 把总结出的解题技巧写进程序记忆，并提炼成元规则。
        3. 把应用改造成独立的一键学习系统，不依赖当前 Codex 工作流。
        4. 支持接入 OpenAI API、后续也支持免费模型、千问、Ollama。
        5. 前端做到一键打开，不需要每次手动复制本地网址。
        6. 把 Ollama 模型目录迁移到 `D:/OLLAMA_MODELS`。
        7. 支持使用 Ollama Cloud 模型，例如 `gpt-oss:120b-cloud`。
        8. 不是摘抄原题，而是“通过学习后独立思考生成原创模拟题”。
        9. 题干质量必须接近真实公职考试，且满足长度约束。
        10. 失败率不能太高，要按单题修复，而不是整卷一票否决。
        11. 能够一键打包整个项目分享给他人。
        12. 建立 Obsidian 库，把全过程细节归档。

        ## 明确被用户反复强调的质量要求

        - 模拟题不能只是换皮摘抄原题。
        - 非数学计算题，题干正文不得少于 50 个字。
        - 资料分析的资料正文不得少于 100 个字。
        - 题目要更像真实公务员/事业单位考试题，而不是极简问答。
        - 失败时要把原因反馈出来，并尽量自动修复。
        - 一次生成 20 道题时，只要 16 道以上合格即可发出。

        ## 工程约束

        ### 本地独立运行

        项目部署目标是用户自己的 Windows 机器，本地启动，本地浏览器访问，本地保存状态。

        ### 多模型兼容

        先后支持过：

        - OpenAI 兼容接口
        - DashScope 兼容接口
        - Ollama 本地接口
        - Ollama Cloud 模型

        ### 规则必须可验证

        规则不是自然语言备注，而是要能被：

        - `validate-rulebook`
        - 模拟卷校验
        - 题干长度校验
        - 原创性校验
        - 结构校验

        这些程序逻辑真正消费。

        ### 项目在脏工作区上持续演化

        用户在同一目录持续追加了：

        - 更多真题材料
        - `联考A+国省考（共50套）` 目录
        - `综合应用能力（综合管理A类）` PDF

        项目要在现有目录基础上增量演化，不能依赖“从头重建一个全新仓库”。

        ## 对“所有细节一字不落”的工程解释

        这个目标只能分成两层：

        - 可直接落盘的：代码、规则、状态、目录、验证结果、关键报错、输出路径、已知结论。
        - 无法逐字还原的：历史对话原文、已被覆盖的瞬时界面状态、未保存到文件系统的临时模型输出。

        因此本库会把可证据化内容尽量全部固化，但不会伪造不存在的逐字记录。
        """
    ),
    "03 目录与组件.md": dedent(
        """
        # 目录与组件

        项目根目录：`C:/Users/ZhuanZ1/Desktop/学习机`

        ## 顶层目录

        - `.git/`：Git 仓库。
        - `.venv/`：本地虚拟环境。
        - `data/`：题库与联网抓料输出。
        - `output/`：模拟卷、分享包等输出。
        - `prompts/`：学习与生成 prompt。
        - `scripts/`：工作流脚本、抓料脚本。
        - `standalone_app/`：独立应用后端与前端模板。
        - `state/`：规则、记忆、会话状态、来源配置。
        - `tests/`：当前针对逐题修复链路的回归测试。
        - `联考A+国省考（共50套）/`：新增的本地大材料库。

        ## 关键文件

        ### 应用层

        - `C:/Users/ZhuanZ1/Desktop/学习机/standalone_app/app.py`
          - 独立应用核心后端。
          - 负责 provider 选择、学习方案生成、模拟卷生成、校验、单题重做、分享打包。

        - `C:/Users/ZhuanZ1/Desktop/学习机/standalone_app/templates/index.html`
          - 独立应用前端。
          - 提供模型来源、模型名、材料目录、本轮重点、反馈备注、生成按钮、打包按钮等 UI。

        - `C:/Users/ZhuanZ1/Desktop/学习机/start_app.bat`
          - 创建虚拟环境、安装依赖、启动服务、自动打开浏览器。
          - 后续还补过“先杀旧端口占用再启动”的逻辑。

        ### 工作流与抓料

        - `C:/Users/ZhuanZ1/Desktop/学习机/scripts/gongkao_workflow.py`
          - 材料索引。
          - 学习包同步。
          - 规则校验。
          - 模拟卷校验。
          - docx 解析。

        - `C:/Users/ZhuanZ1/Desktop/学习机/scripts/source_crawler.py`
          - 联网抓取来源站点材料摘要。
          - 结果写入 `data/web_materials.jsonl` 和 `data/web_material_summary.md`。

        ### 规则与状态

        - `C:/Users/ZhuanZ1/Desktop/学习机/state/rulebook.md`
        - `C:/Users/ZhuanZ1/Desktop/学习机/state/locked_rulebook.json`
        - `C:/Users/ZhuanZ1/Desktop/学习机/state/meta_memory.json`
        - `C:/Users/ZhuanZ1/Desktop/学习机/state/learning_packet.md`
        - `C:/Users/ZhuanZ1/Desktop/学习机/state/source_catalog.json`
        - `C:/Users/ZhuanZ1/Desktop/学习机/state/standalone_session.json`

        这些文件共同承担：

        - 规则显式化
        - 记忆持久化
        - 反馈沉淀
        - 当前会话状态保存
        - 抓料来源配置

        ### 测试

        - `C:/Users/ZhuanZ1/Desktop/学习机/tests/test_per_question_generation.py`
          - 逐题修复并发布 20/20 的测试。
          - 修不好但仍可按 16/20 发布的测试。
          - 结构修复后恢复发布的测试。

        ## 当前输出物

        ### 模拟卷

        保存在：`C:/Users/ZhuanZ1/Desktop/学习机/output/mock_tests`

        其中最近一次明确成功且通过校验的文件是：

        - `C:/Users/ZhuanZ1/Desktop/学习机/output/mock_tests/2026-03-20-170434-公考职测一键模拟卷.md`

        ### 分享包

        保存在：`C:/Users/ZhuanZ1/Desktop/学习机/output/share_packages`

        ### 调试输出

        一些排障时的调试文件也留在项目内，例如：

        - `C:/Users/ZhuanZ1/Desktop/学习机/output/debug-ollama-response.txt`

        ## 当前架构总结

        这个项目现在不是单文件脚本，而是“状态机 + prompt + 规则 + 前端 + 校验器”的组合系统。
        """
    ),
    "04 规则系统演化.md": dedent(
        """
        # 规则系统演化

        规则系统是本项目的核心，不是附属说明文档。

        ## 初始学习阶段

        最早执行的是“公考规则学习”自动化：

        - 打开 `prompts/learning_prompt.md`
        - 刷新材料索引
        - 更新 `rulebook.md`
        - 更新 `locked_rulebook.json`
        - 运行 `validate-rulebook`
        - 留 inbox 总结

        当时形成的早期版本包括：

        - `v2026.03.11-2`
          - 吸收了 6 份真题、690 题。
          - 反馈信号仍为空。

        ## 第一批解题技巧入库

        用户随后提供了大段关于这套卷通用解题框架、常识、言语、数量、判断、资料分析的总结，并要求：

        - 写入程序记忆
        - 提炼成元规则

        之后规则版本升到：

        - `v2026.03.11-4`
          - `reinforce` 增加到 16 条。
          - `avoid` 增加到 12 条。
          - `recent_feedback` 增加手工注入信号。

        这批规则的代表性内容包括：

        - 先判问法，再判内容。
        - 先看选项差异，再决定解题精度。
        - 言语先看逻辑关系，不先猜词。
        - 数量题 30 秒识别不出模型就先跳。
        - 定义题必要条件必须全满足。
        - 资料题先判型，后少算。

        ## 第二批“命题人视角”规则入库

        用户又提供了更偏命题规律的总结，强调：

        - 表面材料新，底层考法旧。
        - 每题只考一个核心点。
        - 干扰项都只是错一点。
        - 难度主要来自识别，而不是冷门知识。

        随后版本升到：

        - `v2026.03.11-6`

        这一批规则更偏命题侧：

        - 先骨架，后材料。
        - 先唯一考点，后选项设计。
        - 错项要像对的。
        - 背景可以新，解法必须旧。
        - 整卷要讲究覆盖和平衡。

        ## 来源域规则入库

        用户进一步指定了资料、言语、判断的典型材料来源域。

        之后规则升级为：

        - `v2026.03.18-1`

        这一轮把“来源规则”写成了程序显式约束，而不是仅作经验提示。

        ## 综应A教材迁移元规则

        用户提供了：

        - `C:/Users/ZhuanZ1/Desktop/学习机/20250916-事业单位考试辅导用书·综合应用能力（综合管理A类）2026版-印刷文件.pdf`

        要求通过学习其中内容定义元规则，提升模拟题质量。

        随后版本升级为：

        - `v2026.03.18-2`

        新增规则强调：

        - 先定真实工作场景，再定问法和核心考点。
        - 公共管理场景必须校验角色身份、权限边界、程序逻辑。
        - 题面要保留正式文本的结构信号。
        - 明确区分已完成工作、当前状态、下一步计划。

        ## 长度硬约束入库

        用户对模拟题质量不满意，明确提出：

        - 除数学计算题外，题干正文必须超过 50 个字。
        - 资料分析材料正文必须超过 100 个字。

        之后版本升级为：

        - `v2026.03.18-3`

        这不是软建议，而是写进了生成校验链路的硬约束。

        ## 规则系统的当前结构

        当前规则系统由以下部分构成：

        - `rulebook.md`：可读版规则簿。
        - `locked_rulebook.json`：程序实际消费的锁定规则。
        - `meta_memory.json`：反馈、强化、规避、最近信号。
        - `learning_packet.md`：学习包摘要。
        - `applied_ability_a_meta_rules.md`：综应A迁移规则。

        ## 当前规则系统的作用

        它不只是“保存经验”，而是实际支撑：

        - 学习方案 prompt
        - 出题 prompt
        - 原创性校验
        - 题面长度校验
        - 来源域约束
        - 反馈回写逻辑

        规则系统已经变成这个项目最重要的“稳定层”。
        """
    ),
    "05 独立应用演化.md": dedent(
        """
        # 独立应用演化

        ## 从工作流依赖到本地独立应用

        用户最初提出一个明确诉求：

        - 不想继续依赖当前对话工作流存在
        - 要做成一个独立应用
        - 最好一键开始、一键学习、一键出题

        于是项目从“脚本 + 规则更新”扩展为“独立应用”。

        ## 最小可运行版

        最早的独立版包含：

        - `standalone_app/app.py`
        - `standalone_app/templates/index.html`
        - `standalone_app/requirements.txt`
        - `start_app.bat`

        那个阶段先实现：

        - 本地 Flask 服务
        - 浏览器页面
        - 粘贴 API Key
        - 点击开始学习

        ## 启动体验优化

        用户不想每次手工输入本地网址，于是：

        - `start_app.bat` 被改造成启动服务后自动打开浏览器

        后来又发现旧服务残留会导致一直连到旧代码，于是继续加了：

        - 启动前先清理占用 18765 端口的旧服务

        ## 分享能力接入

        用户要求“一键打包分享”。之后：

        - 前端新增“一键打包分享”按钮
        - 后端新增打包接口
        - 生成 zip 到 `output/share_packages`
        - 自动触发浏览器下载

        ## 学习闭环接入

        用户的目标不是“点一下返回一段文本”，而是完整学习闭环，所以独立应用后来接入：

        - 刷新材料索引
        - 刷新学习包
        - 生成学习方案
        - 生成模拟题
        - good / bad 反馈回写

        ## 从摘抄题库到原创命题

        应用曾走过一段错误路线：

        - 为了尽快出卷，直接从本地题库抽题组卷

        用户明确否定这条路，要求：

        - 必须通过学习材料后独立思考出题
        - 不能直接摘抄原题

        之后应用改成：

        - 模型生成原创卷
        - 题干与 `data/questions.jsonl` 做相似度比对
        - 过近则拒绝发布

        ## 联网抓料接入

        用户后来要求：

        - 每次开始做模拟题时，都去指定来源网站抓材料作为出题原料

        因此应用又接入：

        - `scripts/source_crawler.py`
        - `state/source_catalog.json`
        - 抓料结果写入 `data/web_materials.jsonl` / `data/web_material_summary.md`
        - 生成 prompt 会自动拼接抓料摘要

        ## 当前应用定位

        当前独立应用不是一个单次调用网页，而是本地训练平台的前端入口。
        """
    ),
    "06 模型接入与策略.md": dedent(
        """
        # 模型接入与调用策略

        ## 最早路线：OpenAI API

        用户一开始希望通过 OpenAI API 把项目做成独立应用，并曾直接贴出一把 API Key。

        当时系统明确做了两件事：

        - 提示该 Key 已泄露，应立刻撤销并重建。
        - 不把该 Key 再次写回文件或档案。

        ## OpenAI 兼容接口问题

        早期调用中出现过：

        - `Unsupported parameter: 'temperature' is not supported with this model.`

        随后从后端移除了不兼容参数。

        ## 配额问题

        后续又遇到：

        - `429 insufficient_quota`

        这不是代码问题，而是账号额度问题。后来应用还加过配额不足时的离线兜底逻辑，避免页面直接报死。

        ## 支持更多 provider

        用户提出可否用免费模型、千问、Ollama。于是应用扩展为支持：

        - `openai`
        - `dashscope`
        - `ollama`

        这样应用可以：

        - 走 OpenAI 兼容接口
        - 走千问兼容接口
        - 走本地/云端的 Ollama API

        ## Ollama 迁移与使用

        用户后来逐步把注意力转到 Ollama：

        - 把模型相关目录迁移到 `D:/OLLAMA_MODELS`
        - 询问 Ollama 图标为何不弹聊天窗，后确认 Ollama 主要是后台服务/托盘形态
        - 决定把项目默认模型切到 `gpt-oss:120b-cloud`

        ## 为什么用了 `gpt-oss:120b-cloud`

        用户发现 Ollama 支持一些云端模型，于是要求：

        - 不下载大模型，直接使用 cloud model
        - 把项目默认模型切到 `gpt-oss:120b-cloud`

        后端与前端随后改成：

        - 默认 provider = `ollama`
        - 默认 model = `gpt-oss:120b-cloud`

        ## 模型策略的现实问题

        这个模型能工作，但在“长中文考试题 + 严格格式 + 严格长度 + 严格原创性 + 整卷输出”这个任务上，服从性不够稳定。它最常见的坏输出模式包括：

        - 某一题题干过短
        - 资料分析缺少共享材料
        - Markdown 区块标题漂移
        - 使用 `**1.**` 这类粗体题号
        - 偶尔生成结构不完整的卷面

        因此，后续工程重点不是换模型，而是：

        - 增强解析器
        - 增强结构修复
        - 从整卷一票否决改成逐题重做

        ## 当前模型结论

        当前项目是“多 provider 兼容，但默认依赖 Ollama Cloud”。

        成功生成过的最新卷子说明：

        - `gpt-oss:120b-cloud` 在当前链路上已经可以真实跑通
        - 但必须依赖更强的后处理、修复和校验策略，不能把它当成一次性完美输出的模型来用
        """
    ),
    "07 材料体系与来源.md": dedent(
        """
        # 材料体系与来源

        ## 本地材料

        当前项目内存在多类本地材料：

        - 单份真题 docx
        - `联考A+国省考（共50套）` 目录中的批量材料
        - `综合应用能力（综合管理A类）` PDF

        项目后来真实索引过这个新增材料目录，结果为：

        - 已索引 43 份材料
        - 共解析 4970 道题

        ## 学习材料与规则来源

        用户多次提供了人工总结，包括：

        - 解题技巧总结
        - 命题人视角总结
        - 材料来源域总结
        - 综应A教材迁移要求

        这些都不是放在旁边参考，而是被写进 `meta_memory` 和 `locked_rulebook` 中，成为生成约束。

        ## 联网来源域设计

        用户明确指定过的来源包括：

        ### 资料分析

        - 国务院各部门网站
        - 各省市统计局网站
        - 中国互联网网络信息中心
        - 中国产业经济信息网
        - 政府工作报告
        - 各行业协会网站
        - 根据真题搜索类似材料
        - AI 辅助选题后再回源确认

        ### 言语

        核心官媒类：

        - 人民网
        - 新华网
        - 光明网
        - 求是网
        - 中国政府网

        主流媒体补充：

        - 半月谈
        - 中国青年报
        - 经济日报

        其他补充：

        - 三联生活周刊
        - 文汇报
        - 澎湃新闻
        - 果壳网

        ### 判断

        - 定义判断：MBA 智库、百科、法律/文学释义材料
        - 论证判断：人民网、新华网、光明网、央视网、中国政府网、科普中国等

        ## 联网抓料的接入方式

        后来实现了：

        - `scripts/source_crawler.py`
        - `state/source_catalog.json`
        - `data/web_materials.jsonl`
        - `data/web_material_summary.md`

        在生成时，系统会：

        1. 先刷新本地材料索引。
        2. 再去来源池抓最近材料。
        3. 把抓到的摘要拼进学习方案和出题 prompt。

        ## 为什么材料体系重要

        用户反复强调一个问题：

        - 真题风格的核心不在热点话题本身，而在能力骨架、正式表达、结构信号、来源气质。

        因此材料体系的作用不只是“给模型一点背景”，而是帮助模型接近真实考试的：

        - 场景质感
        - 问法
        - 结构信号
        - 题面正式性
        - 干扰项设计空间
        """
    ),
    "08 故障与修复时间线.md": dedent(
        """
        # 故障与修复时间线

        这一部分按实际出现过的问题和修复点记录。

        ## 1. OpenAI 参数不兼容

        现象：

        - 使用 `gpt-5` 时返回 `Unsupported parameter: 'temperature' is not supported with this model.`

        修复：

        - 从 `standalone_app/app.py` 移除不兼容参数。

        ## 2. OpenAI 配额不足

        现象：

        - 返回 `429 insufficient_quota`

        结论：

        - 不是代码 bug，而是账号额度问题。

        处理：

        - 页面提示。
        - 后续增加离线兜底方案。

        ## 3. 旧服务残留导致前端一直连旧版本

        现象：

        - 明明代码修了，页面行为还像旧逻辑。

        原因：

        - 18765 端口被多个旧 Python 进程占用。

        修复：

        - `start_app.bat` 启动前清理旧端口进程。

        ## 4. 模拟卷最初是直接抽原题组卷

        现象：

        - 输出卷子虽然像样，但本质是摘抄原题。

        用户反馈：

        - 明确否决。

        修复：

        - 改为模型原创生成。
        - 对 `data/questions.jsonl` 做相似度比对。

        ## 5. 模型短题太多，题干不够像真题

        现象：

        - 大量题干只有十几到几十字。
        - 资料分析甚至只有表格或空材料。

        修复：

        - 非数学题题干正文必须 >= 50 字。
        - 资料分析资料正文必须 >= 100 字。
        - 校验失败直接拦截。

        ## 6. 长度校验早期漏检

        现象：

        - 明明短题存在，仍然被发布。

        原因：

        - 旧解析器对 `**政治理论（2）**` 这类粗体分区标题识别不稳。

        修复：

        - 改成只统计题干正文，不统计选项。
        - 分区解析兼容多种标题格式。

        ## 7. 原创性校验还依赖旧的 `## 题目` 提取器

        现象：

        - 报错：`未在 ## 题目 区块提取到题目。`

        原因：

        - 长度校验与原创性校验使用了不同的解析器。

        修复：

        - `extract_question_stems()` 改为复用同一套 `parse_question_sections()`。

        ## 8. 生成失败率过高

        现象：

        - 一次生成 20 题，只要 1 题不合格就整卷失败。

        原因：

        - 整卷自由生成 + 严格串联校验 + 整卷一票否决。

        修复：

        - 重构为逐题评估、逐题修复、16 题阈值发布。

        ## 9. 报错乱码、问号文案

        现象：

        - 页面错误信息显示成大量问号。

        原因：

        - 替换 `generate_valid_paper()` 过程中，部分错误文案写坏。

        修复：

        - 恢复正常中文错误信息。

        ## 10. 云端模型输出使用 `**1.**` 粗体题号，解析不到题

        现象：

        - 原始模型文本里明明有题，但解析器抽到 0 题。

        修复：

        - `parse_numbered_entry_lines()`、`parse_question_block_lines()`、`extract_stem_from_block_lines()` 兼容粗体题号。

        ## 11. 区块标题漂移

        现象：

        - 模型可能写 `## 试题`、`## 题干`、`## 参考答案`、`## 解析` 等别名。

        修复：

        - 头部集合放宽：
          - `QUESTION_SECTION_HEADERS = {"## 题目", "## 试题", "## 题干"}`
          - `ANSWER_SECTION_HEADERS = {"## 答案", "## 参考答案"}`
          - `NOTE_SECTION_HEADERS = {"## 命题说明", "## 解析", "## 命题说明与解析"}`

        ## 12. 整卷结构损坏时完全无法解析

        现象：

        - 初稿题量 < 16，导致整轮失败。

        修复：

        - 新增 `repair_paper_structure(...)`，先做整卷结构修复，再进入逐题修复。

        ## 13. `validate-paper` 误把答案区和说明区编号都算成题目

        现象：

        - 报错：`question_count=20 与题目行数=60 不一致`

        原因：

        - 校验脚本以前统计了正文里所有编号行。

        修复：

        - `scripts/gongkao_workflow.py` 只统计 `## 题目` 到 `## 答案` 之间的编号行。

        ## 14. docx 索引时遇到坏包直接崩

        现象：

        - `zipfile.BadZipFile: File is not a zip file`

        原因：

        - 扫到了扩展名是 `.docx` 但实际不是合法 zip 包的文件，或 Word 临时锁文件。

        修复：

        - 自动跳过 `~$` 锁文件。
        - 遇到坏 `.docx` 不再整轮崩掉，继续索引其他材料。

        ## 15. 最新一次真实成功验证

        最后通过真实运行，成功生成并校验通过：

        - `C:/Users/ZhuanZ1/Desktop/学习机/output/mock_tests/2026-03-20-170434-公考职测一键模拟卷.md`

        当时输出为：

        - `模拟卷通过校验`
        - `候选题量: 20`
        - `发布题数: 20`
        - `单道题修复: 8`
        - `资料模块修复: 0`
        """
    ),
    "09 当前状态与验证.md": dedent(
        """
        # 当前状态与验证

        ## 当前项目状态

        当前工作区里，项目已经具备以下能力：

        - 本地一键启动独立应用。
        - 支持 `openai / dashscope / ollama` 三类 provider。
        - 默认走 `ollama + gpt-oss:120b-cloud`。
        - 支持刷新本地材料与学习包。
        - 支持联网抓料。
        - 支持原创模拟题生成。
        - 支持 good / bad 反馈回写。
        - 支持一键打包分享整个项目。

        ## 关键验证结果

        ### 规则校验

        历次规则版本更新后都跑过 `validate-rulebook`，并确认规则簿可用。

        ### 语法校验

        以下文件在关键修复后都做过语法检查：

        - `standalone_app/app.py`
        - `scripts/gongkao_workflow.py`

        ### 单元测试

        真实跑通过：

        - `python -m unittest discover -s tests -p "test_per_question_generation.py"`

        当前已覆盖的行为包括：

        - 坏题修好后可以发布 20/20
        - 坏题修不好仍可按 16/20 发布
        - 从 0 题初稿经过结构修复后恢复发布

        ### 真实生成验证

        曾用下面这段方式直接从 Python 入口实跑生成：

        ```python
        import standalone_app.app as app_mod
        paper_path, _paper_content, validation = app_mod.generate_valid_paper(
            provider='ollama',
            api_key='',
            model='gpt-oss:120b-cloud',
            focus=None,
        )
        print(str(paper_path))
        print('---VALIDATION---')
        print(validation)
        ```

        当次真实成功结果：

        - 输出路径：`C:/Users/ZhuanZ1/Desktop/学习机/output/mock_tests/2026-03-20-170434-公考职测一键模拟卷.md`
        - 校验结果：通过
        - 候选题量：20
        - 发布题数：20
        - 单道题修复：8
        - 资料模块修复：0

        ## 当前仍需注意的现实情况

        - `gpt-oss:120b-cloud` 不是高服从性中文考试生成模型，仍可能产生坏题或坏结构。
        - 现在失败率已经比早期低，但不能保证零失败。
        - 逐题修复和结构修复已经能显著提升成功率，但还没有做到最优。

        ## 当前最准确的工程结论

        这个项目现在已经从“经常整体失败”走到“能够真实跑出通过校验的卷子”，但为了长期稳定，还需要进一步改造成按模块分批生成，而不是先整卷自由吐初稿。
        """
    ),
    "10 对话重建记录.md": dedent(
        """
        # 对话重建记录

        这一部分按时间顺序重建项目构建过程。它尽量覆盖所有可确认细节，但不伪造无法从当前证据恢复的逐字聊天原文。

        ## A. 自动化学习起点

        - 用户首先以 `Automation: 公考规则学习` 的形式要求执行 `prompts/learning_prompt.md`。
        - 要求刷新材料索引、更新 `state/rulebook.md`、更新 `state/locked_rulebook.json`、运行 `validate-rulebook`、留下 inbox 总结。
        - 当时得出版本：`v2026.03.11-2`，状态 locked。

        ## B. 两轮大规模解题技巧总结被写入记忆

        - 用户先提供第一套从真题中提炼的解题技巧，偏重解题流程。
        - 系统将其写入 `meta_memory.json`、`rulebook.md`、`locked_rulebook.json`、`learning_packet.md`。
        - 版本升到 `v2026.03.11-4`。
        - 随后用户又提供第二套更偏命题人视角的总结。
        - 系统继续吸收，版本升到 `v2026.03.11-6`。

        ## C. 从工作流依赖转向独立应用

        - 用户要求：能否直接调用 OpenAI API，把系统做成独立的一键开始与学习的应用，而不是依赖当前工作流存在。
        - 系统确认方向可行，但提示用户贴出的 OpenAI API Key 已泄露，需要撤销。
        - 用户要求后续留一个粘贴 Key 的位置。
        - 随后实现了最小独立应用：Flask + HTML + start_app.bat。

        ## D. 早期 API 问题

        - 用户启动后遇到 `temperature` 参数不支持问题。
        - 后端修掉该参数。
        - 随后用户又遇到 OpenAI `429 insufficient_quota`。
        - 系统解释这是额度问题，并一度加过离线兜底。

        ## E. 接入免费模型与 Ollama

        - 用户询问可否用免费模型，例如千问。
        - 后端扩展支持 `openai / dashscope / ollama`。
        - 用户进一步要求前端自动打开，不想再复制粘贴网址。
        - `start_app.bat` 被改成自动打开浏览器。

        ## F. Ollama 使用与迁移

        - 用户希望把 Ollama 相关内容迁移到 `D:/OLLAMA_MODELS`。
        - 模型目录迁移完成，程序本体与运行目录的官方边界被解释清楚。
        - 用户发现 Ollama 图标不弹聊天框，系统说明 Ollama 本质是后台服务。
        - 用户发现 Ollama 可用 cloud models，于是要求把默认模型切成 `gpt-oss:120b-cloud`。

        ## G. 模拟题从“学习方案”扩展到“出题”

        - 用户指出：之所以要调用大模型，就是为了学习模拟并且出模拟题。
        - 并新增了 `联考A+国省考（共50套）` 材料目录供系统学习。
        - 系统把一键流程改成：索引材料、刷新学习包、生成学习方案、生成模拟卷、回收反馈。
        - 实际索引结果为 43 份材料、4970 道题。

        ## H. 用户否决“摘抄原题组卷”

        - 早期为了先跑通，应用曾直接抽题库组卷。
        - 用户明确指出：要的是学习后独立思考出来的题，而不是摘抄原题。
        - 系统随后把链路改成模型原创生成，并增加原创性相似度校验。

        ## I. 材料来源域被程序化

        - 用户提供了资料、言语、判断的来源规则与多个真题出处示例。
        - 系统将其写进 `rulebook`、`locked_rulebook`、`generation_prompt`。
        - 后续又根据用户要求实现了联网爬虫，在每轮开始前抓取公开材料作为生成原料。

        ## J. 用户提供综应A教材 PDF

        - 用户提供 `综合应用能力（综合管理A类）` PDF，要求学习其中内容并提炼元规则。
        - 系统生成 `state/applied_ability_a_meta_rules.md` 并更新规则版本到 `v2026.03.18-2`。

        ## K. 用户对题目质量极度不满

        用户反复指出的问题包括：

        - 题干太短，完全不像公考题。
        - 资料分析材料太短。
        - 生成结果和之前没有本质差别。
        - 失败率太高。

        系统随后陆续做了：

        - 非数学题题干正文 >= 50 字。
        - 资料分析资料正文 >= 100 字。
        - 长度校验不算选项，只算题干正文。
        - 资料分析共享材料强约束。
        - 错题自动定点扩写修复。

        ## L. 一系列解析器与校验器 Bug

        在高强度调试过程中，先后出现并修复了：

        - 粗体模块标题导致长度校验漏检。
        - 原创性校验仍依赖旧的 `## 题目` 提取器。
        - 错误文案乱码成问号。
        - `**1.**` 粗体题号导致 0 题解析。
        - 区块标题别名导致解析失败。
        - `validate-paper` 把答案区和命题说明区编号都算成题目，报 `20 != 60`。

        ## M. 用户要求“不要总整卷失败”

        - 用户提出：一次虽然生成 20 道题，但只要其中 16 道以上合格就可以发出来，没合格的按原因重做。
        - 系统随后重构后端链路：
          - 先生成整卷初稿
          - 逐题评估
          - 坏题按原因单独修复
          - 资料分析模块可整段重做
          - 16 题阈值发布
        - 同时新增对应测试。

        ## N. 最新一次真实跑通

        在完成一系列解析器、结构修复、阈值发布、校验器修复之后，系统实际跑出了：

        - `C:/Users/ZhuanZ1/Desktop/学习机/output/mock_tests/2026-03-20-170434-公考职测一键模拟卷.md`

        且实跑结果显示：

        - 候选题量：20
        - 发布题数：20
        - 单道题修复：8
        - 资料模块修复：0

        ## O. 当前请求

        最新请求是：

        - 在当前项目目录下新建一个 Obsidian 库。
        - 把这个关于公考学习机构建的全过程和所有细节记录进去。

        当前这套归档就是对该请求的响应结果。
        """
    ),
    "11 局限与下一步.md": dedent(
        """
        # 局限与下一步

        ## 当前已知局限

        ### 1. 无法保证恢复所有历史聊天逐字原文

        原因很简单：

        - 当前工作区里没有完整会话数据库导出。
        - 历史回复中有大量中间态并未作为文件落盘。

        因此本库只能做到：

        - 最大程度重建过程
        - 记录可验证的技术事实
        - 标注无法直接验证的边界

        ### 2. 当前默认模型服从性仍有限

        `gpt-oss:120b-cloud` 可以工作，但不够稳定，仍会给生成链路施加很大后处理压力。

        ### 3. 当前仍然是“整卷初稿 + 修补”的架构

        现在已经不是一票否决，但仍旧先生成整卷初稿。更稳的下一步应该是：

        - 按模块生成
        - 按题型生成
        - 题目骨架由程序先固定
        - 模型只负责填充内容

        ### 4. 当前中文编码痕迹不完全干净

        由于此前多轮通过不同方式写文件，仓库内部分文件存在终端显示乱码或 mojibake 痕迹。功能虽已能跑通，但长期仍建议统一编码与文本清洗。

        ## 下一步建议

        ### 优先级 1：按模块分批生成

        建议把整卷拆为：

        - 政治/常识
        - 言语
        - 数量
        - 判断
        - 资料

        这样每个模块只承担本模块失败风险，不再让某一题拖死整卷。

        ### 优先级 2：模板骨架先由代码固定

        尤其对：

        - 非数学题的 `背景 + 条件 + 问法`
        - 资料分析的共享材料结构
        - Markdown 标题与分区

        都应由程序先写死，再让模型填内容。

        ### 优先级 3：增加模型原始输出调试视图

        当前虽然已有调试文件，但前端没有直接展示生成阶段每一步的状态。后续建议增加：

        - 初稿
        - 结构修复稿
        - 单题修复记录
        - 最终发布稿

        ### 优先级 4：单独发展综应A模式

        当前项目主体仍是客观题训练链路。若要真正吃透 `综合应用能力（综合管理A类）` PDF 的价值，建议单独开一个综应A模式，而不是继续把主观题要求硬塞进当前客观题生成器。

        ## 对这份 Obsidian 库的定位

        这不是“随便写几篇项目说明”，而是当前工作区的工程档案库。后续继续迭代时，应该把：

        - 新版本规则
        - 新故障
        - 新修复
        - 新验证结果

        继续按同样方式补进来，避免项目再次失去演化脉络。
        """
    ),
    "附录/文件索引.md": dedent(
        """
        # 文件索引

        ## 项目根目录

        - `C:/Users/ZhuanZ1/Desktop/学习机`

        ## 关键应用文件

        - `C:/Users/ZhuanZ1/Desktop/学习机/standalone_app/app.py`
        - `C:/Users/ZhuanZ1/Desktop/学习机/standalone_app/templates/index.html`
        - `C:/Users/ZhuanZ1/Desktop/学习机/start_app.bat`

        ## 工作流与脚本

        - `C:/Users/ZhuanZ1/Desktop/学习机/scripts/gongkao_workflow.py`
        - `C:/Users/ZhuanZ1/Desktop/学习机/scripts/source_crawler.py`

        ## 规则与状态

        - `C:/Users/ZhuanZ1/Desktop/学习机/state/rulebook.md`
        - `C:/Users/ZhuanZ1/Desktop/学习机/state/locked_rulebook.json`
        - `C:/Users/ZhuanZ1/Desktop/学习机/state/meta_memory.json`
        - `C:/Users/ZhuanZ1/Desktop/学习机/state/learning_packet.md`
        - `C:/Users/ZhuanZ1/Desktop/学习机/state/source_catalog.json`
        - `C:/Users/ZhuanZ1/Desktop/学习机/state/applied_ability_a_meta_rules.md`
        - `C:/Users/ZhuanZ1/Desktop/学习机/state/standalone_session.json`

        ## 数据与材料

        - `C:/Users/ZhuanZ1/Desktop/学习机/data/questions.jsonl`
        - `C:/Users/ZhuanZ1/Desktop/学习机/data/material_summary.md`
        - `C:/Users/ZhuanZ1/Desktop/学习机/data/web_materials.jsonl`
        - `C:/Users/ZhuanZ1/Desktop/学习机/data/web_material_summary.md`
        - `C:/Users/ZhuanZ1/Desktop/学习机/联考A+国省考（共50套）`
        - `C:/Users/ZhuanZ1/Desktop/学习机/20250916-事业单位考试辅导用书·综合应用能力（综合管理A类）2026版-印刷文件.pdf`

        ## 测试

        - `C:/Users/ZhuanZ1/Desktop/学习机/tests/test_per_question_generation.py`

        ## 输出

        - `C:/Users/ZhuanZ1/Desktop/学习机/output/mock_tests`
        - `C:/Users/ZhuanZ1/Desktop/学习机/output/share_packages`
        - `C:/Users/ZhuanZ1/Desktop/学习机/output/mock_tests/2026-03-20-170434-公考职测一键模拟卷.md`

        ## 本 Obsidian 库

        - `C:/Users/ZhuanZ1/Desktop/学习机/obsidian_gongkao_archive`
        """
    ),
}


def main() -> None:
    for relative_path, content in FILES.items():
        path = VAULT / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.lstrip("\n"), encoding="utf-8")

    extra = VAULT / "test_unicode.md"
    if extra.exists():
        extra.unlink()

    print(str(VAULT))
    print(f"FILES={len(FILES)}")


if __name__ == "__main__":
    main()
