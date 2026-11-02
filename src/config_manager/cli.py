"""Command-line interface for layered configuration."""
import argparse
import json
import sys

from .core import SCHEMA, ConfigError, get_key, load, parse_value, set_key, write_json


def main(argv=None):
    parser = argparse.ArgumentParser(description="Layered JSON configuration manager")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="Write a starter configuration")
    init.add_argument("path")
    init.add_argument("--force", action="store_true")
    for name in ("show", "validate"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--file", default=None)
    get = sub.add_parser("get")
    get.add_argument("key", choices=sorted(SCHEMA))
    get.add_argument("--file", default=None)
    set_cmd = sub.add_parser("set")
    set_cmd.add_argument("key", choices=sorted(SCHEMA))
    set_cmd.add_argument("value")
    set_cmd.add_argument("--file", required=True)
    set_cmd.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            write_json(args.path, load(), overwrite=args.force)
            print(f"Created {args.path}")
        elif args.command == "show":
            print(json.dumps(load(args.file), indent=2))
        elif args.command == "validate":
            load(args.file)
            print("Configuration valid")
        elif args.command == "get":
            print(json.dumps(get_key(load(args.file), args.key)))
        elif args.command == "set":
            data = load(args.file)
            data = set_key(data, args.key, parse_value(args.value, SCHEMA[args.key]))
            write_json(args.file, data, overwrite=True)
            print(f"Updated {args.key} in {args.file}")
    except ConfigError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0
