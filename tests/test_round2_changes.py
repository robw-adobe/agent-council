"""R2 concessions/escalations are consumed, not dropped (2026-06-24).

The 2-round cross-read asks each deliberator for `concessions` and
`escalations`. Previously these were parsed into the payload and thrown away —
the verdict's dissent surface relied entirely on the adjudicator's retelling.
Now they're captured on DeliberatorResult and summarized deterministically
from the deliberators' own words.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))

from agent_council.verdict import DeliberatorResult, summarize_round2_changes  # noqa: E402


def _res(role: str, *, concessions=None, escalations=None) -> DeliberatorResult:
    return DeliberatorResult(
        role=role,
        r2_concessions=concessions or [],
        r2_escalations=escalations or [],
        raw_r1={"score": 4},
        raw_r2={"score": 4},
    )


class Round2ChangesTest(unittest.TestCase):
    def test_no_deltas_returns_empty_string(self) -> None:
        results = {"skeptic": _res("skeptic"), "evidence": _res("evidence")}
        self.assertEqual("", summarize_round2_changes(results))

    def test_concession_is_named_with_role_and_text(self) -> None:
        results = {
            "skeptic": _res("skeptic", concessions=["Evidence's tier framing subsumes my pricing gap."]),
        }
        out = summarize_round2_changes(results)
        self.assertIn("skeptic", out)
        self.assertIn("conceded", out.lower())
        self.assertIn("Evidence's tier framing subsumes my pricing gap.", out)

    def test_escalation_is_named_with_role_and_text(self) -> None:
        results = {
            "voice_identity": _res("voice_identity", escalations=["Hype word is worse than I scored R1."]),
        }
        out = summarize_round2_changes(results)
        self.assertIn("voice_identity", out)
        self.assertIn("escalated", out.lower())
        self.assertIn("Hype word is worse than I scored R1.", out)

    def test_multiple_deliberators_all_surfaced(self) -> None:
        results = {
            "skeptic": _res("skeptic", concessions=["c1"]),
            "voice_identity": _res("voice_identity", escalations=["e1"]),
            "evidence": _res("evidence", concessions=["c2"], escalations=["e2"]),
        }
        out = summarize_round2_changes(results)
        for token in ("c1", "e1", "c2", "e2"):
            self.assertIn(token, out)

    def test_default_fields_are_empty_lists(self) -> None:
        dr = DeliberatorResult(role="skeptic")
        self.assertEqual([], dr.r2_concessions)
        self.assertEqual([], dr.r2_escalations)


if __name__ == "__main__":
    unittest.main()
