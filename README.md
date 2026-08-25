# 🖥️ Lunafy Server Auto-Renewal

[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-2088FF?logo=github-actions&logoColor=white)](https://github.com/features/actions)
[![SeleniumBase](https://img.shields.io/badge/SeleniumBase-UC%20Mode-success?logo=selenium)](https://seleniumbase.io/)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://www.python.org/)

> 🤖 **全自动监控 + 续期** Lunafy 免费服务器，基于 SeleniumBase UC Mode 自动处理 Cloudflare Turnstile 人机验证，配合企业微信机器人实时推送状态。

---

## ✨ 功能特性

| 功能 | 状态 | 说明 |
|------|:----:|------|
| 🔐 **Cookie 自动登录** | ✅ | 注入 Cookie 绕过手动登录流程 |
| 🛡️ **Turnstile 自动过盾** | ✅ | 基于 SeleniumBase `uc_gui_click_captcha()` 模拟人类轨迹点击 |
| 🔄 **Renew 自动续期** | ✅ | 检测过期状态 → 点击 Renew → 完成验证 → 刷新确认 |
| 📱 **企业微信实时通知** | ✅ | 成功 / 失败 / Cookie 失效 全场景覆盖 |
| 🌐 **GOST 代理隧道** | ✅ | 流量走代理出口，降低 IP 风控概率 |
| 📷 **自动截图存档** | ✅ | 每步操作保留截图至 Artifacts，方便排查 |

---

## 📁 项目结构

```
.
├── .github/
│   └── workflows/
│       └── lunafy-monitor.yml    # GitHub Actions 工作流
├── monitor.py                     # 核心监控续期脚本
└── README.md                      # 本文件
```

---

## 🔐 环境变量配置

在仓库 **Settings → Secrets and variables → Actions → New repository secret** 中添加以下 Secrets：

| Secret 名称 | 必填 | 格式示例 | 说明 |
|------------|:----:|----------|------|
| `GOST_PROXY` | ✅ | `socks5://user:pass@host:port` | GOST 上游代理地址，用于隧道转发 |
| `WECHAT_WEBHOOK_KEY` | ✅ | `693a91f6-7xxx-4bc4-97a0-0ec2sfs60f` | 企业微信机器人 Key |
| `LUNAFY_COOKIES` | ✅ | JSON 数组（见下方） | Cookie Editor 导出的登录态 Cookie |

### 🍪 LUNAFY_COOKIES 格式

在浏览器中安装 [Cookie-Editor](https://cookie-editor.com/) 扩展，登录 `https://panel.lunafy.run/login` 后导出 Cookies，整理为以下 JSON 格式填入 Secret：

```json
[
  {
    "name": "__alt_fp",
    "value": "你的值",
    "httpOnly": false
  },
  {
    "name": "pelican_session",
    "value": "你的值",
    "httpOnly": true
  },
  {
    "name": "remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d",
    "value": "你的值",
    "httpOnly": true
  },
  {
    "name": "XSRF-TOKEN",
    "value": "你的值",
    "httpOnly": false
  }
]
```

> ⚠️ `remember_web_` 后面的哈希值每个人不同，请直接从你的 Cookie Editor 中复制完整名称。

---

## 🚀 快速部署

### 1️⃣ Fork / 创建仓库

将本项目的 `monitor.py` 和 `.github/workflows/lunafy-monitor.yml` 放入你的 GitHub 仓库。

### 2️⃣ 配置 Secrets

按照上方表格配置 `GOST_PROXY`、`WECHAT_WEBHOOK_KEY`、`LUNAFY_COOKIES`。

### 3️⃣ 手动触发测试

进入 **Actions → Lunafy Turnstile 自动续期 → Run workflow**，观察首次运行结果。

### 4️⃣ 查看通知

运行结束后，检查企业微信机器人是否收到状态推送。

---

## ⏰ 定时策略

默认每 **2 小时** 自动运行一次：

```yaml
on:
  schedule:
    - cron: '0 */2 * * *'   # 每 2 小时
  workflow_dispatch:         # 支持手动触发
```

如需调整频率，修改 `.github/workflows/lunafy-monitor.yml` 中的 `cron` 表达式即可。

---

## 📱 企业微信通知示例

### ✅ 续期成功
```
🎉 Lunafy 续期成功！

📊 服务器状态：✅ 正常运行 (Active)
📝 详情：续期完成，服务器已恢复
🖥️ 服务器数量：1

✅ Turnstile 人机验证已通过
⏰ 检测时间：2026-08-25 22:17:00
🤖 GitHub Actions + SeleniumBase UC Mode
```

### ❌ Cookie 失效
```
🔐 Lunafy Cookie 已失效

登录状态过期，已被重定向到登录页。
👉 请重新登录 https://panel.lunafy.run/login 并更新 Secrets 中的 LUNAFY_COOKIES

⏰ 2026-08-25 22:17:00
```

### ⚠️ Turnstile 验证失败（降级通知）
```
❌ Lunafy 续期失败

📊 服务器状态：❌ 已过期 (Expired)
📝 详情：服务器已被删除，需续期重建
⏰ 删除时间：24/08 11:53

🛑 Turnstile 自动验证未成功。
👉 请手动处理：https://panel.lunafy.run/
1. 点击 Renew 按钮
2. 勾选「Verify you are human」

⏰ 2026-08-25 22:17:00
```

---

## 🛠️ 技术栈

- **SeleniumBase** — UC Mode 反检测浏览器自动化
- **GOST** — 安全代理隧道
- **GitHub Actions** — CI/CD 定时任务
- **企业微信机器人** — 实时消息推送
- **xvfb** — 虚拟 X11 显示服务器（供 headed 浏览器渲染）

---

## ⚠️ 注意事项

1. **Cookie 有效期**：`pelican_session` 和 `remember_web_xxx` 有过期时间，失效后需重新从浏览器复制更新。
2. **IP 风控**：GitHub Actions 的数据中心 IP 可能被 Cloudflare 标记，即使使用 UC Mode + 代理也无法 100% 保证通过 Turnstile。脚本已做好**失败降级**，会立即通知你手动处理。
3. **截图调试**：无论成功失败，Actions 都会上传页面截图到 Artifacts，保留 5 天，方便排查问题。
4. **频率限制**：请勿将 cron 设置得过于频繁（如每分钟），避免对 Lunafy 服务器造成压力或触发封禁。

---

## 📷 调试截图说明

每次运行会自动保存以下截图到 Artifacts：

| 文件名 | 说明 |
|--------|------|
| `01_dashboard.png` | 注入 Cookie 后访问 Dashboard 的首屏 |
| `02_renew_clicked.png` | 点击 Renew 按钮后的状态 |
| `03_popup_visible.png` | Security Check 弹窗出现后的画面 |
| `04_after_turnstile.png` | Turnstile 验证尝试后的画面 |
| `05_final_status.png` | 刷新页面后的最终状态 |

---

## 📜 免责声明

本项目仅供学习和技术交流使用。使用者需自行承担因使用本脚本而产生的一切后果，包括但不限于：

- 账号因自动化操作被平台封禁
- Cookie 泄露导致的安全风险
- 服务器数据丢失或服务中断

**请遵守 Lunafy 平台的使用条款，合理使用免费资源。**

---

<div align="center">

Made with ❤️ by GitHub Actions + SeleniumBase

</div>
