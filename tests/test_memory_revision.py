from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from finance_journal_core.app import FinanceJournalApp
from finance_journal_core.storage import json_loads


class MemoryRevisionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.runtime_root = Path(self.temp_dir.name) / "runtime"
        self.repo_root = Path(__file__).resolve().parents[1]
        self.skill_root = self.repo_root / "finance-journal-orchestrator"
        self.app = FinanceJournalApp(
            repo_root=self.repo_root,
            skill_root=self.skill_root,
            runtime_root=str(self.runtime_root),
            enable_market_data=False,
        )
        self.app.init_runtime()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_manual_revision_can_demote_wrong_memory_and_patch_skill_guards(self) -> None:
        first = self.app.log_trade(
            ts_code="603083",
            name="Alpha Optics",
            buy_date="20260410",
            buy_price=43.2,
            sell_date="20260415",
            sell_price=47.8,
            thesis="repair-flow pullback entry",
            logic_type_tags=["leader", "pullback"],
            pattern_tags=["ma_pullback"],
            market_stage_tag="range",
            environment_tags=["repair_flow", "cpo"],
            decision_context={"strategy_context": {"strategy_line": "cpo_repair_pullback"}},
        )
        second = self.app.log_trade(
            ts_code="688256",
            name="Photon Link",
            buy_date="20260411",
            buy_price=58.4,
            sell_date="20260416",
            sell_price=61.4,
            thesis="repair-flow follow-up entry",
            logic_type_tags=["leader", "pullback"],
            pattern_tags=["base_reclaim"],
            market_stage_tag="range",
            environment_tags=["repair_flow", "cpo"],
            decision_context={"strategy_context": {"strategy_line": "cpo_repair_pullback"}},
        )

        before = self.app.query_memory(
            strategy_line="cpo_repair_pullback",
            market_stage="range",
            tags="leader,pullback,repair_flow",
            limit=5,
        )
        self.assertEqual(before["matched_cells"][0]["memory_id"], first["memory_cell"]["memory_id"])

        revised = self.app.revise_memory_cell(
            first["memory_cell"]["memory_id"],
            tags=[
                "trade",
                "symbol:603083.SH",
                "strategy:cpo_repair_pullback",
                "stage:downtrend",
                "mistake:wrong_thesis",
                "error_cluster:trend_conflict",
            ],
            market_stage="downtrend",
            quality_score=-8,
            correction_note="this thesis was wrong for a shrinking downtrend tape",
        )
        revised_memory = revised["memory_cell"]
        quality = json_loads(revised_memory.get("quality_json"), {}) or {}
        tags = json_loads(revised_memory.get("tags_json"), []) or []
        self.assertEqual(revised_memory["market_stage"], "downtrend")
        self.assertEqual(quality.get("quality_score"), -8.0)
        self.assertIn("error_cluster:trend_conflict", tags)

        after = self.app.query_memory(
            strategy_line="cpo_repair_pullback",
            market_stage="range",
            tags="leader,pullback,repair_flow",
            limit=5,
        )
        self.assertEqual(after["matched_cells"][0]["memory_id"], second["memory_cell"]["memory_id"])

        skillize = self.app.skillize_memory(trade_date="20260416", lookback_days=365, min_samples=1)
        self.assertTrue(skillize["created_skills"])
        skill_id = skillize["created_skills"][0]["skill_id"]
        revised_skill = self.app.revise_skill_card(
            skill_id,
            add_do_not_use_when=["when the market is shrinking and trending down"],
            add_trigger_conditions=["stage:range"],
        )
        skill_row = revised_skill["skill_card"]
        guards = json_loads(skill_row.get("do_not_use_when_json"), []) or []
        triggers = json_loads(skill_row.get("trigger_conditions_json"), []) or []
        self.assertIn("when the market is shrinking and trending down", guards)
        self.assertIn("stage:range", triggers)


if __name__ == "__main__":
    unittest.main()
