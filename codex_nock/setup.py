from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .config import default_config_path


CODEX_NOTIFY_LINE = 'notify = ["python", "-m", "codex_nock", "notify"]'


@dataclass(frozen=True)
class SetupResult:
    nock_config_path: Path
    codex_config_path: Path
    nock_config_changed: bool
    codex_config_changed: bool
    nock_backup_path: Path | None = None
    codex_backup_path: Path | None = None


def default_codex_config_path() -> Path:
    env_path = os.environ.get("CODEX_CONFIG")
    if env_path:
        return Path(env_path).expanduser()
    return Path.home() / ".codex" / "config.toml"


def desktop_config(project_name: str, fullscreen: bool = True, auto_close_seconds: int = 0) -> str:
    fullscreen_value = "true" if fullscreen else "false"
    return f"""# Codex Nock config.
# This file is safe by default: it does not send prompts, code, or terminal output.

[notify]
provider = "desktop"
project_name = "{escape_toml_string(project_name)}"
timeout_seconds = 10

[privacy]
mode = "minimal"
max_body_chars = 500
include_raw_event = false

[providers.desktop]
fullscreen = {fullscreen_value}
auto_close_seconds = {auto_close_seconds}
"""


def apply_desktop_setup(
    nock_config_path: str | Path | None = None,
    codex_config_path: str | Path | None = None,
    project_name: str = "Codex",
    dry_run: bool = False,
) -> SetupResult:
    nock_path = Path(nock_config_path).expanduser() if nock_config_path else default_config_path()
    codex_path = Path(codex_config_path).expanduser() if codex_config_path else default_codex_config_path()

    nock_changed = not nock_path.exists() or nock_path.read_text(encoding="utf-8") != desktop_config(project_name)
    original_codex = codex_path.read_text(encoding="utf-8") if codex_path.exists() else ""
    updated_codex = upsert_top_level_notify(original_codex)
    codex_changed = updated_codex != original_codex
    nock_backup_path = backup_path_for(nock_path) if nock_changed and nock_path.exists() else None
    backup_path = backup_path_for(codex_path) if codex_changed and codex_path.exists() else None

    if not dry_run:
        if nock_changed:
            nock_path.parent.mkdir(parents=True, exist_ok=True)
            if nock_path.exists() and nock_backup_path:
                shutil.copy2(nock_path, nock_backup_path)
            nock_path.write_text(desktop_config(project_name), encoding="utf-8")
        if codex_changed:
            codex_path.parent.mkdir(parents=True, exist_ok=True)
            if codex_path.exists() and backup_path:
                shutil.copy2(codex_path, backup_path)
            codex_path.write_text(updated_codex, encoding="utf-8")

    return SetupResult(
        nock_config_path=nock_path,
        codex_config_path=codex_path,
        nock_config_changed=nock_changed,
        codex_config_changed=codex_changed,
        nock_backup_path=nock_backup_path,
        codex_backup_path=backup_path,
    )


def upsert_top_level_notify(content: str) -> str:
    lines = content.splitlines()
    newline = "\n"
    first_section = next((idx for idx, line in enumerate(lines) if line.strip().startswith("[")), len(lines))

    for idx in range(first_section):
        stripped = lines[idx].strip()
        if stripped.startswith("notify"):
            if stripped == CODEX_NOTIFY_LINE:
                return ensure_trailing_newline(content)
            lines[idx] = CODEX_NOTIFY_LINE
            return newline.join(lines) + newline

    insert_at = 0
    while insert_at < first_section and is_leading_comment_or_blank(lines[insert_at]):
        insert_at += 1
    lines.insert(insert_at, CODEX_NOTIFY_LINE)
    if insert_at + 1 < len(lines) and lines[insert_at + 1].strip():
        lines.insert(insert_at + 1, "")
    return newline.join(lines) + newline


def backup_path_for(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return path.with_name(f"{path.name}.bak-{stamp}")


def is_leading_comment_or_blank(line: str) -> bool:
    stripped = line.strip()
    return not stripped or stripped.startswith("#")


def ensure_trailing_newline(content: str) -> str:
    return content if content.endswith(("\n", "\r")) else content + "\n"


def escape_toml_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
