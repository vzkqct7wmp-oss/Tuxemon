# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from tuxemon.hermes.schemas import (
    HermesBattleDecisionRequest,
    HermesLegalAction,
    HermesMonsterSnapshot,
)

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.technique.technique import Technique


def object_slug(obj: Any) -> str | None:
    value = getattr(obj, "slug", None)
    if value is not None:
        return str(value)
    value = getattr(obj, "name", None)
    return str(value) if value is not None else None


def object_iid(obj: Any) -> str | None:
    value = getattr(obj, "instance_id", None)
    if value is None:
        return None
    return getattr(value, "hex", str(value))


def monster_snapshot(monster: Monster) -> HermesMonsterSnapshot:
    owner = monster.get_owner() if hasattr(monster, "get_owner") else None
    status = getattr(getattr(monster, "status", None), "current_status", None)
    moves = getattr(monster, "moves", None)
    techniques: list[str] = []

    if moves is not None:
        try:
            techniques = [
                slug
                for move in moves.get_moves()
                if (slug := object_slug(move)) is not None
            ]
        except Exception:
            techniques = []

    return HermesMonsterSnapshot(
        slug=object_slug(monster) or "unknown",
        name=str(getattr(monster, "name", object_slug(monster) or "unknown")),
        owner_slug=object_slug(owner),
        instance_id=object_iid(monster),
        level=getattr(monster, "level", None),
        hp=getattr(monster, "hp", None),
        current_hp=getattr(monster, "current_hp", None),
        hp_ratio=getattr(monster, "hp_ratio", None),
        status=object_slug(status),
        techniques=techniques,
    )


def encode_legal_actions(
    actor: Monster,
    valid_actions: Sequence[tuple[Technique, Monster]],
) -> list[HermesLegalAction]:
    encoded: list[HermesLegalAction] = []
    actor_slug = object_slug(actor)
    actor_iid = object_iid(actor)

    for index, (technique, target) in enumerate(valid_actions):
        method_slug = object_slug(technique) or "unknown"
        target_slug = object_slug(target) or "unknown"
        target_iid = object_iid(target)
        action_id = ":".join(
            [
                "technique",
                actor_iid or actor_slug or "actor",
                method_slug,
                target_iid or target_slug,
            ]
        )
        encoded.append(
            HermesLegalAction(
                action_id=action_id,
                kind="technique",
                user_slug=actor_slug,
                user_instance_id=actor_iid,
                method_slug=method_slug,
                target_slug=target_slug,
                target_instance_id=target_iid,
                description=f"{actor_slug} uses {method_slug} on {target_slug}",
                metadata={"index": index},
            )
        )
    return encoded


def build_battle_decision_request(
    *,
    turn: int,
    actor: Monster,
    trainer_slug: str | None,
    valid_actions: Sequence[tuple[Technique, Monster]],
    active_monsters: Sequence[Monster],
) -> HermesBattleDecisionRequest:
    return HermesBattleDecisionRequest(
        request_id=uuid4().hex,
        turn=turn,
        actor_slug=object_slug(actor) or "unknown",
        actor_instance_id=object_iid(actor),
        trainer_slug=trainer_slug,
        legal_actions=encode_legal_actions(actor, valid_actions),
        active_monsters=[
            monster_snapshot(monster) for monster in active_monsters
        ],
    )
