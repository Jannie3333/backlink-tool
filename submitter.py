# -*- coding: utf-8 -*-
"""
外链提交自动化模块
策略：访问目标网站 → 找 Submit 入口 → 自动填表（含 Google 登录）→ 记录结果
"""
import re
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, Page
from config import IMAGES_DIR, GOOGLE_EMAIL, GOOGLE_PASSWORD
from product_manager import load_product

# ── 提交入口关键词 ─────────────────────────────────────
SUBMIT_LINK_TEXTS = [
    "submit", "submit tool", "submit your tool", "add tool", "add your tool",
    "submit a tool", "add a tool", "get listed", "list your tool", "free listing",
    "suggest a tool", "submit product", "add product", "submit ai",
    "submit site", "submit url", "add your website", "add website",
    "add listing", "submit listing", "free submit",
]
SUBMIT_URL_PATTERNS = [
    "/submit", "/add", "/submit-tool", "/add-tool", "/get-listed",
    "/submit-your-tool", "/free-submission", "/list-your-tool",
    "/suggest", "/submit-a-tool", "/add-your-tool",
]

# ── 表单字段映射（每次调用重新加载最新产品信息）─────────
def _field_map() -> dict:
    p = load_product()
    if not p:
        return {}

    social_links = p.get("social_links", [])
    if isinstance(social_links, list):
        social_str = ", ".join(social_links)
    else:
        social_str = str(social_links)

    kw = p.get("keywords", [])
    kw_str = ", ".join(kw) if isinstance(kw, list) else str(kw)

    return {
        # URL / 网址
        "url":           p.get("url", ""),
        "website":       p.get("url", ""),
        "website url":   p.get("url", ""),
        "site url":      p.get("url", ""),
        "homepage":      p.get("url", ""),
        "link":          p.get("url", ""),
        "tool url":      p.get("url", ""),
        "product url":   p.get("url", ""),
        # 名称 / 标题
        "name":          p.get("name", ""),
        "title":         p.get("title", ""),
        "tool name":     p.get("name", ""),
        "product name":  p.get("name", ""),
        "app name":      p.get("name", ""),
        # 描述
        "short description": p.get("short_desc", ""),
        "brief":             p.get("short_desc", ""),
        "summary":           p.get("short_desc", ""),
        "tagline":           p.get("short_desc", ""),
        "description":       p.get("long_desc", ""),
        "about":             p.get("long_desc", ""),
        "long description":  p.get("long_desc", ""),
        "full description":  p.get("long_desc", ""),
        # 联系人
        "email":             p.get("submitter_email", ""),
        "contact email":     p.get("submitter_email", ""),
        "your email":        p.get("submitter_email", ""),
        "your name":         p.get("submitter_name", ""),
        "submitter":         p.get("submitter_name", ""),
        "contact name":      p.get("submitter_name", ""),
        # 关键词 / 标签 / 分类
        "keywords":      kw_str,
        "tags":          p.get("tags", kw_str),
        "tag":           p.get("tags", kw_str),
        "category":      p.get("category", "AI Tools"),
        "type":          p.get("category", "AI Tools"),
        # 社媒
        "twitter":       p.get("social_twitter", ""),
        "x.com":         p.get("social_twitter", ""),
        "social":        social_str,
        "social media":  social_str,
        # 价格
        "pricing":       p.get("price", ""),
        "price":         p.get("price", ""),
        "pricing url":   p.get("pricing_url", ""),
        "pricing page":  p.get("pricing_url", ""),
        # 联盟
        "affiliate":     p.get("affiliate_url", ""),
        "affiliate url": p.get("affiliate_url", ""),
        # 公司
        "company":       p.get("company_name", ""),
        "company name":  p.get("company_name", ""),
        "organization":  p.get("company_name", ""),
        "company address": p.get("company_address", ""),
        "address":       p.get("company_address", ""),
        "phone":         p.get("company_phone", ""),
        "telephone":     p.get("company_phone", ""),
    }


def _best_value_for_label(label: str) -> str:
    label_low = label.lower().strip()
    fm = _field_map()
    if label_low in fm:
        return fm[label_low]
    for key, val in fm.items():
        if key in label_low or label_low in key:
            return val
    return ""


# ── 查找提交入口 ───────────────────────────────────────
def _find_submit_href(page: Page) -> str:
    for a in page.query_selector_all("a"):
        try:
            text     = (a.text_content() or "").lower().strip()
            href     = (a.get_attribute("href") or "")
            href_low = href.lower()
            if any(kw in text for kw in SUBMIT_LINK_TEXTS):
                return href
            if any(pat in href_low for pat in SUBMIT_URL_PATTERNS):
                return href
        except Exception:
            continue
    return ""


def _resolve_href(base_url: str, href: str) -> str:
    if href.startswith("http"):
        return href
    return base_url.rstrip("/") + "/" + href.lstrip("/")


# ── 自动 Google 登录 ───────────────────────────────────
def _auto_google_login(page: Page, log) -> bool:
    try:
        log("   [Google] 正在自动登录...")
        page.wait_for_selector("input[type='email']", timeout=8000)
        email_input = page.query_selector("input[type='email']")
        if email_input:
            email_input.click()
            time.sleep(0.5)
            email_input.fill(GOOGLE_EMAIL)
            time.sleep(0.5)
            next_btn = (
                page.query_selector("#identifierNext button") or
                page.query_selector("button:has-text('Next')") or
                page.query_selector("[jsname='LgbsSe']")
            )
            if next_btn:
                next_btn.click()
            else:
                page.keyboard.press("Enter")
            time.sleep(2)

        page.wait_for_selector("input[type='password']", timeout=8000)
        pwd_input = page.query_selector("input[type='password']")
        if pwd_input:
            pwd_input.click()
            time.sleep(0.5)
            pwd_input.fill(GOOGLE_PASSWORD)
            time.sleep(0.5)
            pwd_btn = (
                page.query_selector("#passwordNext button") or
                page.query_selector("button:has-text('Next')") or
                page.query_selector("[jsname='LgbsSe']")
            )
            if pwd_btn:
                pwd_btn.click()
            else:
                page.keyboard.press("Enter")
            time.sleep(3)

        log("   [Google] 账号密码已填入，等待验证...")
        for _ in range(30):
            time.sleep(1)
            if "accounts.google.com" not in page.url:
                log("   [Google] 登录成功")
                return True
        log("   [Google] 等待超时，可能需要验证码或二次验证")
        return False

    except Exception as e:
        log(f"   [Google] 自动登录出错: {e}")
        return False


# ── 点击"Sign in with Google"按钮 ─────────────────────
def _click_google_signin_button(page: Page, log) -> bool:
    selectors = [
        "button:has-text('Sign in with Google')",
        "a:has-text('Sign in with Google')",
        "[class*='google']",
        "button:has-text('Continue with Google')",
        "a:has-text('Continue with Google')",
        "[data-provider='google']",
        "button:has-text('Google')",
    ]
    for sel in selectors:
        try:
            btn = page.query_selector(sel)
            if btn and btn.is_visible():
                log("   [Google] 发现 Google 登录按钮，点击...")
                with page.context.expect_page(timeout=5000) as popup_info:
                    btn.click()
                popup = popup_info.value
                popup.wait_for_load_state("domcontentloaded")
                _auto_google_login(popup, log)
                time.sleep(3)
                return True
        except Exception:
            try:
                btn = page.query_selector(sel)
                if btn and btn.is_visible():
                    btn.click()
                    time.sleep(2)
                    _auto_google_login(page, log)
                    return True
            except Exception:
                continue
    return False


# ── 从元素周边提取字段标签 ────────────────────────────
def _get_field_hint(page: Page, el) -> str:
    parts = []
    try:
        fid = el.get_attribute("id") or ""
        if fid:
            lbl = page.query_selector(f"label[for='{fid}']")
            if lbl:
                parts.append(lbl.text_content() or "")

        aria = el.get_attribute("aria-label") or ""
        if aria:
            parts.append(aria)
        aria_id = el.get_attribute("aria-labelledby") or ""
        if aria_id:
            lbl_el = page.query_selector(f"#{aria_id}")
            if lbl_el:
                parts.append(lbl_el.text_content() or "")

        parts.append(el.get_attribute("placeholder") or "")
        parts.append(el.get_attribute("name") or "")
        parts.append(fid)
        parts.append(el.get_attribute("data-field") or "")
        parts.append(el.get_attribute("data-label") or "")

        parent_label = el.evaluate("""el => {
            let p = el.parentElement;
            for (let i=0; i<4; i++) {
                if (!p) break;
                if (p.tagName === 'LABEL') return p.innerText || '';
                p = p.parentElement;
            }
            return '';
        }""")
        if parent_label:
            parts.append(str(parent_label))

        prev_sibling_text = el.evaluate("""el => {
            let s = el.previousElementSibling;
            if (s) return s.innerText || s.textContent || '';
            let p = el.parentElement;
            if (p) {
                let ps = p.previousElementSibling;
                if (ps) return ps.innerText || ps.textContent || '';
            }
            return '';
        }""")
        if prev_sibling_text:
            parts.append(str(prev_sibling_text)[:80])

    except Exception:
        pass

    return " ".join(parts).lower()


# ── 填写表单 ───────────────────────────────────────────
def _fill_form(page: Page, log) -> int:
    p = load_product()
    time.sleep(2)

    filled     = 0
    filled_ids = set()

    selectors = [
        "input[type='text']", "input[type='url']", "input[type='email']",
        "input[type='search']", "input:not([type])", "input[type='']",
        "textarea",
    ]
    for selector in selectors:
        for el in page.query_selector_all(selector):
            try:
                if not el.is_visible():
                    continue
                if el.get_attribute("readonly") or el.get_attribute("disabled"):
                    continue
                el_name = (el.get_attribute("name") or "").lower()
                el_id   = (el.get_attribute("id") or "").lower()
                if any(skip in el_name + el_id for skip in
                       ["search","captcha","csrf","token","honeypot","_hp"]):
                    continue

                uid = el_id or el_name or id(el)
                if uid in filled_ids:
                    continue

                hint  = _get_field_hint(page, el)
                value = _best_value_for_label(hint)

                if not value:
                    itype = (el.get_attribute("type") or "").lower()
                    if itype == "url":
                        value = p.get("url", "")
                    elif itype == "email":
                        value = p.get("submitter_email", "")

                if value:
                    el.click()
                    time.sleep(0.2)
                    el.fill(value)
                    filled += 1
                    filled_ids.add(uid)
                    log(f"   填写字段: [{hint[:40]}] = {value[:50]}")

            except Exception:
                continue

    # 下拉框
    for sel in page.query_selector_all("select"):
        try:
            if not sel.is_visible():
                continue
            hint = _get_field_hint(page, sel)
            if any(kw in hint for kw in ["categ","type","topic","genre","niche"]):
                for opt in sel.query_selector_all("option"):
                    txt = (opt.text_content() or "").lower()
                    if any(kw in txt for kw in ["image","video","ai","creative","design","media"]):
                        sel.select_option(value=opt.get_attribute("value") or "")
                        filled += 1
                        log(f"   下拉选择: [{txt}]")
                        break
            elif any(kw in hint for kw in ["pric","plan","tier"]):
                for opt in sel.query_selector_all("option"):
                    txt = (opt.text_content() or "").lower()
                    if any(kw in txt for kw in ["paid","premium","freemium","free"]):
                        sel.select_option(value=opt.get_attribute("value") or "")
                        filled += 1
                        break
        except Exception:
            continue

    # iframe 嵌入表单
    for iframe in page.query_selector_all("iframe"):
        try:
            src = (iframe.get_attribute("src") or "").lower()
            if any(pv in src for pv in ["airtable","google","typeform","jotform"]):
                log(f"   检测到嵌入表单（{src[:40]}），尝试填写...")
                frame = iframe.content_frame()
                if frame:
                    filled += _fill_frame(frame, log)
        except Exception:
            continue

    return filled


def _fill_frame(frame, log) -> int:
    p = load_product()
    filled = 0
    time.sleep(2)
    for selector in ["input[type='text']","input[type='url']",
                     "input[type='email']","textarea"]:
        for el in frame.query_selector_all(selector):
            try:
                if not el.is_visible():
                    continue
                placeholder = (el.get_attribute("placeholder") or "").lower()
                aria_label  = (el.get_attribute("aria-label") or "").lower()
                name        = (el.get_attribute("name") or "").lower()
                hint        = f"{placeholder} {aria_label} {name}"
                value       = _best_value_for_label(hint)
                if not value:
                    if "url" in hint or "website" in hint:
                        value = p.get("url", "")
                    elif "email" in hint:
                        value = p.get("submitter_email", "")
                if value:
                    el.click(); time.sleep(0.2)
                    el.fill(value)
                    filled += 1
                    log(f"   [iframe] 填写: [{hint[:35]}] = {value[:40]}")
            except Exception:
                continue
    return filled


# ── 检测是否有图片上传字段 ─────────────────────────────
def _detect_file_uploads(page: Page) -> bool:
    """检查页面是否存在图片上传 input"""
    for fi in page.query_selector_all("input[type='file']"):
        try:
            if not fi.is_visible():
                continue
            accept = (fi.get_attribute("accept") or "").lower()
            # 无限制 or 明确接受图片
            if not accept or any(x in accept for x in ["image","png","jpg","jpeg","*"]):
                return True
        except Exception:
            continue
    return False


# ── 上传图片 ───────────────────────────────────────────
def _try_upload_image(page: Page, log) -> tuple:
    """
    尝试上传图片到所有可见的 file input。
    返回 (uploaded: bool, note: str)
    """
    # logo.* 优先，其次按名称排序
    candidates = []
    for ext in ["*.png","*.jpg","*.jpeg","*.gif","*.webp"]:
        candidates.extend(IMAGES_DIR.glob(ext))
    # 去重，logo 开头的排最前
    seen = set()
    logos  = []
    others = []
    for img in candidates:
        if img not in seen:
            seen.add(img)
            if img.stem.lower() == "logo":
                logos.append(img)
            else:
                others.append(img)
    images = logos + sorted(others)

    if not images:
        return False, ""

    uploaded_names = []
    img_idx = 0
    for fi in page.query_selector_all("input[type='file']"):
        try:
            if not fi.is_visible():
                continue
            accept = (fi.get_attribute("accept") or "").lower()
            if accept and not any(x in accept for x in ["image","png","jpg","jpeg","*"]):
                continue
            img = images[min(img_idx, len(images) - 1)]
            fi.set_input_files(str(img))
            log(f"   [图片] 已上传: {img.name}")
            uploaded_names.append(img.name)
            img_idx += 1
        except Exception:
            continue

    if uploaded_names:
        return True, "已上传: " + ", ".join(uploaded_names)
    return False, ""


# ── 单个网站提交 ───────────────────────────────────────
def submit_one(domain: str, log, browser_instance=None) -> dict:
    result = {"domain": domain, "status": "unknown", "note": ""}
    try:
        page = browser_instance.new_page()
        page.set_default_timeout(15000)

        base = f"https://{domain}"
        log(f"访问 {base}")
        try:
            page.goto(base, wait_until="domcontentloaded", timeout=15000)
        except Exception as e:
            result.update(status="error", note=f"无法访问: {e}")
            page.close()
            return result

        time.sleep(2)

        # ── 找提交入口 ──────────────────────────────────
        href = _find_submit_href(page)
        if not href:
            for pat in SUBMIT_URL_PATTERNS:
                try:
                    r = page.goto(base + pat, wait_until="domcontentloaded", timeout=8000)
                    if r and r.status == 200:
                        href = base + pat
                        break
                    page.goto(base, wait_until="domcontentloaded", timeout=8000)
                except Exception:
                    continue

        if not href:
            log("   -> 未找到提交入口")
            result.update(status="no_entry", note="未找到 Submit 链接")
            page.close()
            return result

        submit_url = _resolve_href(base, href)
        log(f"   -> 提交页: {submit_url}")
        try:
            page.goto(submit_url, wait_until="domcontentloaded", timeout=15000)
        except Exception as e:
            result.update(status="error", note=f"提交页加载失败: {e}")
            page.close()
            return result
        time.sleep(2)

        # ── 检测并处理登录 ──────────────────────────────
        page_text   = (page.content() or "").lower()
        current_url = page.url

        LOGIN_KEYWORDS = [
            "login required", "please log in", "please sign in",
            "register to submit", "sign in to submit", "login to submit",
            "you must be logged in", "need to login", "need to sign in",
        ]

        if "accounts.google.com" in current_url:
            log("   -> 检测到 Google 登录页，自动登录...")
            ok = _auto_google_login(page, log)
            if not ok:
                result.update(status="login_required",
                              note="Google 自动登录失败，请手动注册/登录后提交")
                page.close()
                return result
            time.sleep(2)

        elif any(kw in page_text for kw in ["sign in with google","continue with google","login with google"]):
            log("   -> 检测到 Google 登录按钮，尝试自动登录...")
            ok = _click_google_signin_button(page, log)
            if not ok:
                result.update(status="login_required",
                              note="需用 Google 登录，自动登录失败，请手动提交")
                page.close()
                return result
            time.sleep(2)

        elif any(kw in page_text for kw in LOGIN_KEYWORDS):
            log("   -> 页面要求登录，尝试 Google 自动登录...")
            ok = _click_google_signin_button(page, log)
            if ok:
                time.sleep(3)
                new_text = (page.content() or "").lower()
                if any(kw in new_text for kw in LOGIN_KEYWORDS):
                    # 还是在登录页
                    result.update(status="login_required",
                                  note="需注册/登录后手动提交")
                    page.close()
                    return result
            else:
                result.update(status="login_required",
                              note="需注册/登录后手动提交")
                page.close()
                return result

        # ── 填写表单 ────────────────────────────────────
        time.sleep(1)
        filled = _fill_form(page, log)
        log(f"   -> 填写了 {filled} 个字段")

        # ── 图片上传 ────────────────────────────────────
        needs_upload = _detect_file_uploads(page)
        img_uploaded, img_note = _try_upload_image(page, log)

        extra_notes = []
        if img_uploaded:
            extra_notes.append(img_note)
        elif needs_upload:
            log("   [!] 该站需要上传图片/Logo，但 images/ 文件夹为空！")
            extra_notes.append("需上传图片(images/文件夹为空)")

        # ── 提交 ────────────────────────────────────────
        submit_btn = None
        for sel in [
            "button[type='submit']", "input[type='submit']",
            "button:has-text('Submit')", "button:has-text('Add Tool')",
            "button:has-text('Send')",  "button:has-text('Publish')",
            "[role='button']:has-text('Submit')",
        ]:
            try:
                btn = page.query_selector(sel)
                if btn and btn.is_visible():
                    submit_btn = btn
                    break
            except Exception:
                continue

        base_note = f"填写 {filled} 项"
        if extra_notes:
            base_note += " | " + " | ".join(extra_notes)

        if submit_btn:
            submit_btn.click()
            time.sleep(3)
            log("   -> 已点击提交按钮")
            result.update(status="success", note=base_note)
        else:
            log(f"   -> 未找到提交按钮（已填写 {filled} 项）")
            result.update(status="success", note=base_note + " (无提交按钮)")

        page.close()

    except Exception as e:
        result.update(status="error", note=str(e)[:80])

    return result


# ── 批量提交 ───────────────────────────────────────────
def run_submissions(domains: list, log_cb=None) -> list:
    def log(msg):
        if log_cb:
            log_cb(msg)

    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--start-maximized"])
        for i, raw in enumerate(domains, 1):
            domain = raw.strip().replace("https://","").replace("http://","").strip("/")
            if not domain:
                continue
            log(f"\n[{i}/{len(domains)}] {domain}")
            res = submit_one(domain, log, browser_instance=browser)
            results.append(res)
            time.sleep(1)
        browser.close()
    return results
