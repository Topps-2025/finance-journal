---
name: finance-journal-orchestrator
description: OpenClaw-facing orchestration skill for conversation-first trade journaling, statement import, long-term memory retrieval, self-evolution reminders, and markdown vault sync.
---

# Finance Journal Orchestrator

## Read First

- `../FINANCE_JOURNAL_STATUS_AND_CHANGELOG.md`
- `../TRADE_MEMORY_ARCHITECTURE.md`
- `references/data-contracts.md`
- `references/openclaw-skill-functional-spec.md`
- `references/openclaw-session-contract.md`
- `references/command-cheatsheet.md`
- `references/intake-workflow.md`

## Default Workflow

- initialize runtime -> `scripts/init_finance_journal.py`
- structured CLI -> `scripts/finance_journal_cli.py`
- OpenClaw / QQ / Feishu gateway -> `scripts/finance_journal_gateway.py`
- session agent entry -> `scripts/finance_journal_session_agent.py`
- scheduler entry -> `scripts/run_finance_journal_schedule.py`

## Route by Task

- plan creation / update / historical reference -> `$trade-plan-assistant`
- trade log / statement import / post-trade review / evolution reminder -> `$trade-evolution-engine`
- behavior health report -> `$behavior-health-reporter`
- vault export and dashboard -> stay in this skill
- long-term memory rebuild / query / skillize -> stay in this skill

## Output Discipline

1. write SQLite first, then JSON / Markdown artifacts
2. sync to vault if enabled
3. make memory retrieval provenance explicit
4. make it clear which reminders come from history and which are just structured summaries
5. never output auto-trading instructions

## Boundaries

- this is a journaling and long-term memory orchestrator
- it does not fetch market news or morning briefs anymore
- skill cards are reusable review knowledge, not execution policies
