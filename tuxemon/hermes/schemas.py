# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import time
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class HermesMonsterSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    name: str
    owner_slug: str | None = None
    instance_id: str | None = None
    level: int | None = None
    hp: int | None = None
    current_hp: int | None = None
    hp_ratio: float | None = None
    status: str | None = None
    techniques: list[str] = Field(default_factory=list)


class HermesLegalAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_id: str
    kind: Literal["technique", "item", "status"]
    user_slug: str | None = None
    user_instance_id: str | None = None
    method_slug: str | None = None
    target_slug: str
    target_instance_id: str | None = None
    description: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class HermesBattleDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    turn: int
    actor_slug: str
    actor_instance_id: str | None = None
    trainer_slug: str | None = None
    objective: str = "win"
    legal_actions: list[HermesLegalAction]
    active_monsters: list[HermesMonsterSnapshot] = Field(default_factory=list)


class HermesBattleDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    action_id: str
    rationale: str | None = None


class HermesTraceEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sequence: int
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)
