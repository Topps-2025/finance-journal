# Finance Journal（中文说明）

更新日期：2026-04-15

`Finance Journal` 现在聚焦于一个核心问题：把 OpenClaw 式交互编排、交易流水、复盘反思与长程交易记忆结合起来，形成一个本地优先、可持续沉淀、可检索、可演化的交易记忆框架。

它不是新闻快讯系统、公告抓取器，也不是跟单或自动下单系统。

## 一、当前定位

这个仓库主要解决以下几类问题：

- 用自然语言把计划、交易、复盘记下来，而不是先手填大量表单。
- 把计划、成交、复盘沉淀为结构化账本与长程记忆，而不是散落的笔记。
- 在后续交互中召回历史上相似的交易记忆、错误模式和稳定路径。
- 通过 bandit 式优先级调整，让高价值提醒更容易再次出现。
- 把稳定的历史路径固化为 skill card，形成可复用的交易知识与社区资产。

## 二、仓库结构

- `finance-journal-orchestrator/`：面向 OpenClaw 的会话入口、网关脚本与参考文档。
- `trade-plan-assistant/`：计划创建、计划补全、计划历史参考。
- `trade-evolution-engine/`：交易复盘、自进化提醒、bandit 优先级输出。
- `behavior-health-reporter/`：行为纪律、健康度、风格画像等报告。
- `finance_journal_core/`：共享运行时、SQLite 存储、记忆层、检索层、vault 导出。
- `tests/`：围绕记忆流、修正流、benchmark 的本地测试。

## 三、运行时产物

- SQLite 数据库：`_runtime/data/finance_journal.db`
- 每日产物：`_runtime/artifacts/daily/YYYYMMDD/`
- 长程记忆快照：`_runtime/memory/`
- Markdown / Obsidian vault：`_runtime/obsidian-vault/`

## 四、长程交易记忆设计

当前的记忆层借鉴了 EverOS / EverMemOS / HyperMem 的设计思想，但落地到交易场景时做了本地化改造。

### 1. `memory_cells`

原子记忆单元。每个 plan / trade / review 都会被抽取成一个可检索的记忆单元，包含：

- 来源实体 id 与类型
- 交易日期、标的、策略线、市场阶段
- 归一化文本主体
- 摘要、标签、质量分与溯源信息

### 2. `memory_scenes`

场景层。把离散的记忆单元组织成可复用的“场景表面”，例如：

- 标的场景
- setup 场景
- 市场阶段场景
- 策略线场景

### 3. `memory_hyperedges`

超边层。用于描述多元关系，而不仅是两两连接，例如：

- 标的 + setup + 市场阶段
- 错误簇 + 风险风格 + 情绪状态
- 策略线 + 环境标签 + 失败模式

### 4. `memory_skill_cards`

技能卡层。把长期稳定、证据充分的高价值路径固化为可复用技能卡，记录：

- 触发条件
- 禁止使用条件
- 证据交易
- 样本数
- bandit 快照
- 是否可社区共享

## 五、检索流程

当前检索是一个 coarse-to-fine 的分层流程：

1. SQLite FTS5 全文召回
2. 结构化过滤：标的 / 市场阶段 / 策略线 / 标签
3. scene 与 hyperedge 扩展
4. bandit 感知的 reminder rerank

这意味着：bandit 仍然保留，但它不再负责“从零找到候选”，而是站在更强的记忆召回层之上做优先级排序。

## 六、错误输入与局部修正

这个框架不是自动裁判用户“对错”的 oracle，但它可以通过历史证据和本地可编辑机制来帮助修正错误理解：

- 相似失败案例会在检索时被召回，形成隐式反证。
- 复盘可以写入“纠错记忆”，下次再次出现时参与召回。
- 可以手动修订记忆标签、市场阶段、质量分与纠错说明。
- 可以直接给技能卡补充 `do_not_use_when` 禁止条件。
- 错误路径在 bandit 层会逐步降权，而不是被强行立即删除。

详细说明见 `ERROR_INPUT_CORRECTION.md`。

## 七、关键命令

```powershell
python .\finance-journal-orchestrator\scripts\finance_journal_cli.py init
python .\finance-journal-orchestrator\scripts\finance_journal_cli.py session turn --session-key qq:user_a --trade-date 20260410 --text "今天买了603083"
python .\finance-journal-orchestrator\scripts\finance_journal_cli.py trade import-statement --file .\examples\statement_rows.csv --trade-date 20260415 --session-key qq:user_a
python .\finance-journal-orchestrator\scripts\finance_journal_cli.py evolution remind --logic-tags leader,pullback --pattern-tags ma_pullback --market-stage range --environment-tags repair_flow
python .\finance-journal-orchestrator\scripts\finance_journal_cli.py memory rebuild
python .\finance-journal-orchestrator\scripts\finance_journal_cli.py memory query --ts-code 603083 --market-stage range --tags leader,pullback
python .\finance-journal-orchestrator\scripts\finance_journal_cli.py memory revise memory_trade_xxx --add-tags error_cluster:trend_conflict --quality-score -8 --market-stage downtrend --correction-note "下跌趋势追突破，这个思路有误"
python .\finance-journal-orchestrator\scripts\finance_journal_cli.py memory skill-edit skill_quality_path_xxx --add-do-not-use-when "当市场缩量下跌时禁止使用"
python .\finance-journal-orchestrator\scripts\finance_journal_cli.py memory skillize --trade-date 20260415 --lookback-days 365
python .\finance-journal-orchestrator\scripts\run_memory_benchmark.py --root .\_runtime_benchmark --disable-market-data
python .\finance-journal-orchestrator\scripts\finance_journal_cli.py vault sync --trade-date 20260415
```

## 八、推荐阅读顺序

- `TRADE_MEMORY_ARCHITECTURE.md`：简洁版记忆架构说明
- `TRADE_MEMORY_SYSTEM_PAPER.md`：论文风格的架构说明，便于后续 LaTeX 整理
- `OPENCLAW_DEMO_WORKFLOW.md`：面向课程展示的完整 OpenClaw 工作流
- `MEMORY_RETRIEVAL_BENCHMARK.md`：EverOS 风格的检索评测、baseline 与结果
- `ERROR_INPUT_CORRECTION.md`：错误输入如何暴露、修正、降权、固化边界
- `IMPLEMENTED_FEATURES.md`：已经完成的功能
- `NOT_IMPLEMENTED_YET.md`：仍然保留为空白或后续扩展的边界

## 九、公开仓与私有仓的同步边界

- 公共仓 `origin/main`：推送核心代码、测试与通用说明文档。
- 私有仓 `github-private/private-sync`：可额外同步运行数据、券商流水、私有 vault 快照等敏感内容。
- `_runtime*`、`*.db`、券商导出表等默认应保持忽略；只有在明确需要做私有同步时才追加上传。

## 十、当前验证方式

```powershell
python -m compileall finance_journal_core finance-journal-orchestrator\scripts tests
python -m unittest discover -s tests -v
```

## 参考资料

1. EverOS 仓库：<https://github.com/EverMind-AI/EverOS>
2. EverMemOS: A Self-Organizing Memory Operating System for Structured Long-Horizon Reasoning：<https://arxiv.org/abs/2601.02163>
3. HyperMem: Hypergraph Memory for Long-Term Conversations：<https://arxiv.org/abs/2604.08256>
