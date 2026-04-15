from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from finance_journal_core.app import FinanceJournalApp
from finance_journal_core.gateway import dispatch


class FinanceJournalSmokeTest(unittest.TestCase):
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

    def test_core_trade_memory_flow(self) -> None:
        plan_result = self.app.create_plan(
            ts_code="603083",
            name="剑桥科技",
            direction="buy",
            thesis="回踩 5 日线参与",
            logic_tags=["龙头首阴", "低吸"],
            market_stage="震荡市",
            environment_tags=["修复回流", "CPO"],
            buy_zone="42.5-43.0",
            stop_loss="40.0",
            valid_from="20260410",
            valid_to="20260415",
            decision_context={
                "user_focus": ["剑桥科技", "CPO"],
                "observed_signals": ["回踩 5 日线", "板块修复"],
                "position_reason": "试错仓先参与",
                "strategy_context": {
                    "strategy_line": "cpo_repair_pullback",
                    "strategy_family": "semi_systematic",
                },
            },
            with_reference=True,
        )
        plan_id = plan_result["plan"]["plan_id"]
        self.assertTrue(plan_result["plan"]["memory_cell"]["memory_id"].startswith("memory_plan_"))

        trade = self.app.log_trade(
            ts_code="603083",
            name="剑桥科技",
            plan_id=plan_id,
            buy_date="20260410",
            buy_price=43.2,
            thesis="回踩 5 日线参与",
            logic_type_tags=["龙头首阴", "低吸"],
            pattern_tags=["均线回踩"],
            market_stage_tag="震荡市",
            environment_tags=["修复回流", "CPO"],
            emotion_notes="盘中有点急。",
            mistake_tags=["冲动"],
            notes="第一次试错单。",
            decision_context={
                "user_focus": ["剑桥科技"],
                "observed_signals": ["分时止跌"],
                "position_reason": "先拿一笔验证修复",
                "strategy_context": {"strategy_line": "cpo_repair_pullback"},
            },
        )
        trade_id = trade["trade_id"]
        self.assertTrue(trade["memory_cell"]["memory_id"].startswith("memory_trade_"))
        self.assertTrue(Path(trade["vault_note"]["path"]).exists())

        enriched = self.app.enrich_trade_from_text(
            trade_id,
            "补充：更像高位分歧后的修复回流，经验：下次先等量能回暖确认。",
            trade_date="20260410",
        )
        self.assertTrue(enriched["memory_cell"]["memory_id"].startswith("memory_trade_"))

        closed = self.app.close_trade(
            trade_id,
            sell_date="20260415",
            sell_price=46.8,
            sell_reason="达到预设止盈",
            lessons_learned="更适合分批卖出。",
        )
        self.assertEqual(closed["status"], "closed")
        self.assertTrue(closed["memory_cell"]["memory_id"].startswith("memory_trade_"))

        memory_query = self.app.query_memory(
            ts_code="603083",
            market_stage="震荡市",
            tags=["龙头首阴", "低吸", "修复回流"],
            limit=5,
        )
        self.assertTrue(memory_query["matched_cells"])

        reminder = self.app.generate_evolution_reminder(
            logic_tags=["龙头首阴", "低吸"],
            pattern_tags=["均线回踩"],
            market_stage="震荡市",
            environment_tags=["修复回流"],
            trade_date="20260415",
            write_artifact=False,
        )
        self.assertIn("memory_candidates", reminder)
        self.assertIn("linked_skill_cards", reminder)

        skillize = self.app.skillize_memory(trade_date="20260415", lookback_days=365, min_samples=1)
        self.assertTrue(skillize["created_skills"])
        self.assertTrue(skillize["created_skills"][0]["skill_id"].startswith("skill_"))

        sync_result = self.app.sync_vault(trade_date="20260415", limit=20)
        self.assertTrue(sync_result["enabled"])
        self.assertTrue(any("06-memory" in path or "07-skills" in path for path in sync_result["paths"]))

    def test_session_turn_returns_memory_context(self) -> None:
        self.app.log_trade(
            ts_code="600519",
            name="贵州茅台",
            buy_date="20260410",
            buy_price=1350,
            thesis="高股息修复低吸",
            logic_type_tags=["低吸"],
            pattern_tags=["均线回踩"],
            market_stage_tag="震荡市",
            environment_tags=["高股息", "防守"],
            decision_context={"strategy_context": {"strategy_line": "dividend_repair"}},
        )

        first = self.app.handle_session_turn(
            "qq:user_a",
            "今天买了600519，1360买的，逻辑还是高股息修复低吸。",
            trade_date="20260411",
        )
        self.assertEqual(first["route"], "applied_from_session")
        self.assertIn("memory_retrieval", first)
        self.assertIn("memory_checklist", first)

        second = self.app.handle_session_turn(
            "qq:user_a",
            "补充：这次还是想按防守仓处理，别追求重仓。",
            trade_date="20260411",
        )
        self.assertEqual(second["route"], "entity_enriched")
        self.assertIn("memory_retrieval", second)

    def test_statement_import_and_memory_rebuild(self) -> None:
        statement_path = self.runtime_root / "statement_rows.csv"
        statement_path.write_text(
            "证券代码,证券名称,成交日期,成交时间,买卖标志,成交价格,成交数量,成交金额,手续费,成交编号\n"
            "603083,剑桥科技,20260410,09:35:00,买入,43.20,100,4320.00,2.10,deal_1\n",
            encoding="utf-8",
        )

        result = self.app.import_statement_file(str(statement_path), trade_date="20260410", session_key="qq:user_a")
        self.assertEqual(result["route"], "statement_import")
        self.assertTrue(result["items"])
        trade_id = result["items"][0]["trade_id"]
        self.assertTrue(trade_id)

        rebuilt = self.app.rebuild_memory()
        self.assertGreaterEqual(rebuilt["rebuild_count"], 1)

        memory_query = self.app.query_memory(ts_code="603083", limit=5)
        self.assertTrue(memory_query["matched_cells"])

    def test_schedule_uses_memory_compaction(self) -> None:
        self.app.log_trade(
            ts_code="603083",
            name="剑桥科技",
            buy_date="20260410",
            buy_price=43.2,
            thesis="回踩参与",
            logic_type_tags=["低吸"],
            pattern_tags=["均线回踩"],
            market_stage_tag="震荡市",
            environment_tags=["修复回流"],
        )
        dry_run = self.app.run_schedule(now="2026-04-10T08:31", dry_run=True)
        kinds = {item["kind"] for item in dry_run["actions"]}
        self.assertIn("memory_compaction", kinds)
        self.assertNotIn("event_fetch", kinds)
        self.assertNotIn("morning_brief", kinds)

    def test_gateway_routes_memory_commands(self) -> None:
        self.app.log_trade(
            ts_code="603083",
            name="剑桥科技",
            buy_date="20260410",
            buy_price=43.2,
            thesis="回踩参与",
            logic_type_tags=["低吸"],
            pattern_tags=["均线回踩"],
            market_stage_tag="震荡市",
            environment_tags=["修复回流"],
        )
        payload = dispatch(
            "记忆 查询 ts_code=603083 market_stage=震荡市 tags=低吸,均线回踩",
            anchor_path=self.skill_root / "scripts" / "finance_journal_gateway.py",
            runtime_root=str(self.runtime_root),
            enable_market_data=False,
        )
        self.assertIn("matched_cells", payload)
        self.assertTrue(payload["matched_cells"])


if __name__ == "__main__":
    unittest.main()
