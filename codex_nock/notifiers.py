from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from .events import Notification


class NotifyError(RuntimeError):
    pass


@dataclass(frozen=True)
class SendResult:
    provider: str
    detail: str


def send_notification(
    provider: str,
    provider_config: dict[str, Any],
    notification: Notification,
    timeout_seconds: float,
    dry_run: bool = False,
) -> SendResult:
    provider = provider.lower().strip()
    if dry_run or provider == "stdout":
        print(f"[{notification.title}]\n{notification.body}")
        return SendResult(provider="stdout", detail="printed")
    if provider == "ntfy":
        return send_ntfy(provider_config, notification, timeout_seconds)
    if provider == "bark":
        return send_bark(provider_config, notification, timeout_seconds)
    if provider == "pushdeer":
        return send_pushdeer(provider_config, notification, timeout_seconds)
    if provider == "wxpusher":
        return send_wxpusher(provider_config, notification, timeout_seconds)
    if provider == "wecom":
        return send_wecom(provider_config, notification, timeout_seconds)
    if provider == "desktop":
        return send_desktop(provider_config, notification)
    raise NotifyError(f"Unknown provider: {provider}")


def send_ntfy(config: dict[str, Any], notification: Notification, timeout: float) -> SendResult:
    base_url = str(config.get("url", "https://ntfy.sh")).rstrip("/")
    topic = secret_value(config, "topic", "topic_env")
    if not topic:
        raise NotifyError("ntfy requires topic or topic_env")
    url = f"{base_url}/{urllib.parse.quote(topic.strip('/'))}"
    headers = {
        "Title": notification.title,
        "Priority": str(config.get("priority", "default")),
        "Content-Type": "text/plain; charset=utf-8",
    }
    request(url, data=notification.body.encode("utf-8"), headers=headers, timeout=timeout)
    return SendResult(provider="ntfy", detail="sent")


def send_bark(config: dict[str, Any], notification: Notification, timeout: float) -> SendResult:
    server = str(config.get("server", "https://api.day.app")).rstrip("/")
    key = secret_value(config, "key", "key_env")
    if not key:
        raise NotifyError("bark requires key or key_env")
    title = urllib.parse.quote(notification.title)
    body = urllib.parse.quote(notification.body)
    url = f"{server}/{urllib.parse.quote(key.strip('/'))}/{title}/{body}"
    request(url, timeout=timeout)
    return SendResult(provider="bark", detail="sent")


def send_pushdeer(config: dict[str, Any], notification: Notification, timeout: float) -> SendResult:
    endpoint = str(config.get("endpoint", "https://api2.pushdeer.com/message/push"))
    pushkey = secret_value(config, "pushkey", "pushkey_env")
    if not pushkey:
        raise NotifyError("pushdeer requires pushkey or pushkey_env")
    form = urllib.parse.urlencode(
        {
            "pushkey": pushkey,
            "text": notification.title,
            "desp": notification.body,
            "type": "text",
        }
    ).encode("utf-8")
    request(endpoint, data=form, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=timeout)
    return SendResult(provider="pushdeer", detail="sent")


def send_wxpusher(config: dict[str, Any], notification: Notification, timeout: float) -> SendResult:
    endpoint = str(config.get("endpoint", "https://wxpusher.zjiecode.com/api/send/message"))
    app_token = secret_value(config, "app_token", "app_token_env")
    uids = list_value(config, "uids", "uids_env")
    topic_ids = config.get("topic_ids", [])
    if not app_token:
        raise NotifyError("wxpusher requires app_token or app_token_env")
    if not uids and not topic_ids:
        raise NotifyError("wxpusher requires uids/topic_ids or uids_env")
    payload = {
        "appToken": app_token,
        "content": f"{notification.title}\n\n{notification.body}",
        "summary": notification.title,
        "contentType": int(config.get("content_type", 1)),
        "uids": uids,
        "topicIds": topic_ids,
    }
    request_json(endpoint, payload, timeout)
    return SendResult(provider="wxpusher", detail="sent")


def send_wecom(config: dict[str, Any], notification: Notification, timeout: float) -> SendResult:
    webhook = secret_value(config, "webhook", "webhook_env")
    if not webhook:
        raise NotifyError("wecom requires webhook or webhook_env")
    payload = {
        "msgtype": "text",
        "text": {"content": f"{notification.title}\n{notification.body}"},
    }
    request_json(webhook, payload, timeout)
    return SendResult(provider="wecom", detail="sent")


def send_desktop(config: dict[str, Any], notification: Notification) -> SendResult:
    timeout = int(config.get("auto_close_seconds", 0))
    fullscreen = bool(config.get("fullscreen", True))
    accent = str(config.get("accent", accent_for_status(notification.status)))
    args = [
        sys.executable,
        "-m",
        "codex_nock.popup",
        "--title",
        notification.title,
        "--body",
        notification.body,
        "--accent",
        accent,
        "--timeout",
        str(timeout),
    ]
    if fullscreen:
        args.append("--fullscreen")

    popen_kwargs: dict[str, Any] = {
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "close_fds": True,
    }
    if os.name == "nt":
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    try:
        subprocess.Popen(args, **popen_kwargs)
    except OSError as exc:
        raise NotifyError(f"Could not open desktop popup: {exc}") from exc
    return SendResult(provider="desktop", detail="opened")


def accent_for_status(status: str) -> str:
    if status == "needs-approval":
        return "#f59e0b"
    if status == "failed":
        return "#ef4444"
    return "#12b981"


def secret_value(config: dict[str, Any], value_key: str, env_key: str) -> str:
    env_name = config.get(env_key)
    if env_name:
        value = os.environ.get(str(env_name), "")
        if value:
            return value
    return str(config.get(value_key, "") or "")


def list_value(config: dict[str, Any], value_key: str, env_key: str) -> list[str]:
    value = config.get(value_key)
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    env_name = config.get(env_key)
    if env_name:
        raw = os.environ.get(str(env_name), "")
        return [item.strip() for item in raw.split(",") if item.strip()]
    return []


def request_json(url: str, payload: dict[str, Any], timeout: float) -> bytes:
    return request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=timeout,
    )


def request(url: str, data: bytes | None = None, headers: dict[str, str] | None = None, timeout: float = 10.0) -> bytes:
    req = urllib.request.Request(url, data=data, headers=headers or {}, method="POST" if data is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        raise NotifyError(f"HTTP {exc.code} from provider") from exc
    except urllib.error.URLError as exc:
        raise NotifyError(f"Could not reach provider: {exc.reason}") from exc
