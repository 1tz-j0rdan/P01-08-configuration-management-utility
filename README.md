# P01-08 — Configuration Management Utility

A dependency-free Python CLI demonstrating layered JSON configuration, validation, environment overrides, and safe edits.

## Features
- Typed defaults with a strict documented schema
- JSON configuration files
- Override precedence: **defaults < file < environment**
- Environment variable names such as `CFG_SERVER__PORT` and `CFG_APP__DEBUG`
- Validate, inspect, retrieve and update individual settings
- File overwrite protection on `init`
- 100% local CLI workflow using Python standard library

## Install (PowerShell)
```powershell
py -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Demo
```powershell
New-Item -ItemType Directory -Force .\demo-files
python -m config_manager init .\demo-files\app.json
python -m config_manager show --file .\demo-files\app.json
python -m config_manager get server.port --file .\demo-files\app.json
python -m config_manager set server.port 9090 --file .\demo-files\app.json
python -m config_manager validate --file .\demo-files\app.json
$env:CFG_SERVER__PORT = "7070"
python -m config_manager get server.port --file .\demo-files\app.json
Remove-Item Env:CFG_SERVER__PORT
python -m config_manager get server.port --file .\demo-files\app.json
```

Expected final two `get` values: `7070`, then `9090`.

`init` refuses to replace an existing file unless `--force` is supplied. `set` intentionally edits the file and will persist the fully resolved configuration; unset environment overrides before editing if you want only file-based values saved.

## Settings
| Key | Type | Default | Rule |
| --- | --- | --- | --- |
| `app.name` | string | `portfolio-app` | Nonempty |
| `app.debug` | boolean | `false` | true/false/yes/no/1/0/on/off |
| `server.host` | string | `127.0.0.1` | Nonempty |
| `server.port` | integer | `8080` | 1–65535 |
| `logging.level` | string | `INFO` | DEBUG/INFO/WARNING/ERROR/CRITICAL |

Only these keys are supported. JSON file values must use the correct JSON types.

## Tests
```powershell
python -m pytest -v
python -m ruff check .
```

## Repository
`.venv/` and `demo-files/` are ignored. The example configuration is not committed; the application defaults are in code.
