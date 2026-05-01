# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HermesBattleScore:
    decisions: int = 0
    illegal_actions: int = 0
    fallbacks: int = 0
    hp_events: int = 0
    turns: int = 0
    result: str | None = None

    def record_decision(self) -> None:
        self.decisions += 1

    def record_illegal_action(self) -> None:
        self.illegal_actions += 1

    def record_fallback(self) -> None:
        self.fallbacks += 1

    def record_hp_events(self, count: int) -> None:
        self.hp_events += count

    def record_result(self, result: str, turns: int) -> None:
        self.result = result
        self.turns = turns

    @property
    def score(self) -> int:
        base = 100 if self.result == "won" else 25 if self.result else 0
        return max(
            0,
            base
            + self.hp_events * 2
            - self.turns * 2
            - self.illegal_actions * 25
            - self.fallbacks * 10,
        )

    def report_lines(self) -> list[str]:
        return [
            f"Result: {self.result or 'pending'}",
            f"Score: {self.score}",
            f"Turns: {self.turns}",
            f"Decisions: {self.decisions}",
            f"Illegal actions: {self.illegal_actions}",
            f"Fallbacks: {self.fallbacks}",
            f"HP events: {self.hp_events}",
        ]

    def report(self) -> str:
        return "\n".join(self.report_lines())
