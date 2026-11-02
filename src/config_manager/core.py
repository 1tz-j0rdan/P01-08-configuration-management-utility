"""Layered JSON configuration with strict validation and environment overrides."""
import json
import os
import re
from pathlib import Path

DEFAULTS = {
    "app": {"name": "portfolio-app", "debug": False},
    "server": {"host": "127.0.0.1", "port": 8080},
    "logging": {"level": "INFO"},
}
SCHEMA = {
    "app.name": str,
    "app.debug": bool,
    "server.host": str,
    "server.port": int,
    "logging.level": str,
}
LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class ConfigError(ValueError):
    """Invalid configuration input."""


def merge(base, override):
    """Recursively merge dictionaries without modifying either input."""
    if not isinstance(base, dict) or not isinstance(override, dict):
        raise ConfigError("Configuration layers must be objects")
    result = {k: merge(v, {}) if isinstance(v, dict) else v for k, v in base.items()}
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = value
    return result


def read_json(path):
    """Read a UTF-8 JSON object from disk."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ConfigError(f"Cannot read configuration {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError("Configuration root must be a JSON object")
    return data


def flatten(data, prefix=""):
    """Yield dotted keys and leaf values."""
    for key, value in data.items():
        name = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            yield from flatten(value, name)
        else:
            yield name, value


def set_key(data, dotted, value):
    """Set an existing dotted configuration key."""
    if dotted not in SCHEMA:
        raise ConfigError(f"Unknown setting: {dotted}")
    result = merge(data, {})
    node = result
    parts = dotted.split(".")
    for part in parts[:-1]:
        if not isinstance(node.get(part), dict):
            raise ConfigError(f"Invalid section: {part}")
        node = node[part]
    node[parts[-1]] = value
    return result


def get_key(data, dotted):
    if dotted not in SCHEMA:
        raise ConfigError(f"Unknown setting: {dotted}")
    node = data
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            raise ConfigError(f"Missing setting: {dotted}")
        node = node[part]
    return node


def parse_value(raw, expected):
    if expected is bool:
        if raw.lower() in {"true", "1", "yes", "on"}:
            return True
        if raw.lower() in {"false", "0", "no", "off"}:
            return False
        raise ConfigError(f"Invalid boolean: {raw}")
    if expected is int:
        if not re.fullmatch(r"[+-]?[0-9]+", raw):
            raise ConfigError(f"Invalid integer: {raw}")
        return int(raw)
    return raw


def validate(data):
    """Reject unknown, missing, incorrectly typed, or out-of-range settings."""
    if not isinstance(data, dict):
        raise ConfigError("Configuration must be an object")
    actual = dict(flatten(data))
    for key in actual.keys() - SCHEMA.keys():
        raise ConfigError(f"Unknown setting: {key}")
    for key, expected in SCHEMA.items():
        if key not in actual:
            raise ConfigError(f"Missing setting: {key}")
        value = actual[key]
        if type(value) is not expected:
            raise ConfigError(f"Wrong type for {key}: expected {expected.__name__}")
    if not 1 <= actual["server.port"] <= 65535:
        raise ConfigError("server.port must be between 1 and 65535")
    if not actual["app.name"].strip() or not actual["server.host"].strip():
        raise ConfigError("Application name and server host must not be empty")
    if actual["logging.level"] not in LEVELS:
        raise ConfigError("logging.level must be DEBUG, INFO, WARNING, ERROR, or CRITICAL")
    return data


def load(path=None, env=None, prefix="CFG_"):
    """Load defaults < JSON file < environment variables."""
    config = merge(DEFAULTS, read_json(path) if path is not None else {})
    source = os.environ if env is None else env
    for dotted, expected in SCHEMA.items():
        env_name = prefix + dotted.replace(".", "__").upper()
        if env_name in source:
            config = set_key(config, dotted, parse_value(source[env_name], expected))
    return validate(config)


def write_json(path, data, overwrite=False):
    """Write a JSON config, refusing to overwrite unless explicitly allowed."""
    validate(data)
    target = Path(path)
    if target.exists() and not overwrite:
        raise ConfigError(f"File exists (use --force): {target}")
    try:
        target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"Cannot write {target}: {exc}") from exc
