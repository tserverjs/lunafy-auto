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
    info = {
        "status_text": "未知",
        "status_emoji": "❓",
        "message": "",
        "deleted_date": "",
        "notice": "",
        "servers_count": "0",
        "need_renew": False,
    }
    html = sb.get_page_source()
    text = sb.get_text("body")

    # 是否需要续期（Renew 按钮是否存在）
    info["need_renew"] = (
        sb.is_element_visible('button:contains("Renew")') or
        'fi-color-danger' in html and 'Renew' in html
    )

    # 状态判断
    if "Expired" in text or "expired" in html.lower():
        info["status_text"] = "已过期 (Expired)"
        info["status_emoji"] = "❌"
    elif "Active" in text:
        info["status_text"] = "正常运行 (Active)"
        info["status_emoji"] = "✅"

    # 提取删除日期，如 24/08 11:53
    m = re.search(r'Server deleted on.*?(\d{2}/\d{2}\s+\d{2}:\d{2})', html)
    if m:
        info["deleted_date"] = m.group(1)

    # 提取状态消息
    if "Your servers have been deleted" in text:
        info["message"] = "服务器已被删除，需续期重建"
    elif "Renew to create a new one" in text:
        info["message"] = "服务器已删除，点击 Renew 重建"

    # 提取 Discord 通知
    if "Discord" in text:
        info["notice"] = "验证后将自动加入 Discord，退出会导致服务器被删除"

    # 提取服务器数量
    m = re.search(r'Your Servers.*?(\d+)', html, re.S)
    if m:
        info["servers_count"] = m.group(1)

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
    # headless=False 配合 xvfb-run 使用，UC GUI 才能正常模拟点击
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

            # 设置窗口大小（确保验证码元素在视口内）
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
                    print(f"  ✅ Cookie 注入: {c.get('name')}")
                except Exception as e:
                    print(f"  ⚠️ Cookie {c.get('name')} 注入失败: {e}")

            # ========== Step 2: 访问 Dashboard ==========
            print("🌐 访问 Dashboard...")
            sb.uc_open_with_tab("https://panel.lunafy.run/")
            time.sleep(3)
            sb.save_screenshot("01_dashboard.png")

            current_url = sb.get_current_url()
            print(f"📍 当前 URL: {current_url}")

            # 检查是否被重定向到登录页（Cookie 失效）
            if "/login" in current_url:
                send_wechat(
                    f"🔐 Lunafy Cookie 已失效\n\n"
                    f"登录状态过期，已被重定向到登录页。\n"
                    f"👉 请重新登录 https://panel.lunafy.run/login 并更新 Secrets 中的 LUNAFY_COOKIES\n\n"
                    f"⏰ {now}"
                )
                return

            # ========== Step 3: 提取当前状态 ==========
            info = extract_info(sb)
            print(f"📊 状态: {info['status_text']}, 需续期: {info['need_renew']}")

            # 如果不需要续期，直接通知
            if not info["need_renew"]:
                msg = (
                    f"✅ Lunafy 服务器状态正常\n\n"
                    f"📊 当前状态：{info['status_emoji']} {info['status_text']}\n"
                    f"📝 详情：{info['message'] or '一切正常，无需操作'}\n"
                    f"🖥️ 服务器数量：{info['servers_count']}\n\n"
                    f"⏰ 检测时间：{now}\n"
                    f"🤖 GitHub Actions + SeleniumBase UC"
                )
                send_wechat(msg)
                return

            # ========== Step 4: 点击 Renew 按钮 ==========
            print("🔄 检测到 Renew 按钮，正在模拟点击...")
            renew_ok = False

            try:
                if sb.is_element_visible('button:contains("Renew")'):
                    sb.click('button:contains("Renew")')
                    renew_ok = True
                    print("  ✅ 通过文本选择器点击 Renew")
                elif sb.is_element_visible(".fi-color-danger"):
                    sb.click(".fi-color-danger")
                    renew_ok = True
                    print("  ✅ 通过 class 选择器点击 Renew")
                else:
                    # JS 兜底点击
                    sb.execute_script('''
                        var btns = document.querySelectorAll("button");
                        for(var i=0;i<btns.length;i++){
                            if(btns[i].innerText.trim()==="Renew"){
                                btns[i].click();
                                return true;
                            }
                        }
                        return false;
                    ''')
                    renew_ok = True
                    print("  ✅ 通过 JS 遍历点击 Renew")
            except Exception as e:
                print(f"❌ 点击 Renew 失败: {e}")

            if not renew_ok:
                send_wechat(f"❌ Lunafy 续期失败\n\n无法点击 Renew 按钮，请检查页面结构。\n\n⏰ {now}")
                return

            time.sleep(2)
            sb.save_screenshot("02_renew_clicked.png")

            # ========== Step 5: 等待 Security Check 弹窗 ==========
            print("⏳ 等待 Security Check 弹窗...")
            popup_appeared = False
            for i in range(10):
                if sb.is_element_visible('text=Security Check') or sb.is_element_visible('text=Verify you are human'):
                    popup_appeared = True
                    print("🎯 Security Check 弹窗已出现")
                    break
                time.sleep(1)

            if not popup_appeared:
                send_wechat(
                    f"⚠️ Lunafy 续期异常\n\n"
                    f"已点击 Renew，但未检测到 Security Check 弹窗。\n"
                    f"👉 请手动检查：https://panel.lunafy.run/\n\n"
                    f"⏰ {now}"
                )
                return

            time.sleep(2)
            sb.save_screenshot("03_popup_visible.png")

            # ========== Step 6: UC 自动过盾 Turnstile ==========
            turnstile_ok = False
            try:
                print("🛡️ 尝试 uc_gui_click_captcha...")
                sb.uc_gui_click_captcha()
                time.sleep(5)
                turnstile_ok = True
                print("✅ uc_gui_click_captcha 执行完毕")
            except Exception as e:
                print(f"⚠️ uc_gui_click_captcha 失败: {e}")
                try:
                    print("🛡️ 尝试 uc_gui_handle_cf...")
                    sb.uc_gui_handle_cf()
                    time.sleep(5)
                    turnstile_ok = True
                    print("✅ uc_gui_handle_cf 执行完毕")
                except Exception as e2:
                    print(f"⚠️ uc_gui_handle_cf 也失败: {e2}")

            time.sleep(3)
            sb.save_screenshot("04_after_turnstile.png")

            # ========== Step 7: 等待续期完成并刷新状态 ==========
            print("⏳ 等待服务器续期响应...")
            time.sleep(5)

            # 刷新页面查看最新状态
            sb.open("https://panel.lunafy.run/")
            time.sleep(3)
            sb.save_screenshot("05_final_status.png")

            info = extract_info(sb)

            # ========== Step 8: 发送结果通知 ==========
            if turnstile_ok and not info["need_renew"]:
                msg = (
                    f"🎉 Lunafy 续期成功！\n\n"
                    f"📊 服务器状态：{info['status_emoji']} {info['status_text']}\n"
                    f"📝 详情：{info['message'] or '续期完成，服务器已恢复'}\n"
                    f"🖥️ 服务器数量：{info['servers_count']}\n\n"
                    f"✅ Turnstile 人机验证已通过\n"
                    f"⏰ 检测时间：{now}\n"
                    f"🤖 GitHub Actions + SeleniumBase UC Mode"
                )
            elif turnstile_ok and info["need_renew"]:
                msg = (
                    f"⚠️ Lunafy 续期结果待确认\n\n"
                    f"📊 服务器状态：{info['status_emoji']} {info['status_text']}\n"
                    f"📝 详情：{info['message']}\n"
                    f"⏰ 删除时间：{info['deleted_date'] or '24/08 11:53'}\n\n"
                    f"🛡️ Turnstile 验证已尝试，但页面仍显示需续期。\n"
                    f"可能原因：IP 被 Cloudflare 标记 / 触发二次验证\n"
                    f"👉 请手动确认：https://panel.lunafy.run/\n\n"
                    f"⏰ {now}"
                )
            else:
                msg = (
                    f"❌ Lunafy 续期失败\n\n"
                    f"📊 服务器状态：{info['status_emoji']} {info['status_text']}\n"
                    f"📝 详情：{info['message']}\n"
                    f"⏰ 删除时间：{info['deleted_date'] or '24/08 11:53'}\n\n"
                    f"🛑 Turnstile 自动验证未成功。\n"
                    f"👉 请手动处理：https://panel.lunafy.run/\n"
                    f"1. 点击 Renew 按钮\n"
                    f"2. 勾选「Verify you are human」\n\n"
                    f"⏰ {now}"
                )

            send_wechat(msg)
            print("✅ 监控流程结束")

    except Exception as e:
        print(f"❌ 脚本异常: {e}")
        send_wechat(f"❌ Lunafy 脚本异常\n\n错误：{str(e)}\n\n⏰ {now}")


if __name__ == "__main__":
    main()
