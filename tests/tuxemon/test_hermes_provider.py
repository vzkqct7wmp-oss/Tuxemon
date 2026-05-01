# SPDX-License-Identifier: GPL-3.0
from tuxemon.hermes.providers import (
    LocalHeuristicHermesProvider,
    ScriptedHermesProvider,
)
from tuxemon.hermes.schemas import (
    HermesBattleDecisionRequest,
    HermesLegalAction,
)


def test_local_provider_returns_first_legal_action():
    request = HermesBattleDecisionRequest(
        request_id="request-1",
        turn=1,
        actor_slug="rockitten",
        legal_actions=[
            HermesLegalAction(
                action_id="a",
                kind="technique",
                target_slug="bigfin",
            ),
            HermesLegalAction(
                action_id="b",
                kind="technique",
                target_slug="bigfin",
            ),
        ],
    )

    decision = LocalHeuristicHermesProvider().choose_action(request)

    assert decision.action_id == "a"


def test_scripted_provider_returns_next_action_id():
    request = HermesBattleDecisionRequest(
        request_id="request-1",
        turn=1,
        actor_slug="rockitten",
        legal_actions=[],
    )

    decision = ScriptedHermesProvider(["chosen"]).choose_action(request)

    assert decision.request_id == "request-1"
    assert decision.action_id == "chosen"
