from __future__ import annotations

import unittest

from finance_journal_core.intake import build_completeness_report, build_polling_bundle, field_has_explicit_value


class IntakeCompletenessTest(unittest.TestCase):
    def test_short_thesis_counts_as_meaningful_when_it_is_not_trade_noise(self) -> None:
        fields = {
            "notes": "[statement-import] | side=买入 | quantity=4300.0 | amount=33455.0 | fee=10.33",
        }
        self.assertTrue(field_has_explicit_value("thesis", "电力老龙", fields=fields))
        self.assertTrue(field_has_explicit_value("thesis", "农产品", fields=fields))

    def test_non_blocking_context_gaps_do_not_block_evolution_readiness(self) -> None:
        fields = {
            "ts_code": "600396.SH",
            "buy_date": "20260326",
            "buy_price": 7.78,
            "sell_date": "20260327",
            "sell_price": 7.96,
            "thesis": "电力老龙",
            "environment_tags": ["电力"],
            "user_focus": [],
            "observed_signals": [],
            "position_reason": "",
            "position_confidence": None,
            "stress_level": None,
            "mistake_tags": [],
            "emotion_notes": "平稳",
            "lessons_learned": "强势票优先做核心。",
            "notes": "[statement-import] | side=买入 | quantity=4300.0 | amount=33455.0 | fee=10.33",
        }

        report = build_completeness_report(fields, "closed_trade")

        self.assertEqual(report["blocking_missing_fields"], [])
        self.assertTrue(report["ready_for_evolution"])
        self.assertTrue(report["needs_follow_up"])
        self.assertCountEqual(
            report["core_missing_fields"],
            ["user_focus", "observed_signals", "position_reason"],
        )

    def test_guided_prompt_uses_numbered_labeled_template(self) -> None:
        fields = {
            "ts_code": "600396.SH",
            "buy_date": "20260326",
            "buy_price": 7.78,
            "sell_date": "20260327",
            "sell_price": 7.96,
            "thesis": "",
            "environment_tags": [],
            "user_focus": [],
            "observed_signals": [],
            "position_reason": "",
            "notes": "",
        }
        bundle = build_polling_bundle(
            fields,
            "closed_trade",
            missing_fields=["thesis"],
            follow_up_questions=["核心逻辑：这笔交易/计划最核心的逻辑是什么？请用一句话概括。"],
            reflection_prompts=[
                {"field": "environment_tags", "question": "市场主题/阶段：当时的市场背景更像哪一种？", "options": ["修复回流"]},
                {"field": "user_focus", "question": "关注对象：你当时主要盯着哪些对象？", "options": ["板块"]},
            ],
        )
        reply_template = ((bundle.get("guided_prompt") or {}).get("reply_template") or "")
        self.assertIn("1. 核心逻辑：", reply_template)
        self.assertIn("2. 关注对象：", reply_template)
        self.assertIn("3. 市场主题/阶段：", reply_template)


if __name__ == "__main__":
    unittest.main()
