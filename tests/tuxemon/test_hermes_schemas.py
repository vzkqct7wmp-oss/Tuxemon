# SPDX-License-Identifier: GPL-3.0
import pytest
from pydantic import ValidationError

from tuxemon.hermes.schemas import (
    HermesBattleDecision,
    HermesBattleDecisionRequest,
    HermesLegalAction,
)


def test_decision_request_requires_legal_action_shape():
    action = HermesLegalAction(
        action_id="technique:actor:ram:target",
        kind="technique",
        target_slug="rockitten",
    )

    request = HermesBattleDecisionRequest(
        request_id="request-1",
        turn=1,
        actor_slug="bigfin",
        legal_actions=[action],
    )

    assert request.legal_actions[0].action_id == action.action_id


def test_decision_rejects_extra_fields():
    with pytest.raises(ValidationError):
        HermesBattleDecision(
            request_id="request-1",
            action_id="action-1",
            extra=True,
        )
