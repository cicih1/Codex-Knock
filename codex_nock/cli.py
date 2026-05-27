from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .config import create_example_config, default_config_path, load_config
from .events import build_notification, read_event
from .notifiers import NotifyError, send_notification
from .setup import apply_desktop_setup, default_codex_config_path


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = normalize_args(parser, argv)

    if args.command == "init":
        return init_command(args)
    if args.command == "setup-desktop":
        return setup_desktop_command(args)
    if args.command == "test":
        event = {"type": "test", "message": args.message}
        return notify_command(args, event)
    return notify_command(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codex-knock", description="Send phone notifications for Codex events.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    notify = subparsers.add_parser("notify", help="Send a notification from a Codex event JSON payload.")
    add_common_args(notify)
    notify.add_argument("event_json", nargs="?", help="Codex event JSON. If omitted, stdin is used.")

    test = subparsers.add_parser("test", help="Send a test notification.")
    add_common_args(test)
    test.add_argument("--message", default="Codex Knock test notification.", help="Test message body.")

    init = subparsers.add_parser("init", help="Create an example config file.")
    init.add_argument("--path", default=str(default_config_path()), help="Config file path to create.")

    setup_desktop = subparsers.add_parser("setup-desktop", help="Configure Codex Knock and Codex for desktop popups.")
    setup_desktop.add_argument("--config", default=str(default_config_path()), help="Codex Knock config path to write.")
    setup_desktop.add_argument("--codex-config", default=str(default_codex_config_path()), help="Codex config.toml path to update.")
    setup_desktop.add_argument("--project", default="Codex", help="Project name shown in notifications.")
    setup_desktop.add_argument("--dry-run", action="store_true", help="Preview paths and changes without writing files.")
    return parser


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", help="Path to config.toml.")
    parser.add_argument("--provider", help="Override configured provider.")
    parser.add_argument("--project", help="Override configured project name.")
    parser.add_argument("--dry-run", action="store_true", help="Print notification instead of sending.")


def normalize_args(parser: argparse.ArgumentParser, argv: list[str] | None) -> argparse.Namespace:
    raw = list(sys.argv[1:] if argv is None else argv)
    if raw and raw[0] in {"-h", "--help", "--version"}:
        return parser.parse_args(raw)
    if not raw or raw[0].startswith("-") or raw[0].startswith("{"):
        raw.insert(0, "notify")
    return parser.parse_args(raw)


def init_command(args: argparse.Namespace) -> int:
    try:
        path = create_example_config(args.path)
    except FileExistsError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"Created config: {path}")
    return 0


def setup_desktop_command(args: argparse.Namespace) -> int:
    try:
        result = apply_desktop_setup(
            nock_config_path=args.config,
            codex_config_path=args.codex_config,
            project_name=args.project,
            dry_run=args.dry_run,
        )
    except OSError as exc:
        print(f"codex-knock: {exc}", file=sys.stderr)
        return 1

    action = "Would write" if args.dry_run else "Wrote"
    unchanged = "would keep" if args.dry_run else "kept"
    print(f"{action if result.nock_config_changed else unchanged.capitalize()} Codex Knock config: {result.nock_config_path}")
    print(f"{action if result.codex_config_changed else unchanged.capitalize()} Codex config: {result.codex_config_path}")
    if result.nock_backup_path:
        print(f"Codex Knock backup: {result.nock_backup_path}")
    if result.codex_backup_path:
        print(f"Codex backup: {result.codex_backup_path}")
    if args.dry_run:
        print("Dry run only. Re-run without --dry-run to apply.")
    else:
        print("Desktop notifications are configured. Restart Codex to pick up the notify command.")
    return 0


def notify_command(args: argparse.Namespace, event: dict | None = None) -> int:
    try:
        config, config_path = load_config(args.config)
        provider = args.provider or config.notify.provider
        provider_config = config.providers.get(provider, {})
        project = args.project if args.project is not None else config.notify.project_name
        payload = event if event is not None else read_event(getattr(args, "event_json", None))
        notification = build_notification(payload, config.privacy, project)
        result = send_notification(
            provider,
            provider_config,
            notification,
            timeout_seconds=config.notify.timeout_seconds,
            dry_run=args.dry_run,
        )
    except (OSError, ValueError, NotifyError, json.JSONDecodeError) as exc:
        print(f"codex-knock: {exc}", file=sys.stderr)
        return 1

    if args.dry_run or result.provider == "stdout":
        if config_path:
            print(f"\nConfig: {config_path}")
        return 0
    print(f"codex-knock: notification {result.detail} via {result.provider}")
    return 0
