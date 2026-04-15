# OpenClaw 演示工作流

更新日期：2026-04-15

这份文档用于课程展示，目标是把 `finance-journal-orchestrator` 作为 OpenClaw `skills/` 目录中的会话型技能来演示，重点展示三件事：

1. 大模型如何把自然语言交易表达转成结构化账本
2. 大模型如何依赖 `session_key` 做多轮追问与补充
3. 大模型如何把交易记录沉淀为长程记忆，并在后续会话中召回

## 一、演示前准备

### 1. 仓库位置

假设仓库位于：

```powershell
D:\skills\finance-journal
```

### 2. 初始化运行时

第一次演示前先执行：

```powershell
python .\finance-journal-orchestrator\scripts\finance_journal_cli.py init --disable-market-data
```

预期会生成：

- `_runtime/data/finance_journal.db`
- `_runtime/artifacts/`
- `_runtime/memory/`
- `_runtime/obsidian-vault/`

### 3. 推荐演示入口

课程展示时，最推荐直接使用会话入口：

```powershell
python .\finance-journal-orchestrator\scripts\finance_journal_session_agent.py `
  --disable-market-data `
  --session-key qq:demo_user `
  --trade-date 20260410 `
  --text "今天买了603083"
```

这个入口的意义是：

- OpenClaw 只负责把用户原话和 `session_key` 传进来。
- Finance Journal 自己判断当前属于新建草稿、继续补充、自动落账，还是对最近一笔实体做二次沉淀。

## 二、OpenClaw 最小调用约定

每轮最少提供：

- `session_key`：会话唯一键，例如 `qq:demo_user`
- `text`：用户原始输入

建议额外提供：

- `trade_date`：交易日期，例如 `20260410`
- `mode`：`auto` / `trade` / `plan`
- `lookback_days`：回看窗口

推荐的 `session_key` 规范：

- QQ 私聊：`qq:<user_id>`
- QQ 群聊：`qq:<group_id>:<user_id>`
- 飞书私聊：`feishu:<open_id>`
- 飞书群聊：`feishu:<chat_id>:<open_id>`

## 三、完整会话演示流程

### 1. 第一步：用户给出一个很粗的交易描述

用户输入：

```text
今天买了603083
```

OpenClaw 调用：

```powershell
python .\finance-journal-orchestrator\scripts\finance_journal_session_agent.py `
  --disable-market-data `
  --session-key qq:demo_user `
  --trade-date 20260410 `
  --text "今天买了603083"
```

典型返回片段：

```json
{
  "route": "draft_started",
  "assistant_message": "我先帮你起草好了，当前还缺：buy_price、thesis。下一个问题：实际买入价格是多少？例如：43.2。",
  "session_state": {
    "pending_question": "实际买入价格是多少？"
  }
}
```

这一轮要强调：

- 用户没有被迫先填完整表单
- 系统先起草，再追一个关键问题
- 会话状态已经被记住

### 2. 第二步：继续补字段

用户继续输入：

```text
43.2
```

再次调用同一个 `session_key`：

```powershell
python .\finance-journal-orchestrator\scripts\finance_journal_session_agent.py `
  --disable-market-data `
  --session-key qq:demo_user `
  --trade-date 20260410 `
  --text "43.2"
```

典型返回：

```json
{
  "route": "draft_continued",
  "assistant_message": "我先帮你起草好了，当前还缺：thesis。下一个问题：这笔交易最核心的逻辑是什么？请用一句话概括。",
  "session_state": {
    "pending_question": "这笔交易最核心的逻辑是什么？请用一句话概括。"
  }
}
```

### 3. 第三步：补齐 thesis 并自动落账

用户继续输入：

```text
CPO 修复回流低吸
```

再次调用：

```powershell
python .\finance-journal-orchestrator\scripts\finance_journal_session_agent.py `
  --disable-market-data `
  --session-key qq:demo_user `
  --trade-date 20260410 `
  --text "CPO 修复回流低吸"
```

典型返回：

```json
{
  "route": "draft_applied",
  "assistant_message": "已记入交易账本。类型=open_trade | 标的=603083.SH | 买入日=20260410 | 买价=43.2 ...",
  "result": {
    "trade": {
      "trade_id": "trade_..."
    },
    "memory_cell": {
      "memory_id": "memory_trade_..."
    }
  },
  "session_state": {
    "active_entity_kind": "trade",
    "active_entity_id": "trade_...",
    "pending_question": "真正触发你出手/离场的那个信号是什么？尽量描述你当时看到的市场状态。"
  }
}
```

这一段适合展示：

- SQLite 账本已经落地
- `memory_cell` 已同步生成
- 后续补充会默认沉淀回最近这条交易

### 4. 第四步：做二次沉淀

用户补一句：

```text
补充：当时有点急，属于偏早试错
```

再次调用同一个 `session_key`：

```powershell
python .\finance-journal-orchestrator\scripts\finance_journal_session_agent.py `
  --disable-market-data `
  --session-key qq:demo_user `
  --trade-date 20260410 `
  --text "补充：当时有点急，属于偏早试错"
```

期望路由：

```json
{
  "route": "entity_enriched",
  "result": {
    "updated_fields": [
      "emotion_notes",
      "mistake_tags",
      "notes"
    ],
    "memory_cell": {
      "memory_id": "memory_trade_..."
    }
  }
}
```

这里可以说明：

- 系统不是新建第二条记录
- 而是在最近交易上做二次沉淀
- 长程记忆也会随之刷新

## 四、OpenClaw 并行轮询展示

Finance Journal 不只会返回一个 `next_question`，还会返回 `polling_bundle.parallel_question_groups`，便于上层 UI 把多个相关问题打包成一个并行补问块。

### 1. 获取并行补问块

示例：

```powershell
python .\finance-journal-orchestrator\scripts\finance_journal_cli.py intake parse `
  --mode plan `
  --trade-date 20260410 `
  --text "Plan 603083 buy on pullback, 42.5-43.0, stop 40, repair flow, CPO"
```

返回中的重点片段：

```json
{
  "polling_bundle": {
    "next_question": "你的止损条件是什么？最好给出价格或触发条件。",
    "shared_context_hints": [
      {
        "scope": "trade_date",
        "label": "同日市场环境"
      },
      {
        "scope": "symbol",
        "label": "同票主线 / 做T 复用"
      }
    ],
    "parallel_question_groups": [
      {
        "group": "market_context_block",
        "scope": "trade_date",
        "fields": [
          "environment_tags",
          "observed_signals"
        ],
        "question": "如果同一天市场看法一致，可一次回答关注对象、环境标签和触发信号。"
      }
    ]
  }
}
```

### 2. OpenClaw 上层推荐处理方式

推荐的 UI 逻辑：

1. 如果只有 `next_question`，继续单问单答。
2. 如果存在 `parallel_question_groups`，把一个 group 渲染成一个并行补问卡片。
3. 用户一次回答后，再继续回传同一个 `session_key`。

伪代码示例：

```python
payload = call_session_agent(session_key, text, trade_date)
reply_to_user(payload["assistant_message"])

bundle = (payload.get("draft") or {}).get("polling_bundle") or (payload.get("result") or {}).get("polling_bundle") or {}
if bundle.get("parallel_question_groups"):
    render_parallel_block(bundle["parallel_question_groups"][0])
elif (payload.get("session_state") or {}).get("pending_question"):
    render_single_question((payload["session_state"] or {})["pending_question"])
```

## 五、Gateway 模式展示

如果课程上还想展示“平台网关先统一转命令，再调 skill”，可以使用：

```powershell
python .\finance-journal-orchestrator\scripts\finance_journal_gateway.py `
  --command "session turn session=qq:demo_user trade_date=20260410 text='今天买了603083'"
```

这适合说明：

- OpenClaw 可以直接起 `session` 调用
- 也可以先过一层统一网关协议

## 六、演示时可展示的产物

建议明确告诉学生：系统不是只返回一段聊天文本，而是会同步生成多层产物。

### 1. 结构化存储

- SQLite：`_runtime/data/finance_journal.db`
- 核心表：`plans`、`trades`、`reviews`、`memory_cells`、`memory_scenes`、`memory_hyperedges`、`memory_skill_cards`

### 2. 每日产物

- `_runtime/artifacts/daily/YYYYMMDD/*.json`
- `_runtime/artifacts/daily/YYYYMMDD/*.md`

### 3. 长程记忆

- `_runtime/memory/*.json`
- `_runtime/memory/*.md`

### 4. Vault 导出

- `_runtime/obsidian-vault/01-plans/`
- `_runtime/obsidian-vault/02-trades/`
- `_runtime/obsidian-vault/06-memory/`
- `_runtime/obsidian-vault/07-skills/`

## 七、课堂推荐展示顺序

建议按这个顺序讲：

1. OpenClaw 如何接收用户原话
2. `assistant_message` 如何引导下一轮
3. `route` 如何在 `draft_started -> draft_continued -> draft_applied -> entity_enriched` 之间切换
4. `session_state.pending_question` 如何驱动轮询
5. `memory_retrieval` / `memory_checklist` 如何把历史记忆带回当前会话
6. `_runtime/` 中实际生成的 JSON / Markdown / SQLite / vault 文件

## 八、最短演示脚本

```powershell
python .\finance-journal-orchestrator\scripts\finance_journal_cli.py init --disable-market-data
python .\finance-journal-orchestrator\scripts\finance_journal_session_agent.py --disable-market-data --session-key qq:demo_user --trade-date 20260410 --text "今天买了603083"
python .\finance-journal-orchestrator\scripts\finance_journal_session_agent.py --disable-market-data --session-key qq:demo_user --trade-date 20260410 --text "43.2"
python .\finance-journal-orchestrator\scripts\finance_journal_session_agent.py --disable-market-data --session-key qq:demo_user --trade-date 20260410 --text "CPO 修复回流低吸"
python .\finance-journal-orchestrator\scripts\finance_journal_session_agent.py --disable-market-data --session-key qq:demo_user --trade-date 20260410 --text "补充：当时有点急，属于偏早试错"
python .\finance-journal-orchestrator\scripts\finance_journal_cli.py vault sync --trade-date 20260410 --disable-market-data
```

## 九、课程讲解关键词

可以直接用以下关键词收尾：

- 对话式记账
- 会话状态驱动轮询
- 交易记忆回流
- scene / hyperedge 检索
- 记忆到技能固化

这套流程既能展示“大模型如何与用户多轮交互”，也能展示“框架如何把交互沉淀成可复用的交易长程记忆系统”。
