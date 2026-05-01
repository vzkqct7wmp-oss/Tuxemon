# SPDX-License-Identifier: GPL-3.0
from tuxemon.hermes.scoring import HermesBattleScore


def test_score_rewards_win_and_penalizes_fallbacks():
    score = HermesBattleScore()

    score.record_decision()
    score.record_fallback()
    score.record_illegal_action()
    score.record_hp_events(3)
    score.record_result("won", turns=4)

    assert score.score == 63
    assert "Result: won" in score.report()
