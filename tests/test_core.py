import json

import pytest

from config_manager.cli import main
from config_manager.core import (
    DEFAULTS,
    ConfigError,
    get_key,
    load,
    merge,
    parse_value,
    read_json,
    set_key,
    validate,
    write_json,
)


def test_defaults():
    assert load() == DEFAULTS


def test_merge_nested():
    a = {"x": {"a": 1, "b": 2}}
    assert merge(a, {"x": {"a": 3}}) == {"x": {"a": 3, "b": 2}}
    assert a["x"]["a"] == 1


def test_file_override(tmp_path):
    p = tmp_path / "app.json"
    p.write_text('{"server":{"port":9090}}')
    assert load(p)["server"]["port"] == 9090


def test_env_override(tmp_path):
    p = tmp_path / "app.json"
    p.write_text('{"server":{"port":9090}}')
    assert load(p, env={"CFG_SERVER__PORT": "7070"})["server"]["port"] == 7070


def test_env_bool():
    assert load(env={"CFG_APP__DEBUG": "yes"})["app"]["debug"] is True


@pytest.mark.parametrize("raw,expected", [("true", True), ("false", False), ("1", True), ("0", False)])
def test_bool(raw, expected):
    assert parse_value(raw, bool) is expected


@pytest.mark.parametrize("raw", ["maybe", "", "2"])
def test_invalid_bool(raw):
    with pytest.raises(ConfigError):
        parse_value(raw, bool)


@pytest.mark.parametrize("raw", ["1.0", "abc", ""])
def test_invalid_int(raw):
    with pytest.raises(ConfigError):
        parse_value(raw, int)


def test_invalid_port():
    with pytest.raises(ConfigError):
        load(env={"CFG_SERVER__PORT": "70000"})


def test_unknown_key():
    with pytest.raises(ConfigError):
        set_key(DEFAULTS, "app.unknown", "x")


def test_get_key():
    assert get_key(DEFAULTS, "server.port") == 8080


def test_set_key_immutable():
    changed = set_key(DEFAULTS, "server.port", 9090)
    assert get_key(changed, "server.port") == 9090
    assert get_key(DEFAULTS, "server.port") == 8080


def test_invalid_type():
    with pytest.raises(ConfigError):
        validate(merge(DEFAULTS, {"server": {"port": True}}))


def test_unknown_setting():
    with pytest.raises(ConfigError):
        validate(merge(DEFAULTS, {"extra": 3}))


def test_invalid_level():
    with pytest.raises(ConfigError):
        validate(merge(DEFAULTS, {"logging": {"level": "TRACE"}}))


def test_missing_setting():
    with pytest.raises(ConfigError):
        validate({})


def test_bad_json(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{")
    with pytest.raises(ConfigError):
        read_json(p)


def test_nonobject_json(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("[]")
    with pytest.raises(ConfigError):
        read_json(p)


def test_write_and_read(tmp_path):
    p = tmp_path / "app.json"
    write_json(p, DEFAULTS)
    assert read_json(p) == DEFAULTS
    with pytest.raises(ConfigError):
        write_json(p, DEFAULTS)
    write_json(p, DEFAULTS, overwrite=True)


def test_cli_workflow(tmp_path, capsys):
    p = tmp_path / "app.json"
    assert main(["init", str(p)]) == 0
    assert main(["get", "server.port", "--file", str(p)]) == 0
    assert "8080" in capsys.readouterr().out
    assert main(["set", "server.port", "9090", "--file", str(p)]) == 0
    assert json.loads(p.read_text())["server"]["port"] == 9090
    assert main(["validate", "--file", str(p)]) == 0
    assert main(["show", "--file", str(p)]) == 0


def test_cli_refuses_overwrite(tmp_path, capsys):
    p = tmp_path / "app.json"
    assert main(["init", str(p)]) == 0
    assert main(["init", str(p)]) == 1
    assert "File exists" in capsys.readouterr().err


def test_cli_bad_value(tmp_path, capsys):
    p = tmp_path / "app.json"
    assert main(["init", str(p)]) == 0
    assert main(["set", "server.port", "invalid", "--file", str(p)]) == 1
    assert "Invalid integer" in capsys.readouterr().err
