#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0
# ruff: noqa: E402, I001
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from run_tuxemon import apply_config_from_args, parse_args as parse_game_args
from tuxemon.config import TuxemonConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Hermes Agent Trainer Circuit headlessly."
    )
    parser.add_argument(
        "--trace",
        default="hermes_traces/agent_trainer_circuit.validation.jsonl",
        help="JSONL trace path to write.",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=20000,
        help="Maximum fixed-step frames to advance before failing.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1337,
        help="Python random seed for deterministic combat validation.",
    )
    return parser


def build_config(trace_path: Path) -> TuxemonConfig:
    args = parse_game_args(
        [
            "--mod",
            "hermes_control",
            "--skip-titlescreen",
            "--hermes-agent",
            "--hermes-autoplay",
            "--hermes-trace",
            str(trace_path),
        ]
    )
    config = TuxemonConfig(config_path=None)
    apply_config_from_args(config, args)
    config.config_model.display.fps = 1000
    return config


def run_validation(
    trace_path: Path,
    max_frames: int,
    seed: int,
) -> dict[str, Any]:
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    random.seed(seed)

    import tuxemon.user_config as user_config

    trace_path.parent.mkdir(parents=True, exist_ok=True)
    if trace_path.exists():
        trace_path.unlink()

    config = build_config(trace_path)
    user_config.CONFIG = config

    from tuxemon.headless_client import HeadlessClient
    from tuxemon.main import configure_game_states
    from tuxemon.platform import platform
    from tuxemon.prepare import headless_init
    from tuxemon.session import local_session

    platform.init()
    context = headless_init()
    client = HeadlessClient(config, context)
    local_session.set_client(client)

    completed = False
    combat_started = False
    frames = 0
    completion_emitted = False
    try:
        configure_game_states(client, config, None)

        for _ in range(30):
            client.update(1.0 / 60.0)

        client.event_engine.execute_action(
            "hermes_start_circuit_battle",
            ["hermes_agent_trainer"],
            skip=True,
        )
        combat_started = "CombatState" in client.active_state_names

        for frames in range(1, max_frames + 1):
            client.update(1.0 / 60.0)
            if combat_started and "CombatState" not in client.active_state_names:
                completed = True
                runtime = getattr(client, "hermes_runtime", None)
                if runtime is not None:
                    runtime.emit(
                        "mission.completed",
                        {
                            "mission": "agent_trainer_circuit",
                            "report": runtime.score_report(),
                        },
                    )
                    completion_emitted = True
                break

        runtime = getattr(client, "hermes_runtime", None)
        score = runtime.score if runtime is not None else None
        return {
            "completed": completed,
            "combat_started": combat_started,
            "completion_emitted": completion_emitted,
            "frames": frames,
            "seed": seed,
            "active_states": list(client.active_state_names),
            "trace": str(trace_path),
            "result": getattr(score, "result", None),
            "score": getattr(score, "score", 0),
            "turns": getattr(score, "turns", 0),
            "decisions": getattr(score, "decisions", 0),
            "illegal_actions": getattr(score, "illegal_actions", 0),
            "fallbacks": getattr(score, "fallbacks", 0),
            "hp_events": getattr(score, "hp_events", 0),
            "report": runtime.score_report() if runtime is not None else "",
        }
    finally:
        client.perform_cleanup()


def main() -> int:
    args = build_parser().parse_args()
    result = run_validation(Path(args.trace), args.max_frames, args.seed)
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["completed"]:
        return 1
    if result["result"] is None:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
