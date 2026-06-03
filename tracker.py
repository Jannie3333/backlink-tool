# -*- coding: utf-8 -*-
"""
外链追踪模块
定期检查已提交的网站是否收录了目标产品，发现上线时桌面弹窗通知。
"""
import re
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
import submissions_store as store
from product_manager import load_product

def _get_keywords():
    p = load_product()
    domain = p.get("domain", "")
    name   = p.get("name", "")
    kws = [kw for kw in [domain, name.lower(), name] if kw]
    return kws if kws else ["your-product"]

CHECK_PATHS = [
    "",
    "/tools", "/ai-tools", "/products", "/directory",
    "/tools/image", "/tools/video", "/ai-image", "/ai-video",
    "/category/ai-tools", "/category/image-generation",
    "/category/video-generation",
]


def _notify_desktop(domain: str, live_url: str):
    p = load_product()
    product_name = p.get("domain", "产品")
    title   = "外链上线通知！"
    message = f"{product_name} 已被 {domain} 收录！\n{live_url}"
    try:
        from plyer import notification
        notification.notify(title=title, message=message, app_name="外链工具箱", timeout=15)
    except Exception:
        try:
            import subprocess
            ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms
$n = New-Object System.Windows.Forms.NotifyIcon
$n.Icon = [System.Drawing.SystemIcons]::Information
$n.Visible = $true
$n.ShowBalloonTip(10000, '{title}', '{message}', [System.Windows.Forms.ToolTipIcon]::Info)
Start-Sleep -Seconds 3
$n.Dispose()
"""
            subprocess.Popen(
                ["powershell", "-WindowStyle", "Hidden", "-Command", ps_script],
                creationflags=0x08000000
            )
        except Exception:
            pass


def _check_domain(page, domain: str, log) -> tuple[bool, str]:
    keywords = _get_keywords()
    p = load_product()
    domain_kw = p.get("domain", "").split(".")[0] if p.get("domain") else "your-product"

    for path in CHECK_PATHS:
        url = f"https://{domain}{path}"
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=12000)
            if not resp or resp.status >= 400:
                continue
            time.sleep(1.5)
            content = page.content()
            if any(kw.lower() in content.lower() for kw in keywords):
                links = re.findall(r'href="([^"]*' + re.escape(domain_kw) + r'[^"]*)"', content, re.IGNORECASE)
                live_url = links[0] if links else url
                if not live_url.startswith("http"):
                    live_url = f"https://{domain}{live_url}"
                return True, live_url
        except Exception:
            continue
    return False, ""


def run_check(log_cb=None, check_all: bool = False) -> dict:
    def log(msg):
        if log_cb:
            log_cb(msg)

    if check_all:
        targets = [r for r in store.get_all() if r["status"] != "live"]
    else:
        targets = store.get_pending()

    if not targets:
        log("  没有待检查的域名。")
        return {"total": 0, "new_live": 0, "still_pending": 0}

    log(f"  共 {len(targets)} 个域名待检查...\n")
    stats = {"total": len(targets), "new_live": 0, "still_pending": 0}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ))
        page = ctx.new_page()

        for i, record in enumerate(targets, 1):
            domain = record["domain"]
            log(f"  [{i}/{len(targets)}] 检查 {domain} ...")
            found, live_url = _check_domain(page, domain, log)
            if found:
                store.mark_live(domain, live_url)
                store.mark_notified(domain)
                _notify_desktop(domain, live_url)
                log(f"  ★ 上线！{live_url}")
                stats["new_live"] += 1
            else:
                store.mark_not_found(domain)
                log(f"  - 未收录")
                stats["still_pending"] += 1
            time.sleep(0.5)

        browser.close()

    return stats


def run_auto_loop(interval_hours: float, log_cb=None):
    def log(msg):
        if log_cb:
            log_cb(msg)

    log(f"  自动追踪已启动，每 {interval_hours} 小时检查一次。按 Ctrl+C 停止。\n")
    round_num = 0
    while True:
        round_num += 1
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        log(f"\n  ── 第 {round_num} 轮检查  {ts} ──")
        stats = run_check(log_cb=log_cb, check_all=False)
        log(f"  本轮：新上线 {stats['new_live']} 个 | 仍未收录 {stats['still_pending']} 个")
        log(f"  下次检查：{interval_hours} 小时后。\n")
        try:
            time.sleep(interval_hours * 3600)
        except KeyboardInterrupt:
            log("\n  追踪已停止。")
            break