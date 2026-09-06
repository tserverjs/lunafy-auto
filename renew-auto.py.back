#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import re
import time
from datetime import datetime
from seleniumbase import SB
import requests

# ==================== 配置 ====================
PROXY_SERVER = "socks5://127.0.0.1:40000"
WECHAT_WEBHOOK_KEY = os.getenv("WECHAT_WEBHOOK_KEY")
COOKIES_RAW = os.getenv("LUNAFY_COOKIES", "[]")


# ==================== 企业微信 ====================
def send_wechat(content: str) -> bool:
    if not WECHAT_WEBHOOK_KEY:
        print("⚠️ 未配置 WECHAT_WEBHOOK_KEY")
        return False
    url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={WECHAT_WEBHOOK_KEY}"
    try:
        resp = requests.post(url, json={"msgtype": "text", "text": {"content": content}}, timeout=15)
        result = resp.json()
        print(f"📤 企微响应: {result}")
        return result.get("errcode") == 0
    except Exception as e:
        print(f"❌ 企微发送失败: {e}")
        return False


# ==================== 页面信息提取 ====================
def extract_info(sb) -> dict:
    """
    从 Dashboard 页面提取服务器状态信息
    基于实际页面结构：
      - Server Status: Active / Expired
      - Next renewal: 31/08 13:43
      - Server deleted on: 01/09 13:43
      - Servers 数量
      - 右侧操作按钮状态 (Renew / Unavailable)
    """
    info = {
        "status": "未知",
        "status_emoji": "❓",
        "next_renewal": "未知",
        "deleted_on": "未知",
        "servers_count": "0",
        "action_text": "",       # Renew / Unavailable
        "need_renew": False,
        "notice": "",
    }

    html = sb.get_page_source()
    text = sb.get_text("body")

    print("🔍 开始提取页面信息...")

    # 1. 提取 Server Status（Active / Expired）
    # 匹配 "Server Status: Active" 或 "Server Status: Expired"
    status_match = re.search(r'Server Status:\s*(\w+)', text)
    if status_match:
        raw_status = status_match.group(1).strip()
        info["status"] = raw_status
        if raw_status.lower() == "active":
            info["status_emoji"] = "✅"
            info["need_renew"] = False
        elif raw_status.lower() == "expired":
            info["status_emoji"] = "❌"
            info["need_renew"] = True
        else:
            info["status_emoji"] = "⚠️"
    else:
        # 备用：从 HTML class 判断
        if "fi-color-danger" in html or "Expired" in text:
            info["status"] = "Expired"
            info["status_emoji"] = "❌"
            info["need_renew"] = True
        elif "Active" in text:
            info["status"] = "Active"
            info["status_emoji"] = "✅"
            info["need_renew"] = False

    # 2. 提取 Next renewal 时间，如 "31/08 13:43"
    next_renewal_match = re.search(r'Next renewal\s+(\d{2}/\d{2}\s+\d{2}:\d{2})', text)
    if next_renewal_match:
        info["next_renewal"] = next_renewal_match.group(1).strip()

    # 3. 提取 Server deleted on 时间，如 "01/09 13:43"
    deleted_on_match = re.search(r'Server deleted on\s+(\d{2}/\d{2}\s+\d{2}:\d{2})', text)
    if deleted_on_match:
        info["deleted_on"] = deleted_on_match.group(1).strip()

    # 4. 提取 Servers 数量（右侧卡片 "1"）
    # 匹配 "SERVERS" 附近的数字
    servers_match = re.search(r'SERVERS\s+(\d+)', text)
    if servers_match:
        info["servers_count"] = servers_match.group(1).strip()
    else:
        # 备用：匹配 "Your Servers" 上方的数字
        servers_match2 = re.search(r'Your Servers\s+Active servers\s+(\d+)', text, re.S)
        if servers_match2:
            info["servers_count"] = servers_match2.group(1).strip()

    # 5. 提取右侧操作按钮文本（Renew / Unavailable）
    if sb.is_element_visible('button:contains("Renew")'):
        info["action_text"] = "Renew"
        info["need_renew"] = True
    elif "Unavailable" in text:
        info["action_text"] = "Unavailable"
    elif sb.is_element_visible('button:contains("Unavailable")'):
        info["action_text"] = "Unavailable"

    # 6. 提取 Discord 通知（如果有）
    if "Discord" in text and "deleted" in text:
        info["notice"] = "验证后将自动加入 Discord，退出会导致服务器被删除"

    print(f"📋 提取结果: {info}")
    return info


# ==================== 主流程 ====================
def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 解析 Cookie
    try:
        cookies = json.loads(COOKIES_RAW)
        if not isinstance(cookies, list):
            raise ValueError("LUNAFY_COOKIES 必须是 JSON 数组格式")
    except Exception as e:
        send_wechat(f"❌ Lunafy 监控异常\n\n🍪 Cookie 解析失败：{e}\n\n⏰ {now}")
        return

    # SeleniumBase UC Mode 配置
    sb_kwargs = {
        "uc": True,
        "headless": False,
        "proxy": PROXY_SERVER,
        "locale": "zh-CN",
        "agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    }

    try:
        with SB(**sb_kwargs) as sb:
            print("🚀 SeleniumBase UC Mode 启动成功")

            # 设置窗口大小
            sb.driver.set_window_position(0, 0)
            sb.driver.set_window_size(1920, 1080)

            # ========== Step 1: 注入 Cookie ==========
            print("🍪 正在注入 Cookie...")
            sb.open("https://panel.lunafy.run/login")
            time.sleep(1)

            for c in cookies:
                try:
                    sb.driver.add_cookie({
                        "name": c.get("name", ""),
                        "value": c.get("value", ""),
                        "domain": ".lunafy.run",
                        "path": "/",
                        "secure": True,
                        "httpOnly": c.get("httpOnly", False),
                        "sameSite": "Lax",
                    })
                    print(f"  ✅ Cookie: {c.get('name')}")
                except Exception as e:
                    print(f"  ⚠️ Cookie {c.get('name')} 注入失败: {e}")

            # ========== Step 2: 访问 Dashboard ==========
            print("🌐 访问 Dashboard...")
            sb.uc_open_with_tab("https://panel.lunafy.run/")
            time.sleep(3)
            sb.save_screenshot("01_dashboard.png")

            current_url = sb.get_current_url()
            print(f"📍 当前 URL: {current_url}")

            # Cookie 失效检查
            if "/login" in current_url:
                send_wechat(
                    f"🔐 Lunafy Cookie 已失效\n\n"
                    f"登录状态过期，已被重定向到登录页。\n"
                    f"👉 请重新登录并更新 Secrets 中的 LUNAFY_COOKIES\n\n"
                    f"⏰ {now}"
                )
                return

            # ========== Step 3: 提取状态信息 ==========
            info = extract_info(sb)

            # ========== 分支处理 ==========
            if info["status"].lower() == "active":
                # 🟢 正常运行状态
                msg = (
                    f"✅ Lunafy 服务器状态正常\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 服务器状态：{info['status_emoji']} {info['status']}\n"
                    f"🖥️ 服务器数量：{info['servers_count']} 台\n"
                    f"📅 下次续期：{info['next_renewal']}\n"
                    f"🗑️ 删除时间：{info['deleted_on']}\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"⏰ 检测时间：{now}\n"
                    f"🤖 GitHub Actions 自动监控"
                )
                send_wechat(msg)
                print("✅ 状态正常，已发送通知")
                return

            elif info["status"].lower() == "expired":
                # 🔴 已过期，需要续期
                if info["need_renew"] and info["action_text"] == "Renew":
                    print("🔄 检测到 Renew 按钮，开始续期流程...")

                    # 点击 Renew
                    try:
                        sb.click('button:contains("Renew")')
                        print("  ✅ 已点击 Renew")
                    except Exception as e:
                        print(f"  ❌ 点击 Renew 失败: {e}")
                        send_wechat(
                            f"❌ Lunafy 续期失败\n\n"
                            f"📊 状态：{info['status_emoji']} {info['status']}\n"
                            f"🗑️ 删除时间：{info['deleted_on']}\n"
                            f"❌ 无法点击 Renew 按钮\n\n"
                            f"⏰ {now}"
                        )
                        return

                    time.sleep(2)
                    sb.save_screenshot("02_renew_clicked.png")

                    # 等待 Security Check 弹窗
                    popup_appeared = False
                    for i in range(10):
                        if sb.is_element_visible('text=Security Check') or sb.is_element_visible('text=Verify you are human'):
                            popup_appeared = True
                            break
                        time.sleep(1)

                    if not popup_appeared:
                        send_wechat(
                            f"⚠️ Lunafy 续期异常\n\n"
                            f"已点击 Renew，但未出现 Security Check 弹窗。\n"
                            f"👉 请手动检查：https://panel.lunafy.run/\n\n"
                            f"⏰ {now}"
                        )
                        return

                    time.sleep(2)
                    sb.save_screenshot("03_popup.png")

                    # UC 自动过盾
                    turnstile_ok = False
                    try:
                        sb.uc_gui_click_captcha()
                        time.sleep(5)
                        turnstile_ok = True
                        print("✅ uc_gui_click_captcha 完成")
                    except Exception as e:
                        print(f"⚠️ uc_gui_click_captcha 失败: {e}")
                        try:
                            sb.uc_gui_handle_cf()
                            time.sleep(5)
                            turnstile_ok = True
                            print("✅ uc_gui_handle_cf 完成")
                        except Exception as e2:
                            print(f"⚠️ uc_gui_handle_cf 也失败: {e2}")

                    time.sleep(3)
                    sb.save_screenshot("04_after_turnstile.png")

                    # 刷新查看最新状态
                    sb.open("https://panel.lunafy.run/")
                    time.sleep(3)
                    sb.save_screenshot("05_final.png")
                    info = extract_info(sb)

                    if turnstile_ok and info["status"].lower() == "active":
                        msg = (
                            f"🎉 Lunafy 续期成功！\n\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"📊 服务器状态：{info['status_emoji']} {info['status']}\n"
                            f"🖥️ 服务器数量：{info['servers_count']} 台\n"
                            f"📅 下次续期：{info['next_renewal']}\n"
                            f"🗑️ 删除时间：{info['deleted_on']}\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n\n"
                            f"✅ Turnstile 人机验证已通过\n"
                            f"⏰ {now}"
                        )
                    else:
                        msg = (
                            f"⚠️ Lunafy 续期结果待确认\n\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"📊 服务器状态：{info['status_emoji']} {info['status']}\n"
                            f"🖥️ 服务器数量：{info['servers_count']} 台\n"
                            f"📅 下次续期：{info['next_renewal']}\n"
                            f"🗑️ 删除时间：{info['deleted_on']}\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n\n"
                            f"🛡️ Turnstile 已尝试，但状态未恢复 Active\n"
                            f"👉 请手动确认：https://panel.lunafy.run/\n\n"
                            f"⏰ {now}"
                        )
                    send_wechat(msg)

                else:
                    # 已过期但没有 Renew 按钮（异常情况）
                    msg = (
                        f"❌ Lunafy 状态异常\n\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"📊 服务器状态：{info['status_emoji']} {info['status']}\n"
                        f"🗑️ 删除时间：{info['deleted_on']}\n"
                        f"🖥️ 服务器数量：{info['servers_count']} 台\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"⚠️ 页面显示已过期，但未找到 Renew 按钮\n"
                        f"👉 请手动处理：https://panel.lunafy.run/\n\n"
                        f"⏰ {now}"
                    )
                    send_wechat(msg)

            else:
                # 未知状态
                msg = (
                    f"⚠️ Lunafy 状态未知\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 服务器状态：{info['status_emoji']} {info['status']}\n"
                    f"🖥️ 服务器数量：{info['servers_count']} 台\n"
                    f"📅 下次续期：{info['next_renewal']}\n"
                    f"🗑️ 删除时间：{info['deleted_on']}\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"👉 请手动检查：https://panel.lunafy.run/\n\n"
                    f"⏰ {now}"
                )
                send_wechat(msg)

            print("✅ 监控流程结束")

    except Exception as e:
        print(f"❌ 脚本异常: {e}")
        send_wechat(f"❌ Lunafy 脚本异常\n\n错误：{str(e)}\n\n⏰ {now}")


if __name__ == "__main__":
    main()
