# -*- coding: utf-8 -*-
"""
外链追踪模块
定期检查已提交的网站是否收录了 Pixocto.ai，发现上线时桌面弹窗通知。
"""
import re
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
import submissions_store as store

# 要搜索的目标关键词（只要页面出现其中任一即视为上线）
TARGET_KEYWORDS = ["pixocto.ai", "pixocto", "Pixocto"]

# 每个域名要检查的路径（首页 + 常见目录页）
CHECK_PATHS = [
    "",
    "/tools", "/ai-tools", "/products", "/directory",
    "/tools/image", "/tools/video", "/ai-image", "/ai-video",
    "/category/ai-tools", "/category/image-generation",
    "/category/video-generation", "/listing/pixocto",
]


# ── 桌面通知 ───────────────────────────────────────────
def _notify_desktop(domain: str, live_url: str):
    """Windows 桌面弹窗通知"""
    title   = "外链上线通知！"
    message = f"pixocto.ai 已被 {domain} 收录！\n{live_url}"
    try:
        from plyer import notification
        notification.notify(
            title=title,
            message=message,
            app_name="外链工具箱",
            timeout=15,
        )
    except Exception:
        # plyer 不可用时，用 PowerShell 发 Toast（Windows 10/11 原生）
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
                creationflags=0x08000000  # CREATE_NO_WINDOW
            )
        except Exception:
            pass  # 静默失败，终端里已经会打印


# ── 检查单个域名 ───────────────────────────────────────
def _check_domain(page, domain: str, log) -> tuple[bool, str]:
    """
    访问域名的多个页面，查找 pixocto.ai 关键词。
    返回 (found: bool, live_url: str)
    """
    for path in CHECK_PATHS:
        url = f"https://{domain}{path}"
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=12000)
            if not resp or resp.status >= 400:
                continue
            time.sleep(1.5)
            content = page.content()
            if any(kw.lower() in content.lower() for kw in TARGET_KEYWORDS):
                # 找出具体的链接
                links = re.findall(r'href="([^"]*pixocto[^"]*)"', content, re.IGNORECASE)
                live_url = links[0] if links else url
                if not live_url.startswith("http"):
                    live_url = f"https://{domain}{live_url}"
                return True, live_url
        except Exception:
            continue
    return False, ""


# ── 运行一轮检查 ───────────────────────────────────────
def run_check(log_cb=None, check_all: bool = False) -> dict:
    """
    检查所有待确认的提交。
    check_all=True 时重新检查全部（含已标记 not_found 的）
    返回统计 dict
    """
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
        ctx     = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
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


# ── 自动循环追踪模式 ───────────────────────────────────
def run_auto_loop(interval_hours: float, log_cb=None):
    """
    每隔 interval_hours 小时检查一次，直到用户按 Ctrl+C。
    """
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
