# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from pathlib import Path

from tuxemon.constants.asset_loader import fetch_asset, fetch_mod_asset_roots
from tuxemon.constants.paths import mods_folder
from tuxemon.database.config import DatabaseConfig
from tuxemon.database.data import ModData
from tuxemon.database.loader import ModelLoader
from tuxemon.database.registry import validator
from tuxemon.database.utils import load_config
from tuxemon.database.validator import Validator
from tuxemon.db import load_model_map
from tuxemon.locale.locale import T
from tuxemon.user_config import CONFIG


def _infer_mod_tables(config: DatabaseConfig, mod: str) -> list[str]:
    db_path = Path(config.mod_base_path) / mod / config.mod_db_subfolder
    if not db_path.exists():
        return []

    return [
        path.name
        for path in db_path.iterdir()
        if path.is_dir() and path.name in config.model_map
    ]


def _apply_runtime_mods(config: DatabaseConfig) -> None:
    for mod in CONFIG.mods:
        if mod not in config.active_mods:
            config.active_mods.append(mod)
        config.mod_activation[mod] = True
        if mod not in config.mod_tables:
            config.mod_tables[mod] = _infer_mod_tables(config, mod)


def bootstrap_database() -> ModData:
    """
    Fully initialize the Tuxemon database layer.
    """
    T.initialize_translations()
    fetch_mod_asset_roots(CONFIG)
    config_path = fetch_asset(mods_folder.as_posix(), "db_config.yaml")
    config = load_config(config_path)
    _apply_runtime_mods(config)
    model_map = load_model_map(config.model_map)
    loader = ModelLoader(model_map)
    db = ModData(config, loader)
    validator.set(Validator(db))
    return db
