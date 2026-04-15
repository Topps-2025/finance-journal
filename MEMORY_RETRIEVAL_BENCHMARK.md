# 交易记忆检索评测

更新日期：2026-04-15

本文档用于说明当前 `Finance Journal` 的 EverOS 风格检索评测设计，包括 benchmark、baseline、指标与本地结果。重点不是宣称“已经做成最终最优检索器”，而是用一套可复现的本地实验，说明为什么 scene / hyperedge 扩展在交易记忆场景里有价值。

## 一、评测目标

随着交易记忆不断累积，系统会遇到两个问题：

- 只靠全文匹配，容易召回字面相近但结构不对的交易。
- 只靠结构字段过滤，又会错过文本相似但字段不完整的记忆。

因此本项目的评测重点是：比较不同检索层级在“交易长程记忆召回”上的效果，验证 `graph_hybrid`（scene + hyperedge 扩展）相对普通 baseline 是否更稳定。

## 二、与 EverOS / HyperMem 的关系

本评测对应的设计动机来自以下思想：

- EverOS / EverMemOS：记忆不是 prompt 附件，而是一个显式的操作层。
- HyperMem：长期对话或长期任务中的检索，不应只依赖平面向量或词项重叠，还要考虑关系结构。
- 交易场景改造：我们把“关系”具体落在 `symbol / strategy_line / market_stage / tags / mistake cluster / scene / hyperedge` 这些字段与图结构上。

## 三、当前 benchmark 设计

基准脚本位于：`finance-journal-orchestrator/scripts/run_memory_benchmark.py`

核心实现位于：`finance_journal_core/benchmark.py`

### 1. 数据集构造

当前 benchmark 使用一个可复现的 demo corpus，由脚本自动写入本地运行时。它包含三类主题共 8 条示例交易：

- `CPO repair pullback`
- `dividend defense`
- `AI mean reversion`
- 一组 `crowded breakout` 的失败样本

这些样本会先写入交易，再重建 memory，并进一步执行 `memory skillize`，从而保证评测基于真实的“交易 -> 记忆 -> 技能”流水，而不是单独伪造一张检索表。

### 2. 查询任务

当前共有 5 个 benchmark case：

1. `text_cpo_repair`
   - 纯文本查询，刻意只保留部分词汇重合。
   - 检验图扩展是否能召回第二条相关 CPO 记忆。

2. `strategy_cpo_range`
   - 按 `strategy_line + market_stage + tags` 做结构化查询。
   - 检验结构检索与图扩展的配合。

3. `dividend_defense`
   - 防守 / 红利风格的混合查询。
   - 检验当多个候选都共享市场阶段时，系统是否还能把真正相关的防御记忆排在更前。

4. `crowded_breakout_risk`
   - 风险导向的拥挤突破失败场景。
   - 检验系统能否集中召回失败样本，而不是混入无关“上涨交易”。

5. `ai_mean_reversion`
   - AI 均值回归风格查询。
   - 检验策略线与环境标签的配合召回。

## 四、baseline 设计

当前共对比 4 种方法：

### 1. `fts_only`

只使用 `memory_cells` 文本与标签做 SQLite FTS5 全文召回。

优点：
- 实现最简单
- 适合高词项重合的情况

缺点：
- 对字段型查询不敏感
- 不能利用 scene / hyperedge 关系
- 在“文本不完整但结构很强”的查询里容易失效

### 2. `structured_only`

只按 `ts_code / strategy_line / market_stage / tags` 进行结构匹配。

优点：
- 对明确字段过滤很有效
- 结果可解释性较强

缺点：
- 不理解自由文本
- 当标签不齐、描述不标准时会漏召回
- 无法从关系结构继续扩展

### 3. `hybrid_cell_only`

在单个 `memory_cell` 级别，把全文分数与结构分数做混合。

优点：
- 比单纯 FTS 或单纯结构过滤都更稳
- 当前已经能取得不错的召回效果

缺点：
- 仍然停留在“单元级别”，不能沿着 scene / hyperedge 继续扩展
- 对跨记忆簇、跨同类场景的补召回能力有限

### 4. `graph_hybrid`

当前框架的主检索器。流程是：

1. 用全文和结构约束做粗召回
2. 按 scene 聚合与扩展
3. 按 hyperedge 进行关系扩展
4. 返回最终匹配的 `matched_cells`

这对应当前记忆架构里的创新点：在交易记忆规模越来越大时，不只让系统在“文本块”里搜，而是允许它在“交易场景图”里扩展搜索。

## 五、评测指标

当前脚本计算以下指标：

- `MRR`
- `nDCG`
- `Hit@1`
- `Hit@3`
- `Hit@5`
- `Recall@1`
- `Recall@3`
- `Recall@5`

其中本轮文档展示重点看 `MRR / nDCG / Recall@3 / Recall@5`，因为它们更适合说明“系统是否把相关历史记忆排在前面，且能否尽快把相关簇补全”。

## 六、本地结果（2026-04-15）

运行命令：

```powershell
python .\finance-journal-orchestrator\scripts\run_memory_benchmark.py --root .\_runtime_benchmark --disable-market-data --no-write-artifact
```

得到的聚合结果如下：

| 方法 | MRR | nDCG | Hit@1 | Hit@3 | Recall@3 | Recall@5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `fts_only` | 0.6000 | 0.6000 | 0.6000 | 0.6000 | 0.4000 | 0.4000 |
| `structured_only` | 0.6667 | 0.7141 | 0.6000 | 0.8000 | 0.7000 | 0.8000 |
| `hybrid_cell_only` | 1.0000 | 0.9754 | 1.0000 | 1.0000 | 0.9000 | 1.0000 |
| `graph_hybrid` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

### 结果解读

- `fts_only` 对纯文本重合场景有用，但在 `strategy_cpo_range` 与 `ai_mean_reversion` 这样的结构化查询里直接失效。
- `structured_only` 比 FTS 更稳，但在 `dividend_defense` 里会把共享市场阶段的无关记忆排到前面，说明它缺乏更细粒度的语义区分。
- `hybrid_cell_only` 已经非常强，说明“文本 + 结构混合”是一个必要基础。
- `graph_hybrid` 在当前 5 个 case 上做到 `Recall@3 = 1.0`，说明 scene / hyperedge 扩展确实提升了“把相关记忆簇尽快补齐”的能力。

## 七、case 级观察

### 1. `text_cpo_repair`

- `fts_only` 只能召回一条核心 CPO 记忆。
- `hybrid_cell_only` 已能把第二条相关 CPO 记忆带回来。
- `graph_hybrid` 在此基础上更稳定地保留相关簇，并减少纯偶然词项造成的偏差。

### 2. `dividend_defense`

这是最能说明图扩展价值的一个 case。

- `structured_only` 因为共享 `range` 阶段，前排混入了 CPO 交易。
- `hybrid_cell_only` 先命中第一条红利记忆，但第二条相关记忆被挤到更后。
- `graph_hybrid` 通过相同 scene / relation 扩展，把两条红利防守记忆放到了前两位。

### 3. `crowded_breakout_risk`

- 四种方法都能识别出至少一条核心失败案例。
- `graph_hybrid` 的优势在于更少混入无关“上涨路径”，对风险型查询更干净。

## 八、为什么这能说明框架有效

这个 benchmark 目前规模不大，但它已经能说明两件事：

1. 当前框架不是简单地把交易笔记扔进 FTS。
2. 当记忆层引入 scene / hyperedge 后，系统确实更擅长把“同一类历史经验簇”整体召回出来。

对交易场景来说，这一点非常重要，因为用户真正需要的通常不是“某一条相似句子”，而是：

- 同类 setup 的成功与失败簇
- 某个错误思路反复触发时的失败记忆簇
- 某条策略线在不同市场阶段的经验分层

## 九、如何复现实验

### 1. 直接运行 benchmark

```powershell
python .\finance-journal-orchestrator\scripts\run_memory_benchmark.py --root .\_runtime_benchmark --disable-market-data
```

### 2. 仅打印结果，不写入额外产物

```powershell
python .\finance-journal-orchestrator\scripts\run_memory_benchmark.py --root .\_runtime_benchmark --disable-market-data --no-write-artifact
```

### 3. 相关测试

```powershell
python -m unittest discover -s tests -v
```

其中 `tests/test_memory_benchmark.py` 会验证 benchmark 主流程可以在本地跑通。

## 十、当前局限

这份评测仍然是第一版，主要局限有：

- 还是 demo corpus，不是大规模真实交易历史。
- 目前没有生产级 embedding 检索基线，因此还没有“向量检索 vs 超图检索”的完整对照。
- 目前的 `graph_hybrid` 仍主要基于本地规则与分层打分，没有训练出的 learned reranker。
- 尚未覆盖跨用户、跨 agent 社区记忆交换时的检索评测。

## 十一、下一步建议

接下来比较自然的推进方向是：

1. 增加一个真正的 `vector_only` 或 `vector_hybrid` baseline。
2. 把真实复盘中的错误簇、情绪簇加入评测集。
3. 增加跨时间窗口的长期漂移测试，例如市场风格切换前后的检索稳定性。
4. 给社区记忆层设计去隐私版本的 benchmark，评测共享记忆与共享 skill card 的召回质量。

## 参考资料

1. EverOS 仓库：<https://github.com/EverMind-AI/EverOS>
2. EverMemOS: A Self-Organizing Memory Operating System for Structured Long-Horizon Reasoning：<https://arxiv.org/abs/2601.02163>
3. HyperMem: Hypergraph Memory for Long-Term Conversations：<https://arxiv.org/abs/2604.08256>
