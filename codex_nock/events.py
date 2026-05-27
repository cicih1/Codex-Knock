from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import PrivacyConfig


@dataclass(frozen=True)
class Notification:
    title: str
    body: str
    status: str
    raw_event: dict[str, Any]


def read_event(event_arg: str | None = None) -> dict[str, Any]:
    raw = event_arg
    if raw is None and not sys.stdin.isatty():
        raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {"message": raw}
    return parsed if isinstance(parsed, dict) else {"event": parsed}


def build_notification(event: dict[str, Any], privacy: PrivacyConfig, project_name: str = "") -> Notification:
    status = infer_status(event)
    project = project_name or infer_project(event)
    now = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    title = title_for(status)

    lines = [f"Status: {status}", f"Time: {now}"]
    if project:
        lines.insert(1, f"Project: {project}")

    if privacy.mode.lower() in {"summary", "full"}:
        summary = safe_summary(event)
        if summary:
            lines.append("")
            lines.append(summary)

    if privacy.include_raw_event and privacy.mode.lower() == "full":
        lines.append("")
        lines.append(json.dumps(event, ensure_ascii=False, sort_keys=True))

    body = redact("\n".join(lines), privacy.redact_patterns)
    body = truncate(body, privacy.max_body_chars)
    return Notification(title=title, body=body, status=status, raw_event=event)


def infer_status(event: dict[str, Any]) -> str:
    haystack = " ".join(
        str(value)
        for key, value in flatten(event).items()
        if key.lower() in {"type", "event", "event_name", "hook_event_name", "title", "message", "status"}
    ).lower()
    if any(word in haystack for word in ["permission", "approval", "approve"]):
        return "needs-approval"
    if any(word in haystack for word in ["fail", "failed", "error", "exception"]):
        return "failed"
    if any(word in haystack for word in ["stop", "complete", "completed", "finished", "done"]):
        return "completed"
    return "completed"


def title_for(status: str) -> str:
    if status == "needs-approval":
        return "Codex needs approval"
    if status == "failed":
        return "Codex task failed"
    return "Codex task finished"


def infer_project(event: dict[str, Any]) -> str:
    for key in ("project", "project_name", "repo", "repository", "cwd", "workspace"):
        value = event.get(key)
        if isinstance(value, str) and value.strip():
            if key in {"cwd", "workspace"}:
                return Path(value).name or value
            return value.strip()
    cwd = os.environ.get("CODEX_NOCK_PROJECT") or os.environ.get("PWD")
    return Path(cwd).name if cwd else ""


def safe_summary(event: dict[str, Any]) -> str:
    for key in ("summary", "message", "title", "status"):
        value = event.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    event_type = event.get("type") or event.get("event") or event.get("hook_event_name")
    return f"Event: {event_type}" if event_type else ""


def redact(text: str, patterns: list[str]) -> str:
    result = text
    for pattern in patterns:
        result = re.sub(pattern, "[redacted]", result)
    return result


def truncate(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[: max_chars - 12].rstrip() + "\n[truncated]"


def flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    if not isinstance(value, dict):
        return {prefix: value}
    out: dict[str, Any] = {}
    for key, item in value.items():
        name = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(item, dict):
            out.update(flatten(item, name))
        else:
            out[name] = item
    return out
