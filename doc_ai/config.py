"""Configuration loading utilities for doc_ai.

This module centralizes configuration handling. It loads user-level
configuration files and merges them with project and environment settings.

Order of precedence (last wins):

1. User config file (``~/.config/doc_ai/config.json`` or ``config.yaml``)
2. Project ``.env`` file
3. Environment variables

The resulting values are exposed via the :class:`Settings` object which is
stored on the Typer context (``ctx.obj``) and passed to subcommands.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict
import json
import os

from platformdirs import user_config_path
from dotenv import dotenv_values, find_dotenv
import yaml


def get_user_config_path() -> Path:
    """Return the path to the user configuration file."""

    return user_config_path("doc_ai") / "config.json"


def _read_user_file(path: Path) -> Dict[str, Any]:
    """Read a JSON or YAML file and return its contents as a dict."""

    if not path.exists():
        alt = path.with_suffix(".yaml")
        if alt.exists():
            path = alt
        else:
            alt = path.with_suffix(".yml")
            if alt.exists():
                path = alt
            else:
                return {}
    suffix = path.suffix.lower()
    with path.open("r", encoding="utf-8") as fh:
        if suffix == ".json":
            return json.load(fh) or {}
        if suffix in {".yaml", ".yml"}:
            return yaml.safe_load(fh) or {}
    return {}


def load_user_config() -> Dict[str, Any]:
    """Load configuration from the user's config file."""

    path = get_user_config_path()
    return _read_user_file(path)


def save_user_config(data: Dict[str, Any]) -> None:
    """Persist ``data`` to the user config file in JSON format."""

    path = get_user_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    path.chmod(0o600)


@dataclass
class Settings:
    """Container for configuration values."""

    data: Dict[str, Any] = field(default_factory=dict)
    verbose: bool = False

    def __post_init__(self) -> None:  # pragma: no cover - simple type coercion
        val = self.data.get("VERBOSE", self.data.get("verbose", self.verbose))
        if isinstance(val, str):
            self.verbose = val.lower() in {"1", "true", "yes"}
        else:
            self.verbose = bool(val)

    def __getitem__(self, key: str) -> Any:
        return self.data.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self.data[key] = value


def load_settings(env_file: str | None = None) -> Settings:
    """Return :class:`Settings` merged from user config, .env and environment."""

    cfg: Dict[str, Any] = {}
    cfg.update(load_user_config())
    if env_file is None:
        env_file = find_dotenv(usecwd=True, raise_error_if_not_found=False) or ".env"
    env_path = Path(env_file)
    if env_path.exists():
        cfg.update({k: v for k, v in dotenv_values(env_path).items() if v is not None})
    cfg.update(os.environ)
    return Settings(cfg)

