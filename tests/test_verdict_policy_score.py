"""Score-aware VerdictPolicy tests (moderate policy, 2026-06-24).

The calibration `score` is load-bearing in the verdict, not decorative:
  - SHIP   requires 0 hard blocks AND every R2 score >= ship_min_score (3).
  - A score <= soft_block_score (1) is a SOFT BLOCK (counts toward HOLD).
  - A score of 2 blocks SHIP (-> REVISE) but is NOT a soft block.
  - HOLD   on any irreducible OR (hard + soft blocks) >= hold_block_count (3).

Pins the four agreed cases:
  [5,3,4,3,5] 0 blocks -> SHIP
  [5,2,4,4,5] 0 blocks -> REVISE  (one weak)
  [1,4,4,4,4] 0 blocks -> REVISE  (soft block)
  [1,1,1,4,4]          -> HOLD    (3 soft blocks)
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))

from agent_council.verdict import DeliberatorResult, VerdictPolicy  # noqa: E402


def _res(role: str, score: int, *, block: bool = False, irreducible: bool = False) -> DeliberatorResult:
    """A succeeded deliberator with a given R2 score / block flag."""
    return DeliberatorResult(
        role=role,
        r1_score=score,
        r1_would_block=block,
        r2_score=score,
        r2_would_block=block,
        r2_irreducible=irreducible,
        raw_r1={"score": score},
        raw_r2={"score": score},
        error=None,
    )


def _from_scores(scores: list[int], blocks: list[bool] | None = None,
                 irreducibles: list[bool] | None = None) -> dict[str, DeliberatorResult]:
    roles = ["skeptic", "voice_identity", "evidence", "strategy", "adjudicator"]
    blocks = blocks or [False] * len(scores)
    irreducibles = irreducibles or [False] * len(scores)
    return {
        roles[i]: _res(roles[i], scores[i], block=blocks[i], irreducible=irreducibles[i])
        for i in range(len(scores))
    }


class ScoreAwarePolicyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = VerdictPolicy()

    def test_all_scores_at_least_3_no_blocks_ships(self) -> None:
        verdict, _ = self.policy.apply(_from_scores([5, 3, 4, 3, 5]))
        self.assertEqual("SHIP", verdict)

    def test_one_weak_score_2_blocks_ship_yields_revise(self) -> None:
        verdict, _ = self.policy.apply(_from_scores([5, 2, 4, 4, 5]))
        self.assertEqual("REVISE", verdict)

    def test_one_soft_block_score_1_yields_revise(self) -> None:
        verdict, _ = self.policy.apply(_from_scores([1, 4, 4, 4, 4]))
        self.assertEqual("REVISE", verdict)

    def test_three_soft_blocks_score_1_yields_hold(self) -> None:
        verdict, _ = self.policy.apply(_from_scores([1, 1, 1, 4, 4]))
        self.assertEqual("HOLD", verdict)

    def test_irreducible_holds_regardless_of_scores(self) -> None:
        verdict, _ = self.policy.apply(
            _from_scores([5, 5, 5, 5, 5], irreducibles=[True, False, False, False, False])
        )
        self.assertEqual("HOLD", verdict)

    def test_two_hard_blocks_high_scores_yields_revise(self) -> None:
        verdict, _ = self.policy.apply(
            _from_scores([5, 5, 5, 5, 5], blocks=[True, True, False, False, False])
        )
        self.assertEqual("REVISE", verdict)

    def test_two_hard_blocks_plus_one_soft_block_reaches_three_holds(self) -> None:
        # 2 hard blocks (high score) + 1 score-1 soft block = 3 effective blocks
        verdict, _ = self.policy.apply(
            _from_scores([5, 5, 1, 5, 5], blocks=[True, True, False, False, False])
        )
        self.assertEqual("HOLD", verdict)

    def test_missing_scores_fall_back_to_binary_ship(self) -> None:
        # No scores provided -> don't block SHIP on absent calibration data.
        results = _from_scores([3, 3, 3, 3, 3])
        for r in results.values():
            r.r1_score = None
            r.r2_score = None
        verdict, _ = self.policy.apply(results)
        self.assertEqual("SHIP", verdict)


if __name__ == "__main__":
    unittest.main()
