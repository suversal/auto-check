# HDHive Auto Checkin

HDHive 自动签到脚本，基于 GitHub Actions 实现每日自动签到，支持多账号和 Telegram 通知。

## 功能特性

- ✅ 每日自动签到
- ✅ 支持多账号
- ✅ Telegram 推送签到结果
- ✅ 本地调试支持
- ✅ 无需服务器，免费使用 GitHub Actions

## 部署步骤

### 1. Fork 本仓库

点击右上角 **Fork** 将本仓库复制到你的账号下。

### 2. 配置 Secrets

进入你的 Fork 仓库 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

添加以下 Secrets：

| Name | Value                                                        | Description                    |
|------|--------------------------------------------------------------|--------------------------------|
| `HD_ACCOUNTS` | `[{"user":"your-email@example.com","pass":"your-password"}]` | 账号信息 JSON 格式，多账号用逗号分隔          |
| `TG_TOKEN` | `xxxxxx:yyyyyyyy`                                            | Telegram Bot Token（可选，不需要通知留空） |
| `TG_CHAT_ID` | `123456789`                                                  | Telegram Chat ID（可选）           |
| `LOGIN_ACTION_ID` | `603b753f736d128b24c8b4f894057aa301eda77339`                 | 登录 Action ID（网站变更时需要更新）        |
| `CHECKIN_ACTION_ID` | `40efbc107064215e9eff178b0466274739ba7d9cb4`                 | 签到 Action ID（网站变更时需要更新）        |
| `GAMBLE_CHECKIN` | `True/False`                                                 | 是否开启赌狗签到，不配置默认False            |

**登录失败时，需要在登录和签到接口中查看ACTION_ID并更新至Secret**

<img width="835" height="389" alt="image" src="https://github.com/user-attachments/assets/7c6f97dc-37db-474f-a06e-267e60a793be" />

**Example `HD_ACCOUNTS` 格式:**
```json
[{"user":"user1@example.com","pass":"password1"},{"user":"user2@example.com","pass":"password2"}]
```

### 3. 启用 GitHub Actions

1. 进入你的仓库 → **Actions**
2. 点击 **I understand my workflows, go ahead and enable them**
3. `HDHive Auto Checkin` workflow 会自动启用

### 4. 测试运行

你可以手动触发一次测试：

1. 进入 **Actions** → 点击 `HDHive Auto Checkin` → 点击 **Run workflow** → **Run workflow**
2. 点击运行中的任务可以查看日志

## 本地测试

如果你想在本地运行测试：

1. 编辑 `checkin_local.py`，在配置区填入你的账号信息和 Telegram 配置
2. 安装依赖：
```bash
pip install requests
```
3. 运行：
```bash
python checkin_local.py
```

> 注意：本地测试如果需要代理，请确保 `PROXIES` 配置正确，并打开注释。

## 运行时间

默认每天北京时间 **06:33** 自动执行一次。

如果你想修改运行时间，编辑 `.github/workflows/checkin.yml` 中的 `cron` 表达式。

## 获取 Telegram Bot Token 和 Chat ID

1. 向 [@BotFather](https://t.me/BotFather) 发送 `/newbot` 创建机器人，获取 Token
2. 向 [@userinfobot](https://t.me/userinfobot) 发送 `/start` 获取你的 Chat ID

## 更新 Action ID

网站更新后 Action ID 可能会变化，如果签到失败，需要重新获取并更新 Secrets：

1. 打开 HDHive 登录页，打开浏览器开发者工具 → Network 标签
2. 尝试登录一次，找到带有 `Next-Action` 请求头的请求，从中获取 `LOGIN_ACTION_ID`
3. 同理在签到页面获取 `CHECKIN_ACTION_ID`
4. 更新仓库 Secrets 中的对应值即可

## 注意事项

- 请不要修改 `checkin.py` 和 `.github/workflows/checkin.yml` 中的环境变量引用部分
- 不要将包含账号密码的 `checkin_local.py` 提交到公共仓库
- GitHub Actions 免费配额足够使用，每天一次完全没问题

## 许可证

MIT License
