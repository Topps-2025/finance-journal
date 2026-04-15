# Trade Memory System Paper Note

Updated: 2026-04-15

This document is written in a paper-style structure and keeps equations in standard Markdown math blocks so it can be rendered by GitHub MathJax-compatible viewers, Pandoc, Quarto, or exported into LaTeX later.

## Abstract

We redesign Finance Journal as a local-first trading-memory operating layer. Instead of treating journaling records as flat notes, we organize them into atomic memory cells, scene-level summaries, hypergraph relations, and reusable skill cards. The retrieval pipeline combines full-text recall, structured filters, scene and hyperedge expansion, and bandit-aware reranking. This architecture is inspired by EverOS, EverMemOS, and HyperMem, but adapted to the special constraints of trading records: sparse rewards, long feedback loops, privacy-sensitive data, and the need to turn stable review trajectories into reusable community knowledge.

## 1. Problem Setting

A trading journal grows along three axes at the same time:
- event count keeps increasing
- strategy contexts drift with market regimes
- useful knowledge is often buried inside free-text reflections

A flat note system eventually fails because it cannot answer the following questions reliably:
- which historical trades match the current setup and regime?
- which mistakes repeatedly co-occur with the same trigger pattern?
- which paths are stable enough to be promoted into reusable skills?

We therefore model the journal as a long-horizon memory system instead of a collection of isolated notes.

## 2. System Objective

Let the memory operating layer be

$$
\mathcal{M} = (\mathcal{C}, \mathcal{S}, \mathcal{H}, \mathcal{K}),
$$

where:
- $\mathcal{C}$ is the set of atomic memory cells
- $\mathcal{S}$ is the set of scenes
- $\mathcal{H}$ is the set of hyperedges
- $\mathcal{K}$ is the set of skill cards

Given a query context $q$, the system should return a ranked subset of memories and skills that maximize decision usefulness under privacy and local-runtime constraints.

## 3. Architecture Layers

### 3.1 Memory Cells

A memory cell is created from a plan, trade, or review record. Each cell stores:
- source entity kind and source entity id
- trade date and symbol
- strategy line and market stage
- normalized text body
- summary, quality, and provenance metadata

In the codebase this is implemented primarily in:
- `finance_journal_core/memory.py`
- `finance_journal_core/app.py`
- `finance_journal_core/storage.py`

### 3.2 Scenes

Scenes provide the middle layer between raw cells and high-level retrieval. A scene may represent:
- a symbol-specific memory surface
- a setup pattern
- a market stage
- a strategy line

This layer improves long-horizon recall by grouping atomic events into reusable decision contexts.

### 3.3 Hypergraph Relations

A simple graph links pairs; a hypergraph links multi-way structure. In trading memory this matters because the relevant object is often not a single node but a tuple such as:
- symbol + setup + market stage
- setup + mistake cluster + risk posture
- strategy line + regime + execution style

Hyperedges capture these relations and let retrieval move across structurally related memories.

### 3.4 Skill Cards

A skill card is a distilled reusable capability extracted from repeated high-value paths. It is not a trading bot and not a copy-trading rule. It stores:
- trigger conditions
- do-not-use conditions
- supporting evidence trades
- sample size
- bandit snapshot
- community-shareable flag

This turns long-term journal evidence into reusable review-time skills.

## 4. Retrieval Pipeline

For a query $q$, each candidate memory cell $c$ is scored by a hybrid function:

$$
\mathrm{score}(c \mid q) = \alpha \cdot s_{\mathrm{fts}} + \beta \cdot s_{\mathrm{struct}} + \gamma \cdot s_{\mathrm{scene}} + \delta \cdot s_{\mathrm{hyper}},
$$

where:
- $s_{\mathrm{fts}}$ is the SQLite FTS5 recall score
- $s_{\mathrm{struct}}$ is the exact or fuzzy structured match score over symbol, tags, stage, and strategy line
- $s_{\mathrm{scene}}$ is the scene-level aggregation score
- $s_{\mathrm{hyper}}$ is the relation-expansion score through hyperedges

In the current implementation, coarse recall is done locally with SQLite FTS5 and structured filters, then scenes and hyperedges expand the candidate set.

## 5. Bandit-Compatible Reminder Layer

We keep the original bandit-style evolution layer because trade data is still sparse and delayed. The memory system is therefore the recall layer, while the bandit remains the top-layer prioritizer.

For a candidate action or reminder $a$, a simplified upper-confidence style ranking can be written as:

$$
U(a) = \hat{\mu}_a + \lambda \sqrt{\frac{\ln(1 + N)}{1 + n_a}},
$$

where $\hat{\mu}_a$ is the empirical utility estimate, $n_a$ is the usage count of that path, and $N$ is the total interaction count.

This preserves the existing evolution logic while allowing better recall from larger journals.

## 6. Skill Solidification Criterion

A historical path is eligible for skill-card solidification when it has enough evidence and sufficiently conservative quality. One practical decision rule is:

$$
\mathrm{skillize}(p) = \mathbb{1}[n_p \ge n_{\min}] \cdot \mathbb{1}[\bar{r}_p - \eta \sigma_p > \tau],
$$

where:
- $n_p$ is the sample size for path $p$
- $n_{\min}$ is the minimum evidence threshold
- $\bar{r}_p$ is the average realized utility or return proxy
- $\sigma_p$ is the path volatility or uncertainty term
- $\eta$ controls conservativeness
- $\tau$ is the promotion threshold

The current code uses a simpler operational approximation based on sample counts and bandit snapshots, but this formula provides the intended research direction.

## 7. Community Memory Vision

The architecture is designed for a future community layer in which users and agents exchange:
- memory cards derived from real trading reflections
- skill cards distilled from stable historical paths
- provenance metadata for trust and moderation

This is explicitly different from copy trading. The goal is not to broadcast standardized signals, but to share reusable decision memory and reusable reflective skills.

## 8. Implementation Mapping

The current repository maps the architecture into the following files:
- `finance_journal_core/storage.py`: SQLite schema and runtime storage bootstrap
- `finance_journal_core/memory.py`: memory summaries, tags, scene keys, hyperedge specs, and retrieval scoring helpers
- `finance_journal_core/app.py`: memory sync, query, skillization, session integration, and bandit-backed reminders
- `finance_journal_core/vault.py`: Markdown exports for memory notes and skill notes
- `finance_journal_core/cli.py`: memory-centric CLI surface
- `finance_journal_core/gateway.py`: gateway routing for memory, plan, trade, review, and schedule commands
- `tests/test_finance_journal_smoke.py`: local validation of the memory-centric workflow

## 9. Current Limitations

The current system still does not provide:
- production embeddings or learned vector reranking
- federated memory exchange between multiple runtimes
- a reproducible benchmark suite for retrieval ablations
- automatic privacy sanitization when promoting private data into public artifacts

## 10. References

1. EverOS repository
   - https://github.com/EverMind-AI/EverOS
2. EverMemOS: A Self-Organizing Memory Operating System for Structured Long-Horizon Reasoning
   - https://arxiv.org/abs/2601.02163
3. HyperMem: Hypergraph Memory for Long-Term Conversations
   - https://arxiv.org/abs/2604.08256
