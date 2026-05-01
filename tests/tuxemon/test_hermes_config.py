# SPDX-License-Identifier: GPL-3.0
from run_tuxemon import apply_config_from_args, parse_args
from tuxemon.config import TuxemonConfig


def test_hermes_cli_args_apply_before_launch_config():
    args = parse_args(
        [
            "--mod",
            "hermes_control",
            "--skip-titlescreen",
            "--hermes-provider",
            "local",
            "--hermes-trace",
            "trace.jsonl",
            "--hermes-autoplay",
        ]
    )
    config = TuxemonConfig(config_path=None)

    apply_config_from_args(config, args)

    assert config.mods == ["tuxemon", "hermes_control"]
    assert config.skip_titlescreen is True
    assert config.splash is False
    assert config.hermes.enabled is True
    assert config.hermes.autoplay is True
    assert config.hermes.provider == "local"
    assert config.hermes.trace_path == "trace.jsonl"
