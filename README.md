# Codex Nock

Local-first phone notifications for Codex task completion.

Codex Nock is a tiny CLI that receives a Codex notification event and forwards a privacy-safe alert to your phone or desktop. It starts with one job: let me know when Codex is done, failed, or waiting for approval.

It does not require GitHub, a hosted backend, or any Python dependencies.

## What It Sends

By default, Codex Nock uses `privacy.mode = "minimal"` and sends only:

- status
- project name, if configured
- local time

It does not send prompts, source code, terminal output, or raw Codex event JSON unless you explicitly enable that.

## Supported Channels

- `stdout` for local dry runs
- `desktop` for a full-screen local popup
- `ntfy`
- `Bark`
- `PushDeer`
- `WxPusher`
- Enterprise WeChat group robot (`wecom`)

The simplest zero-account setup is `desktop`: Codex Nock opens a topmost local popup when Codex finishes. The simplest phone setup is usually `ntfy`: install the ntfy app on your phone, subscribe to a private topic, then set that topic locally.

## Install

From this folder:

```powershell
python -m pip install -e .
python -m codex_nock setup-desktop
```

`setup-desktop` creates the Codex Nock config and updates your Codex config with:

```toml
notify = ["python", "-m", "codex_nock", "notify"]
```

If your Codex config already exists, Codex Nock creates a timestamped backup before editing it.

Preview changes without writing files:

```powershell
python -m codex_nock setup-desktop --dry-run
```

On Windows the default config path is:

```text
%APPDATA%\codex-nock\config.toml
```

On macOS/Linux:

```text
~/.config/codex-nock/config.toml
```

## Configure Desktop Popup

The one-command setup above writes this full-screen desktop configuration for you:

```toml
[notify]
provider = "desktop"
project_name = "Codex"

[privacy]
mode = "minimal"

[providers.desktop]
fullscreen = true
auto_close_seconds = 0
```

Then test without sending anything over the network:

```powershell
python -m codex_nock test
```

The popup closes with Enter, Space, or Esc. Set `auto_close_seconds = 10` if you want it to disappear by itself.

## Configure ntfy

Edit the config file:

```toml
[notify]
provider = "ntfy"
project_name = "my-project"

[privacy]
mode = "minimal"

[providers.ntfy]
url = "https://ntfy.sh"
topic_env = "CODEX_NOCK_NTFY_TOPIC"
priority = "default"
```

Set the topic as a local environment variable:

```powershell
[Environment]::SetEnvironmentVariable("CODEX_NOCK_NTFY_TOPIC", "your-private-topic", "User")
```

Open a new terminal and test:

```powershell
python -m codex_nock test
```

Use `--dry-run` to print the notification instead of sending it:

```powershell
python -m codex_nock test --dry-run
```

## Connect Codex

`setup-desktop` handles this automatically. If you prefer to configure Codex manually, add this to the top level of your Codex config, before any `[section]` headers:

```toml
notify = ["python", "-m", "codex_nock", "notify"]
```

Codex Nock accepts event JSON as either a command argument or stdin, so it works with both common hook styles.

## Privacy Modes

```toml
[privacy]
mode = "minimal"
max_body_chars = 500
include_raw_event = false
```

Modes:

- `minimal`: status, project, time only
- `summary`: also includes a short redacted message/title/summary from the event
- `full`: may include raw event JSON only if `include_raw_event = true`

Keep `minimal` unless you are sure your push channel is private enough for your workflow.

## Other Providers

Bark:

```toml
[notify]
provider = "bark"

[providers.bark]
server = "https://api.day.app"
key_env = "CODEX_NOCK_BARK_KEY"
```

PushDeer:

```toml
[notify]
provider = "pushdeer"

[providers.pushdeer]
endpoint = "https://api2.pushdeer.com/message/push"
pushkey_env = "CODEX_NOCK_PUSHDEER_KEY"
```

WxPusher:

```toml
[notify]
provider = "wxpusher"

[providers.wxpusher]
endpoint = "https://wxpusher.zjiecode.com/api/send/message"
app_token_env = "CODEX_NOCK_WXPUSHER_APP_TOKEN"
uids_env = "CODEX_NOCK_WXPUSHER_UIDS"
```

Enterprise WeChat group robot:

```toml
[notify]
provider = "wecom"

[providers.wecom]
webhook_env = "CODEX_NOCK_WECOM_WEBHOOK"
```

Desktop popup:

```toml
[notify]
provider = "desktop"

[providers.desktop]
fullscreen = true
auto_close_seconds = 0
```

## Open Source Notes

This project is intentionally unofficial. Do not use OpenAI names, logos, or branding in a way that suggests endorsement.

Before publishing:

- keep tokens and topics out of commits
- add screenshots only if they do not expose private paths or prompts
- keep approval features separate from notification features
- document any provider-specific privacy tradeoffs

## Development

Run tests:

```powershell
python -m unittest discover
```
