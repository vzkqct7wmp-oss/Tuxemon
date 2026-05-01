# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from tuxemon.hermes.schemas import (
    HermesBattleDecision,
    HermesBattleDecisionRequest,
)


class HermesProvider(Protocol):
    def choose_action(
        self, request: HermesBattleDecisionRequest
    ) -> HermesBattleDecision:
        """Return one legal action for the provided decision request."""


class LocalHeuristicHermesProvider:
    """Deterministic local provider used when no external Hermes service runs."""

    def choose_action(
        self, request: HermesBattleDecisionRequest
    ) -> HermesBattleDecision:
        if not request.legal_actions:
            return HermesBattleDecision(
                request_id=request.request_id,
                action_id="",
                rationale="no legal actions",
            )

        return HermesBattleDecision(
            request_id=request.request_id,
            action_id=request.legal_actions[0].action_id,
            rationale="first legal action",
        )


class ScriptedHermesProvider:
    """Test and replay provider that returns preloaded action ids."""

    def __init__(self, action_ids: Iterable[str]) -> None:
        self._action_ids = iter(action_ids)

    def choose_action(
        self, request: HermesBattleDecisionRequest
    ) -> HermesBattleDecision:
        action_id = next(self._action_ids, "")
        return HermesBattleDecision(
            request_id=request.request_id,
            action_id=action_id,
            rationale="scripted",
        )


def create_provider(name: str) -> HermesProvider:
    if name == "scripted":
        return ScriptedHermesProvider([])
    return LocalHeuristicHermesProvider()
