# -*- coding: utf-8 -*-
"""
外链调研模块：Ahrefs 外链提取 + 联系邮箱查找
"""
import re
import time
from playwright.sync_api import sync_playwright

EMAIL_BLACKLIST = {
    "example", "test", "noreply", "no-reply", "support",
    "sentry", "github", "google", "schema", "w3", "wpcf7",
    "webmaster", "postmaster", "abuse",
}
CONTACT_PATHS = ["/contact", "/contact-us", "/about", "/about-us", "/"]


def _extract_emails(text: str) -> list:
    pattern = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
    results = []
    for e in pattern.findall(text):
        e = e.lower().strip(".")
        local = e.split("@")[0]
        if any(bl in local for bl in EMAIL_BLACKLIST):
            continue
        if len(e) > 80 or "." not in e.split("@")[-1]:
            continue
        if e not in results:
            results.append(e)
    return results


def run_scraper(competitor_url: str, log_cb=None, max_sites: int = 20) -> list:
    """
    完整调研流程：Ahrefs 获取外链 → 逐站查邮箱
    log_cb(str): 进度回调
    返回 list[dict]
    """
    def log(msg):
        if log_cb:
            log_cb(msg)

    target = competitor_url.replace("https://", "").replace("http://", "").strip("/")
    backlinks = []

    with sync_playwright() as p:
        # ── Step 1: Ahrefs（有头，用户可处理验证码）──
        log(f"🌐 正在打开 Ahrefs 查询 **{target}** 的外链...")
        browser = p.chromium.launch(
            headless=False,
            args=["--start-maximized"],
        )
        ctx = browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = ctx.new_page()
        page.goto(
            f"https://ahrefs.com/backlink-checker/?input={target}&mode=subdomains",
            wait_until="domcontentloaded", timeout=30000,
        )

        log("⏳ 等待 Ahrefs 加载（出现验证码请手动通过）...")
        for _ in range(40):
            time.sleep(1)
            if page.query_selector_all("table tbody tr"):
                break

        rows = page.query_selector_all("table tbody tr")
        log(f"✅ 发现 {len(rows)} 条外链")

        for row in rows[:max_sites]:
            cells = row.query_selector_all("td")
            if not cells:
                continue
            try:
                link_el = cells[0].query_selector("a")
                href    = (link_el.get_attribute("href") or "").strip() if link_el else ""
                anchor  = (cells[0].text_content() or "").strip()
                m       = re.match(r"https?://([^/]+)", href)
                domain  = m.group(1) if m else ""
                dr      = (cells[1].text_content() or "").strip() if len(cells) > 1 else ""
                traffic = (cells[2].text_content() or "").strip() if len(cells) > 2 else ""
                if domain:
                    backlinks.append({
                        "referring_domain": domain,
                        "referring_page":   href,
                        "anchor_text":      anchor[:100],
                        "dr":               dr,
                        "traffic":          traffic,
                        "email":            "",
                    })
            except Exception:
                continue

        # 兜底：从页面提取链接
        if not backlinks:
            log("⚠️ 表格为空，从页面文本提取...")
            content = page.content()
            seen = set()
            for href in re.findall(r'href="(https?://[^"]{10,})"', content):
                m = re.match(r"https?://([^/]+)", href)
                if not m:
                    continue
                dom = m.group(1)
                if any(s in dom for s in ["ahrefs.com", "google.", "fonts.", target]):
                    continue
                if dom not in seen:
                    seen.add(dom)
                    backlinks.append({"referring_domain": dom, "referring_page": href,
                                      "anchor_text": "", "dr": "", "traffic": "", "email": ""})
                if len(backlinks) >= max_sites:
                    break

        browser.close()

        if not backlinks:
            log("❌ 未获取到外链，请检查域名或 Ahrefs 是否正常加载。")
            return []

        log(f"\n📋 共 {len(backlinks)} 个外链，开始查找联系邮箱...\n")

        # ── Step 2: 查邮箱（无头）──
        b2  = p.chromium.launch(headless=True)
        c2  = b2.new_context(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ))
        p2  = c2.new_page()

        for i, item in enumerate(backlinks, 1):
            dom = item["referring_domain"]
            log(f"[{i}/{len(backlinks)}] {dom} ...")
            emails_found = []
            for path in CONTACT_PATHS:
                try:
                    r = p2.goto(f"https://{dom}{path}", timeout=10000,
                                wait_until="domcontentloaded")
                    if r and r.status < 400:
                        time.sleep(1.2)
                        emails_found.extend(_extract_emails(p2.content()))
                        if emails_found:
                            break
                except Exception:
                    continue
            seen_e = list(dict.fromkeys(emails_found))
            item["email"] = ", ".join(seen_e[:3])
            suffix = f"✉️ {item['email']}" if item["email"] else "— 未找到"
            log(f"   {suffix}")

        b2.close()

    log("\n✅ 调研完成！")
    return backlinks
