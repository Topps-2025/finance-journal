from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from .analytics import split_tags
from .storage import json_loads, make_id, safe_filename


def strategy_line_from_context(context: dict[str, Any] | None) -> str:
    payload = dict(context or {})
    strategy_context = payload.get("strategy_context")
    if not isinstance(strategy_context, dict):
        return ""
    return str(
        strategy_context.get("strategy_line")
        or strategy_context.get("strategy_name")
        or strategy_context.get("strategy_id")
        or ""
    ).strip()


def extract_tags(entity_kind: str, row: dict[str, Any]) -> list[str]:
    tags: list[str] = [entity_kind]
    if row.get("ts_code"):
        tags.append(f"symbol:{row['ts_code']}")
    if entity_kind == "plan":
        tags.extend(f"logic:{tag}" for tag in split_tags(json_loads(row.get("logic_tags_json"), [])))
        tags.extend(f"environment:{tag}" for tag in split_tags(json_loads(row.get("environment_tags_json"), [])))
        if row.get("market_stage_tag"):
            tags.append(f"stage:{row['market_stage_tag']}")
    elif entity_kind == "trade":
        tags.extend(f"logic:{tag}" for tag in split_tags(json_loads(row.get("logic_type_tags_json"), [])))
        tags.extend(f"pattern:{tag}" for tag in split_tags(json_loads(row.get("pattern_tags_json"), [])))
        tags.extend(f"environment:{tag}" for tag in split_tags(json_loads(row.get("environment_tags_json"), [])))
        tags.extend(f"mistake:{tag}" for tag in split_tags(json_loads(row.get("mistake_tags_json"), [])))
        if row.get("market_stage_tag"):
            tags.append(f"stage:{row['market_stage_tag']}")
        if row.get("status"):
            tags.append(f"status:{row['status']}")
    elif entity_kind == "review":
        if row.get("review_type"):
            tags.append(f"review:{row['review_type']}")
        if row.get("status"):
            tags.append(f"review_status:{row['status']}")
    strategy_line = strategy_line_from_context(json_loads(row.get("decision_context_json"), {}))
    if strategy_line:
        tags.append(f"strategy:{strategy_line}")
    return list(dict.fromkeys(tag for tag in tags if tag))


def build_memory_title(entity_kind: str, row: dict[str, Any]) -> str:
    label = str(row.get("name") or row.get("ts_code") or row.get("trade_id") or row.get("plan_id") or row.get("review_id") or "").strip()
    if entity_kind == "plan":
        return f"Plan | {label}"
    if entity_kind == "review":
        return f"Review | {label}"
    return f"Trade | {label}"


def build_memory_text(entity_kind: str, row: dict[str, Any]) -> str:
    parts: list[str] = []
    for value in (
        row.get("name"),
        row.get("ts_code"),
        row.get("thesis"),
        row.get("buy_reason"),
        row.get("sell_reason"),
        row.get("emotion_notes"),
        row.get("lessons_learned"),
        row.get("prompt_text"),
        row.get("feedback"),
        row.get("notes"),
    ):
        text = str(value or "").strip()
        if text:
            parts.append(text)
    decision_context = json_loads(row.get("decision_context_json"), {}) or {}
    for key in ("interpretation", "position_reason", "emotion_notes", "risk_boundary", "factor_selection_reason", "activation_reason", "subjective_override"):
        text = str(decision_context.get(key) or "").strip()
        if text:
            parts.append(text)
    return "\n".join(dict.fromkeys(parts))


def build_memory_summary(entity_kind: str, row: dict[str, Any]) -> dict[str, Any]:
    summary = {
        "entity_kind": entity_kind,
        "entity_id": row.get("plan_id") or row.get("trade_id") or row.get("review_id") or "",
        "ts_code": row.get("ts_code") or "",
        "name": row.get("name") or "",
        "trade_date": row.get("buy_date") or row.get("valid_from") or row.get("review_due_date") or "",
        "status": row.get("status") or "",
    }
    if entity_kind == "trade":
        summary["actual_return_pct"] = row.get("actual_return_pct")
        summary["timing_alpha_pct"] = row.get("timing_alpha_pct")
    return summary


def build_memory_quality(entity_kind: str, row: dict[str, Any]) -> dict[str, Any]:
    quality: dict[str, Any] = {"entity_kind": entity_kind}
    if entity_kind == "trade":
        quality.update(
            {
                "status": row.get("status") or "",
                "actual_return_pct": row.get("actual_return_pct"),
                "timing_alpha_pct": row.get("timing_alpha_pct"),
                "holding_days": row.get("holding_days"),
                "review_status": row.get("review_status") or "",
            }
        )
    elif entity_kind == "review":
        quality.update(
            {
                "review_type": row.get("review_type") or "",
                "max_gain_pct": row.get("max_gain_pct"),
                "max_drawdown_pct": row.get("max_drawdown_pct"),
            }
        )
    else:
        quality.update(
            {
                "valid_from": row.get("valid_from") or "",
                "valid_to": row.get("valid_to") or "",
                "status": row.get("status") or "",
            }
        )
    return quality


def build_memory_provenance(entity_kind: str, row: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_entity_kind": entity_kind,
        "source_entity_id": row.get("plan_id") or row.get("trade_id") or row.get("review_id") or "",
        "updated_at": row.get("updated_at") or row.get("created_at") or "",
    }


def scene_keys_for_row(entity_kind: str, row: dict[str, Any]) -> list[tuple[str, str, str]]:
    tags = extract_tags(entity_kind, row)
    keys: list[tuple[str, str, str]] = []
    ts_code = str(row.get("ts_code") or "").strip()
    if ts_code:
        keys.append((f"symbol:{ts_code}", "symbol", f"Symbol Scene | {row.get('name') or ts_code}"))
    strategy_line = strategy_line_from_context(json_loads(row.get("decision_context_json"), {}) or {})
    if strategy_line:
        keys.append((f"strategy:{strategy_line}", "strategy", f"Strategy Scene | {strategy_line}"))
    market_stage = str(row.get("market_stage_tag") or "").strip()
    if market_stage:
        keys.append((f"stage:{market_stage}", "stage", f"Stage Scene | {market_stage}"))
    top_logic = next((tag.split(":", 1)[1] for tag in tags if tag.startswith("logic:")), "")
    top_pattern = next((tag.split(":", 1)[1] for tag in tags if tag.startswith("pattern:")), "")
    if top_logic or top_pattern:
        label = " / ".join(part for part in (top_logic, top_pattern) if part)
        keys.append((f"setup:{safe_filename(label)}", "setup", f"Setup Scene | {label}"))
    return keys


def hyperedge_specs_for_row(entity_kind: str, row: dict[str, Any]) -> list[dict[str, str]]:
    tags = extract_tags(entity_kind, row)
    specs: list[dict[str, str]] = []
    for tag in tags:
        if ":" not in tag:
            continue
        edge_type, label = tag.split(":", 1)
        specs.append(
            {
                "edge_key": f"{edge_type}:{label}",
                "edge_type": edge_type,
                "label": label,
            }
        )
    return specs


def memory_query_tokens(
    *,
    text: str = "",
    ts_code: str = "",
    strategy_line: str = "",
    market_stage: str = "",
    tags: Iterable[str] | None = None,
) -> list[str]:
    tokens = [item for item in split_tags(tags) if item]
    if ts_code:
        tokens.append(f"symbol:{ts_code}")
    if strategy_line:
        tokens.append(f"strategy:{strategy_line}")
    if market_stage:
        tokens.append(f"stage:{market_stage}")
    if text:
        tokens.extend(split_tags(text.replace("\n", " ")))
    return list(dict.fromkeys(token for token in tokens if token))


def score_memory_row(
    row: dict[str, Any],
    *,
    text: str = "",
    ts_code: str = "",
    strategy_line: str = "",
    market_stage: str = "",
    tags: Iterable[str] | None = None,
) -> float:
    score = 0.0
    requested_tags = set(memory_query_tokens(text=text, ts_code=ts_code, strategy_line=strategy_line, market_stage=market_stage, tags=tags))
    row_tags = set(split_tags(json_loads(row.get("tags_json"), [])))
    score += float(len(requested_tags & row_tags)) * 2.0
    if ts_code and row.get("ts_code") == ts_code:
        score += 4.0
    if strategy_line and row.get("strategy_line") == strategy_line:
        score += 2.5
    if market_stage and row.get("market_stage") == market_stage:
        score += 1.5
    body = f"{row.get('title') or ''}\n{row.get('text_body') or ''}".lower()
    for token in split_tags(text):
        if token and token.lower() in body:
            score += 1.0
    quality = json_loads(row.get("quality_json"), {}) or {}
    pnl = quality.get("actual_return_pct")
    if isinstance(pnl, (int, float)):
        score += max(min(float(pnl) / 10.0, 2.0), -2.0)
    return round(score, 4)


def summarize_scene(memory_rows: list[dict[str, Any]], *, scene_key: str, scene_type: str, title: str) -> dict[str, Any]:
    tags_counter: Counter[str] = Counter()
    ts_code = ""
    strategy_line = ""
    market_stage = ""
    trade_dates: list[str] = []
    memory_ids: list[str] = []
    for row in memory_rows:
        tags_counter.update(split_tags(json_loads(row.get("tags_json"), [])))
        if not ts_code and row.get("ts_code"):
            ts_code = str(row.get("ts_code") or "")
        if not strategy_line and row.get("strategy_line"):
            strategy_line = str(row.get("strategy_line") or "")
        if not market_stage and row.get("market_stage"):
            market_stage = str(row.get("market_stage") or "")
        if row.get("trade_date"):
            trade_dates.append(str(row.get("trade_date") or ""))
        if row.get("memory_id"):
            memory_ids.append(str(row.get("memory_id") or ""))
    description = f"{title} aggregates {len(memory_rows)} memory cells."
    return {
        "scene_id": make_id("scene"),
        "scene_key": scene_key,
        "scene_type": scene_type,
        "title": title,
        "description": description,
        "trade_date": max(trade_dates) if trade_dates else "",
        "ts_code": ts_code,
        "strategy_line": strategy_line,
        "market_stage": market_stage,
        "tags_json": tags_counter.most_common(12),
        "memory_ids_json": memory_ids,
        "stats_json": {"memory_count": len(memory_rows)},
    }
