# Security Policy

Codex Nock is local-first and privacy-minimal by default. The default desktop setup does not send prompts, source code, terminal output, or raw Codex event JSON over the network.

## Reporting a Vulnerability

Please open a private security advisory on GitHub if the repository supports it. If not, open an issue with a minimal description and avoid posting secrets, tokens, private paths, prompts, or command output.

## Sensitive Data

Do not commit provider tokens, ntfy topics, Bark keys, PushDeer keys, WxPusher app tokens, Enterprise WeChat webhooks, or Codex config files that contain private project paths.

Use environment variables for provider secrets whenever possible.

## Configuration Changes

`codex-nock setup-desktop` updates two local files:

- the Codex Nock config file
- the Codex `config.toml`

If either file already exists and would change, Codex Nock creates a timestamped backup before writing.

## Network Providers

The `desktop` provider is local only. Phone and chat providers such as `ntfy`, `Bark`, `PushDeer`, `WxPusher`, and Enterprise WeChat send notification content to their respective services. Keep `privacy.mode = "minimal"` unless you are comfortable with that provider receiving more detail.
