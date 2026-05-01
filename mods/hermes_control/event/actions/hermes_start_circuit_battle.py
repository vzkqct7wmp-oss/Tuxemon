# SPDX-License-Identifier: GPL-3.0
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.combat.combat_context import (
    BattleMode,
    CombatContext,
    CombatType,
)
from tuxemon.combat.utils import check_battle_legal
from tuxemon.entity.npc import NPC
from tuxemon.event.eventaction import EventAction
from tuxemon.monster.monster import Monster
from tuxemon.session import Session

logger = logging.getLogger(__name__)


PLAYER_TEAM = (("rockitten", 18), ("dandylion", 18))
HERMES_TEAM = (("bigfin", 18), ("agnite", 18))


def _spawn_team(team: tuple[tuple[str, int], ...]) -> list[Monster]:
    return [Monster.spawn_base(slug, level) for slug, level in team]


@final
@dataclass
class HermesStartCircuitBattleAction(EventAction):
    """
    Prepare and start the deterministic Hermes Agent Trainer Circuit battle.

    Script usage:
        hermes_start_circuit_battle [opponent_slug]
    """

    name = "hermes_start_circuit_battle"
    opponent_slug: str = "hermes_agent_trainer"

    def start(self, session: Session) -> None:
        player = session.player
        player.game_variables.set("hermes_circuit_started", "yes")
        opponent = session.client.get_npc(self.opponent_slug)
        if opponent is None:
            opponent = NPC.create(session, self.opponent_slug)
            session.client.npc_manager.add_npc_off_map(opponent)

        player.party.replace_party(_spawn_team(PLAYER_TEAM))
        opponent.party.replace_party(_spawn_team(HERMES_TEAM))

        runtime = getattr(session.client, "hermes_runtime", None)
        if runtime is not None:
            runtime.score = runtime.score.__class__()
            runtime.emit(
                "mission.started",
                {
                    "mission": "agent_trainer_circuit",
                    "player_team": list(PLAYER_TEAM),
                    "hermes_team": list(HERMES_TEAM),
                },
            )

        environment = session.client.environment_manager
        if environment.get_active_environment() is None:
            environment.load_environment("stadium")

        if not (check_battle_legal(player) and check_battle_legal(opponent)):
            logger.warning("Hermes circuit battle is not legal")
            self.stop()
            return

        context = CombatContext(
            session=session,
            teams=[player, opponent],
            combat_type=CombatType.TRAINER,
            battle_mode=BattleMode.SINGLE,
        )
        session.client.push_state("CombatState", context=context)

    def update(self, session: Session, dt: float) -> None:
        if "CombatState" not in session.client.active_state_names:
            runtime = getattr(session.client, "hermes_runtime", None)
            if runtime is not None:
                runtime.emit(
                    "mission.completed",
                    {
                        "mission": "agent_trainer_circuit",
                        "report": runtime.score_report(),
                    },
                )
            self.stop()
