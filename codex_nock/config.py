from __future__ import annotations

import os
import platform
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_REDACT_PATTERNS = [
    r"(?i)(api[_-]?key|token|secret|password|passwd|authorization)\s*[:=]\s*[^\s,;]+",
    r"(?i)bearer\s+[a-z0-9._\-]+",
    r"sk-[a-zA-Z0-9_\-]{16,}",
    r"ghp_[a-zA-Z0-9_]{20,}",
]


@dataclass(frozen=True)
class PrivacyConfig:
    mode: str = "minimal"
    max_body_chars: int = 500
    include_raw_event: bool = False
    redact_patterns: list[str] = field(default_factory=lambda: list(DEFAULT_REDACT_PATTERNS))


@dataclass(frozen=True)
class NotifyConfig:
    provider: str = "stdout"
    project_name: str = ""
    timeout_seconds: float = 10.0


@dataclass(frozen=True)
class AppConfig:
    notify: NotifyConfig = field(default_factory=NotifyConfig)
    privacy: PrivacyConfig = field(default_factory=PrivacyConfig)
    providers: dict[str, dict[str, Any]] = field(default_factory=dict)


def default_config_path() -> Path:
    if platform.system() == "Windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "codex-knock" / "config.toml"
    return Path.home() / ".config" / "codex-knock" / "config.toml"


def legacy_config_path() -> Path:
    if platform.system() == "Windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "codex-nock" / "config.toml"
    return Path.home() / ".config" / "codex-nock" / "config.toml"


def candidate_config_paths() -> list[Path]:
    paths: list[Path] = []
    env_path = os.environ.get("CODEX_NOCK_CONFIG")
    if env_path:
        paths.append(Path(env_path).expanduser())
    paths.append(Path.cwd() / "codex-nock.toml")
    paths.append(Path.cwd() / "codex-knock.toml")
    paths.append(default_config_path())
    paths.append(legacy_config_path())
    paths.append(Path.home() / ".codex-nock.toml")
    paths.append(Path.home() / ".codex-knock.toml")
    return paths


def load_config(path: str | Path | None = None) -> tuple[AppConfig, Path | None]:
    selected = Path(path).expanduser() if path else next((p for p in candidate_config_paths() if p.exists()), None)
    data: dict[str, Any] = {}
    if selected:
        with selected.open("rb") as fh:
            data = tomllib.load(fh)

    notify_data = data.get("notify", {})
    privacy_data = data.get("privacy", {})
    providers_data = data.get("providers", {})

    notify = NotifyConfig(
        provider=str(notify_data.get("provider", os.environ.get("CODEX_NOCK_PROVIDER", "stdout"))),
        project_name=str(notify_data.get("project_name", os.environ.get("CODEX_NOCK_PROJECT", ""))),
        timeout_seconds=float(notify_data.get("timeout_seconds", 10.0)),
    )
    privacy = PrivacyConfig(
        mode=str(privacy_data.get("mode", "minimal")),
        max_body_chars=int(privacy_data.get("max_body_chars", 500)),
        include_raw_event=bool(privacy_data.get("include_raw_event", False)),
        redact_patterns=list(privacy_data.get("redact_patterns", DEFAULT_REDACT_PATTERNS)),
    )
    providers = providers_data if isinstance(providers_data, dict) else {}
    return AppConfig(notify=notify, privacy=privacy, providers=providers), selected


def create_example_config(path: str | Path) -> Path:
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError(f"Config already exists: {target}")
    target.write_text(EXAMPLE_CONFIG, encoding="utf-8")
    return target


EXAMPLE_CONFIG = """# Codex Knock config.
# Keep secrets in environment variables whenever possible.

[notify]
# Start with stdout, then switch to ntfy, bark, pushdeer, wxpusher, or wecom.
provider = "stdout"
project_name = ""
timeout_seconds = 10

[privacy]
# minimal: only status, project, time. summary: also includes short safe event text.
mode = "minimal"
max_body_chars = 500
include_raw_event = false

[providers.ntfy]
url = "https://ntfy.sh"
topic_env = "CODEX_NOCK_NTFY_TOPIC"
# topic = "your-private-topic"
priority = "default"

[providers.bark]
server = "https://api.day.app"
key_env = "CODEX_NOCK_BARK_KEY"

[providers.pushdeer]
endpoint = "https://api2.pushdeer.com/message/push"
pushkey_env = "CODEX_NOCK_PUSHDEER_KEY"

[providers.wxpusher]
endpoint = "https://wxpusher.zjiecode.com/api/send/message"
app_token_env = "CODEX_NOCK_WXPUSHER_APP_TOKEN"
uids_env = "CODEX_NOCK_WXPUSHER_UIDS"
# uids = ["UID_xxx"]
# topic_ids = [123]

[providers.wecom]
webhook_env = "CODEX_NOCK_WECOM_WEBHOOK"

[providers.desktop]
fullscreen = true
# 0 keeps the popup open until Enter, Space, or Esc.
auto_close_seconds = 0
"""
