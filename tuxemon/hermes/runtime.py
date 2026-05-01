# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from tuxemon.hermes.encoder import (
    build_battle_decision_request,
    monster_snapshot,
    object_iid,
    object_slug,
)
from tuxemon.hermes.providers import HermesProvider, create_provider
from tuxemon.hermes.scoring import HermesBattleScore
from tuxemon.hermes.trace import JsonlTraceWriter

if TYPE_CHECKING:
    from tuxemon.ai.ai import AI
    from tuxemon.combat.action_queue import EnqueuedAction
    from tuxemon.combat.session import CombatSession
    from tuxemon.config import TuxemonConfig
    from tuxemon.db import OutputBattle
    from tuxemon.entity.npc import NPC
    from tuxemon.monster.monster import Monster
    from tuxemon.platform.events import PlayerInput
    from tuxemon.technique.technique import Technique

logger = logging.getLogger(__name__)


class HermesRuntime:
    def __init__(
        self,
        *,
        enabled: bool,
        provider: HermesProvider,
        trace: JsonlTraceWriter,
        controlled_trainers: list[str],
        strict_validation: bool = True,
    ) -> None:
        self.enabled = enabled
        self.provider = provider
        self.trace = trace
        self.controlled_trainers = controlled_trainers
        self.strict_validation = strict_validation
        self.score = HermesBattleScore()
        self.client: Any | None = None

    @classmethod
    def from_config(cls, config: TuxemonConfig) -> HermesRuntime:
        hermes = config.hermes
        return cls(
            enabled=hermes.enabled,
            provider=create_provider(hermes.provider),
            trace=JsonlTraceWriter(hermes.trace_path, enabled=hermes.enabled),
            controlled_trainers=list(hermes.controlled_trainers),
            strict_validation=hermes.strict_validation,
        )

    def attach_client(self, client: Any) -> None:
        self.client = client
        if not self.enabled:
            return
        client.event_bus.subscribe("PLAYER_INPUT", self.record_input)
        client.event_bus.subscribe(
            "hermes.combat.action_queued", self.record_action_queued
        )
        self.emit(
            "runtime.started",
            {"controlled_trainers": self.controlled_trainers},
        )

    def close(self) -> None:
        if self.client is None or not self.enabled:
            return
        self.client.event_bus.unsubscribe("PLAYER_INPUT", self.record_input)
        self.client.event_bus.unsubscribe(
            "hermes.combat.action_queued", self.record_action_queued
        )

    def emit(self, event_type: str, payload: dict[str, Any]) -> None:
        if self.enabled:
            self.trace.write(event_type, payload)

    def should_control(self, ai: AI) -> bool:
        if not self.enabled:
            return False
        if "*" in self.controlled_trainers:
            return True
        return ai.character.slug in self.controlled_trainers

    def take_turn(self, ai: AI) -> bool:
        if not self.should_control(ai):
            return False

        valid_actions = ai.get_available_moves()
        selected = self.choose_battle_action(ai, valid_actions)
        if selected is None:
            self.score.record_fallback()
            return False

        technique, target, action_id = selected
        ai.action_tech(
            technique,
            target,
            source="hermes",
            metadata={"action_id": action_id},
        )
        return True

    def choose_battle_action(
        self,
        ai: AI,
        valid_actions: list[tuple[Technique, Monster]],
    ) -> tuple[Technique, Monster, str] | None:
        self.score.record_decision()
        request = build_battle_decision_request(
            turn=ai.combat_session.turn,
            actor=ai.monster,
            trainer_slug=ai.character.slug,
            valid_actions=valid_actions,
            active_monsters=ai.combat_session.active_monsters,
        )
        self.emit("battle.decision.request", request.model_dump(mode="json"))

        try:
            decision = self.provider.choose_action(request)
        except Exception as exc:
            logger.warning("Hermes provider failed: %s", exc)
            self.emit(
                "battle.decision.provider_error",
                {"request_id": request.request_id, "error": str(exc)},
            )
            return None

        self.emit("battle.decision.response", decision.model_dump(mode="json"))
        legal = {
            action.action_id: action for action in request.legal_actions
        }
        selected = legal.get(decision.action_id)
        if selected is None:
            self.score.record_illegal_action()
            self.emit(
                "battle.decision.invalid",
                {
                    "request_id": request.request_id,
                    "action_id": decision.action_id,
                },
            )
            return None

        index = int(selected.metadata["index"])
        technique, target = valid_actions[index]
        return technique, target, selected.action_id

    def record_input(self, event: PlayerInput) -> None:
        button = getattr(event, "button", None)
        self.emit(
            "input.player",
            {
                "button": getattr(button, "name", str(button)),
                "pressed": getattr(event, "pressed", False),
                "held": getattr(event, "held", False),
                "released": getattr(event, "released", False),
            },
        )

    def record_action_queued(
        self, action: EnqueuedAction, turn: int
    ) -> None:
        self.emit(
            "battle.action.queued",
            {
                "turn": turn,
                "source": action.source,
                "metadata": action.metadata,
                "user": object_slug(action.user),
                "method": object_slug(action.method),
                "target": object_slug(action.target),
            },
        )

    def snapshot_combat(
        self, combat_session: CombatSession
    ) -> dict[str, dict[str, Any]]:
        snapshot: dict[str, dict[str, Any]] = {}
        for monster in combat_session.active_monsters:
            iid = object_iid(monster)
            if iid is None:
                continue
            snapshot[iid] = monster_snapshot(monster).model_dump(mode="json")
        return snapshot

    def record_action_result(
        self,
        *,
        kind: str,
        user: Any,
        method: Any,
        target: Monster,
        result: Any,
        before: dict[str, dict[str, Any]],
        after: dict[str, dict[str, Any]],
    ) -> None:
        hp_changes = []
        for iid, new_state in after.items():
            old_state = before.get(iid)
            if old_state is None:
                continue
            old_hp = old_state.get("current_hp")
            new_hp = new_state.get("current_hp")
            if old_hp != new_hp:
                hp_changes.append(
                    {
                        "instance_id": iid,
                        "slug": new_state.get("slug"),
                        "old_hp": old_hp,
                        "new_hp": new_hp,
                    }
                )

        self.score.record_hp_events(len(hp_changes))
        self.emit(
            "battle.action.result",
            {
                "kind": kind,
                "user": object_slug(user),
                "method": object_slug(method),
                "target": object_slug(target),
                "success": getattr(result, "success", None),
                "damage": getattr(result, "damage", None),
                "hp_changes": hp_changes,
            },
        )

    def record_battle_result(
        self,
        result_type: OutputBattle,
        player: NPC,
        opponents: list[NPC],
        turns: int,
    ) -> None:
        result = getattr(result_type, "value", str(result_type))
        if player.is_player:
            self.score.record_result(result, turns)
        self.emit(
            "battle.result",
            {
                "result": result,
                "player": player.slug,
                "opponents": [op.slug for op in opponents],
                "turns": turns,
                "score": self.score.score,
            },
        )

    def score_report(self) -> str:
        return self.score.report()
