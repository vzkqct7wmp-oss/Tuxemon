# SPDX-License-Identifier: GPL-3.0
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session
from tuxemon.tools import open_dialog


@final
@dataclass
class HermesScoreReportAction(EventAction):
    """
    Display the latest Agent Trainer Circuit score report.

    Script usage:
        hermes_score_report
    """

    name = "hermes_score_report"

    def start(self, session: Session) -> None:
        runtime = getattr(session.client, "hermes_runtime", None)
        report = (
            runtime.score_report()
            if runtime is not None
            else "Hermes runtime is not enabled."
        )
        open_dialog(client=session.client, text=report.splitlines())

    def update(self, session: Session, dt: float) -> None:
        if "DialogState" not in session.client.active_state_names:
            self.stop()
