# SPDX-License-Identifier: GPL-3.0
from dataclasses import dataclass

from tuxemon.hermes.runtime import HermesRuntime
from tuxemon.hermes.schemas import HermesBattleDecision
from tuxemon.hermes.trace import JsonlTraceWriter


class InvalidProvider:
    def choose_action(self, request):
        return HermesBattleDecision(
            request_id=request.request_id,
            action_id="not-legal",
        )


class FirstProvider:
    def choose_action(self, request):
        return HermesBattleDecision(
            request_id=request.request_id,
            action_id=request.legal_actions[0].action_id,
        )


@dataclass
class FakeOwner:
    slug: str


class FakeMoves:
    def __init__(self, moves):
        self._moves = moves

    def get_moves(self):
        return self._moves


class FakeMonster:
    def __init__(self, slug, owner=None):
        self.slug = slug
        self.name = slug.title()
        self.instance_id = None
        self.level = 5
        self.hp = 20
        self.current_hp = 20
        self.hp_ratio = 1.0
        self.status = type("Status", (), {"current_status": None})()
        self.moves = FakeMoves([])
        self._owner = owner

    def get_owner(self):
        return self._owner


class FakeCombatSession:
    turn = 2

    def __init__(self, active_monsters):
        self.active_monsters = active_monsters


class FakeAI:
    def __init__(self):
        self.character = FakeOwner("hermes_agent_trainer")
        self.monster = FakeMonster("bigfin", self.character)
        self.technique = type("Technique", (), {"slug": "flood"})()
        self.target = FakeMonster("rockitten", FakeOwner("player"))
        self.combat_session = FakeCombatSession([self.monster, self.target])
        self.actions = []

    def get_available_moves(self):
        return [(self.technique, self.target)]

    def action_tech(self, technique, target, source=None, metadata=None):
        self.actions.append((technique, target, source, metadata))


def make_runtime(provider):
    return HermesRuntime(
        enabled=True,
        provider=provider,
        trace=JsonlTraceWriter(None, enabled=False),
        controlled_trainers=["hermes_agent_trainer"],
    )


def test_runtime_rejects_invalid_provider_action():
    runtime = make_runtime(InvalidProvider())
    ai = FakeAI()

    assert runtime.take_turn(ai) is False
    assert runtime.score.illegal_actions == 1
    assert runtime.score.fallbacks == 1
    assert ai.actions == []


def test_runtime_dispatches_legal_provider_action():
    runtime = make_runtime(FirstProvider())
    ai = FakeAI()

    assert runtime.take_turn(ai) is True

    technique, target, source, metadata = ai.actions[0]
    assert technique is ai.technique
    assert target is ai.target
    assert source == "hermes"
    assert metadata["action_id"].startswith("technique:")
