# Codex Knock

[English](README.md) | [简体中文](README.zh-CN.md)

Codex 任务完成提醒工具，默认本地优先、隐私最小化。

Codex Knock 是一个很小的命令行工具：它接收 Codex 的通知事件，然后把一条安全、简短的提醒发到你的桌面或手机。第一版只做一件事：Codex 跑完、失败或等待批准时提醒你。

它不是桌面宠物。它是一个极简 Codex 提醒桥：只有在 Codex 跑完、失败或需要你处理时才出现。

它不需要 GitHub、不需要自建后端，也没有任何 Python 第三方依赖。

## 为什么需要它

AI 编程任务一跑起来，很容易变成注意力陷阱。你只是想切屏等一分钟，顺手打开视频、消息或网页，结果 Codex 早就跑完了，你却过了很久才发现。

Codex Knock 就像一个小小的敲门提醒：Codex 工作时它安静待着，等任务完成、失败或需要你处理时，立刻用醒目的桌面弹窗或手机通知把你拉回工作流。

## 效果预览

![Codex Knock 桌面弹窗预览](docs/assets/desktop-popup.svg)

## 当前状态

`v0.1.1` 是一个以桌面弹窗为主的 MVP。

- 默认且已本地验证：满屏 `desktop` 桌面弹窗
- 已实现适配器：`ntfy`、`Bark`、`PushDeer`、`WxPusher`、企业微信机器人 `wecom`
- 暂未包含：自研微信小程序、远程批准、托管后端

其他推送渠道已经有基础接口，适合已经配置好对应服务的早期用户尝试。第一版推荐先使用桌面弹窗。

## 会发送什么

默认情况下，Codex Knock 使用 `privacy.mode = "minimal"`，只发送：

- 状态
- 项目名，如果已配置
- 本地时间

它不会发送 prompt、源代码、终端输出或原始 Codex 事件 JSON，除非你明确开启。

## 支持的提醒渠道

- `stdout`：本地干运行测试
- `desktop`：电脑满屏弹窗
- `ntfy`
- `Bark`
- `PushDeer`
- `WxPusher`
- 企业微信群机器人，配置名为 `wecom`

最简单的零账号方案是 `desktop`：Codex 结束后，电脑上弹出一个置顶满屏提醒。最简单的手机方案通常是 `ntfy`：手机安装 ntfy App，订阅一个私有 topic，然后在本机配置这个 topic。

## 安装

从 GitHub 安装：

```powershell
python -m pip install git+https://github.com/cicih1/Codex-Knock.git
python -m codex_knock setup-desktop
python -m codex_knock test
```

如果你是开发者，想本地修改源码：

```powershell
git clone https://github.com/cicih1/Codex-Knock.git
cd Codex-Knock
python -m pip install -e .
python -m codex_knock setup-desktop
python -m codex_knock test
```

`setup-desktop` 会创建 Codex Knock 配置，并自动把下面这一行写入 Codex 配置：

```toml
notify = ["python", "-m", "codex_knock", "notify"]
```

如果 Codex 配置文件已经存在，Codex Knock 会先创建一个带时间戳的备份，再写入。

只预览、不写入文件：

```powershell
python -m codex_knock setup-desktop --dry-run
```

Windows 上默认配置路径是：

```text
%APPDATA%\codex-knock\config.toml
```

macOS/Linux 上默认配置路径是：

```text
~/.config/codex-knock/config.toml
```

## 配置桌面弹窗

上面的一键配置会自动写入这个满屏桌面弹窗配置：

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

测试弹窗：

```powershell
python -m codex_knock test
```

弹窗可以用 `Enter`、`Space` 或 `Esc` 关闭。如果希望它自动消失，可以设置：

```toml
auto_close_seconds = 10
```

## 配置 ntfy

编辑配置文件：

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

把 topic 放到本机环境变量里：

```powershell
[Environment]::SetEnvironmentVariable("CODEX_NOCK_NTFY_TOPIC", "your-private-topic", "User")
```

打开一个新的终端后测试：

```powershell
python -m codex_knock test
```

如果只想打印提醒内容，不真正发送：

```powershell
python -m codex_knock test --dry-run
```

## 连接 Codex

`setup-desktop` 会自动处理这一步。如果你想手动配置，把下面这一行加到 Codex 配置文件的顶层，也就是任何 `[section]` 标题之前：

```toml
notify = ["python", "-m", "codex_knock", "notify"]
```

Codex Knock 支持从命令参数或 stdin 接收事件 JSON，因此可以兼容常见的 Codex notify/hook 调用方式。

## 隐私模式

```toml
[privacy]
mode = "minimal"
max_body_chars = 500
include_raw_event = false
```

模式说明：

- `minimal`：只发送状态、项目名、时间
- `summary`：额外发送一小段已脱敏的事件标题、消息或摘要
- `full`：只有在 `include_raw_event = true` 时才可能包含原始事件 JSON

除非你非常确定推送渠道足够私密，否则建议保持 `minimal`。

## 其他推送渠道

Bark：

```toml
[notify]
provider = "bark"

[providers.bark]
server = "https://api.day.app"
key_env = "CODEX_NOCK_BARK_KEY"
```

PushDeer：

```toml
[notify]
provider = "pushdeer"

[providers.pushdeer]
endpoint = "https://api2.pushdeer.com/message/push"
pushkey_env = "CODEX_NOCK_PUSHDEER_KEY"
```

WxPusher：

```toml
[notify]
provider = "wxpusher"

[providers.wxpusher]
endpoint = "https://wxpusher.zjiecode.com/api/send/message"
app_token_env = "CODEX_NOCK_WXPUSHER_APP_TOKEN"
uids_env = "CODEX_NOCK_WXPUSHER_UIDS"
```

企业微信群机器人：

```toml
[notify]
provider = "wecom"

[providers.wecom]
webhook_env = "CODEX_NOCK_WECOM_WEBHOOK"
```

桌面弹窗：

```toml
[notify]
provider = "desktop"

[providers.desktop]
fullscreen = true
auto_close_seconds = 0
```

## 开源说明

这个项目是非官方工具。请不要使用 OpenAI 的名称、Logo 或品牌表达来暗示官方背书。

发布前请注意：

- 不要把 token、topic、webhook 提交到仓库
- 截图不要暴露私人路径、prompt 或命令输出
- 提醒功能和远程批准功能应保持分离
- 如果启用第三方推送渠道，需要说明对应的隐私取舍

## 开发

运行测试：

```powershell
python -m unittest discover
```
