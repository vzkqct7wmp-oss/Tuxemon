# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tuxemon.hermes.schemas import HermesTraceEvent


class JsonlTraceWriter:
    def __init__(self, path: str | Path | None, enabled: bool = True) -> None:
        self.path = Path(path) if path else None
        self.enabled = enabled and self.path is not None
        self.sequence = 0

    def write(self, event_type: str, payload: dict[str, Any]) -> None:
        if not self.enabled or self.path is None:
            return

        self.sequence += 1
        event = HermesTraceEvent(
            sequence=self.sequence,
            event_type=event_type,
            payload=payload,
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    event.model_dump(mode="json"),
                    sort_keys=True,
                    default=str,
                )
                + "\n"
            )
