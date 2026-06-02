# -*- coding: utf-8 -*-
"""
产品信息管理模块
支持新增/编辑产品配置，存储为 JSON 文件
"""
import json
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "output" / "product.json"
IMAGES_DIR  = Path(__file__).parent / "images"

# (key, 显示名称, 必填, 提示文字)
FIELDS = [
    ("name",            "产品名称",         True,  "如：Pixocto.ai"),
    ("domain",          "产品域名",         True,  "如：pixocto.ai（不含 http://）"),
    ("price",           "价格",             True,  "如：$1/Mo 或 Free"),
    ("pricing_url",     "Pricing 页面地址", True,  "如：https://pixocto.ai/pricing"),
    ("title",           "产品标题",         True,  "如：Pixocto · All-In-One Creative Platform"),
    ("short_desc",      "短描述",           True,  "100 字以内，适合 tagline / summary"),
    ("long_desc",       "长描述",           True,  "200 字以上，适合 About / Description"),
    ("keywords",        "关键词",           True,  "逗号分隔，如：AI image generator, text to video"),
    ("submitter_name",  "提交人姓名",       True,  "如：Jannie Monroe"),
    ("submitter_email", "提交邮箱",         True,  "如：contact@pixocto.ai"),
    ("social_links",    "社媒链接",         True,  "逗号分隔，如：https://x.com/pixocto"),
    ("affiliate_url",   "联盟计划网址",     False, "没有直接按 Enter 跳过"),
    ("company_name",    "公司名称",         True,  "如：LUCKY DAYS CO LTD"),
    ("company_address", "公司地址",         True,  "如：100 N HOWARD ST STE R, SPOKANE, WA 99201"),
    ("company_phone",   "公司电话",         True,  "如：+1 302 3630 580"),
]


# ── 加载 / 保存 ────────────────────────────────────────
def load_product() -> dict:
    CONFIG_FILE.parent.mkdir(exist_ok=True)
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_product(data: dict):
    CONFIG_FILE.parent.mkdir(exist_ok=True)
    CONFIG_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def product_config_exists() -> bool:
    data = load_product()
    return bool(data.get("name") and data.get("domain"))


# ── 展示产品信息表 ─────────────────────────────────────
def show_product_table(data: dict):
    if not data:
        print("  （尚未配置产品信息）")
        return
    col1, col2 = 20, 52
    sep = f"  +{'-'*col1}+{'-'*col2}+"
    print()
    print(sep)
    print(f"  | {'字段':<{col1-1}}| {'内容':<{col2-1}}|")
    print(sep)
    for key, name, required, _ in FIELDS:
        val = data.get(key, "")
        if isinstance(val, list):
            val = ", ".join(val)
        flag  = "" if required else " [可选]"
        label = f"{name}{flag}"
        print(f"  | {label:<{col1-1}}| {str(val)[:col2-2]:<{col2-1}}|")
    print(sep)


# ── 展示图片文件夹状态 ─────────────────────────────────
def show_images_status():
    IMAGES_DIR.mkdir(exist_ok=True)
    exts = ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.webp"]
    imgs = []
    for ext in exts:
        imgs.extend(IMAGES_DIR.glob(ext))
    imgs = sorted(set(imgs))

    print()
    print(f"  [图片文件夹]  {IMAGES_DIR}")
    if imgs:
        print(f"  已有 {len(imgs)} 张图片：")
        for img in imgs:
            tag = " <-- 提交时优先用作 Logo" if img.stem.lower() == "logo" else ""
            print(f"    - {img.name}{tag}")
    else:
        print("  当前无图片。建议将以下文件复制到上方路径：")
        print("    logo.png        (产品 Logo，提交时优先使用)")
        print("    screenshot.png  (产品截图)")
    print()
    print("  提示：直接将图片复制到该文件夹，工具提交时自动识别上传。")
    print("  遇到需要图片但文件夹为空的站点，结果表格会提醒你。")


# ── 交互式填写 / 编辑 ─────────────────────────────────
def run_product_setup() -> dict:
    existing = load_product()
    is_edit  = product_config_exists()

    print()
    if is_edit:
        print("  [编辑产品信息]")
        show_product_table(existing)
        print()
        print("  直接按 Enter 保留现有值，输入新内容即覆盖。")
    else:
        print("  [新增产品信息]")
        print("  标注 * 为必填，其余可按 Enter 跳过。")
    print()

    data = dict(existing)

    for key, name, required, hint in FIELDS:
        old_val = data.get(key, "")
        if isinstance(old_val, list):
            old_val = ", ".join(old_val)

        flag   = "*" if required else "（可选）"
        prompt = f"\n  {flag} {name}"
        if hint:
            prompt += f"\n    提示：{hint}"
        if old_val:
            prompt += f"\n    当前：{old_val[:70]}"
        prompt += "\n  > "

        while True:
            val = input(prompt).strip()
            if not val:
                if old_val:
                    val = old_val
                    break
                elif not required:
                    val = ""
                    break
                else:
                    print("    此字段为必填，请输入内容。")
                    continue
            break

        # 多值字段拆分为 list
        if key in ("keywords", "social_links"):
            data[key] = [v.strip() for v in val.split(",") if v.strip()]
        else:
            data[key] = val

    # ── 补充衍生字段 ───────────────────────────────────
    domain = data.get("domain", "").replace("https://","").replace("http://","").strip("/")
    data["domain"] = domain
    data["url"]    = f"https://{domain}"

    # social_twitter
    socials = data.get("social_links", [])
    if isinstance(socials, str):
        socials = [s.strip() for s in socials.split(",") if s.strip()]
        data["social_links"] = socials
    twitter = next((s for s in socials if "twitter.com" in s or "x.com" in s), "")
    data["social_twitter"] = twitter

    # tags（和 keywords 保持一致）
    kw = data.get("keywords", [])
    if isinstance(kw, list):
        data["tags"] = ", ".join(kw)

    if not data.get("category"):
        data["category"] = "AI Tools"

    # short_desc_alt / long_desc_alt（兜底备用）
    data.setdefault("short_desc_alt", data.get("short_desc", ""))
    data.setdefault("long_desc_alt",  data.get("long_desc", ""))

    save_product(data)
    print("\n  [完成] 产品信息已保存！")
    show_product_table(data)

    # 图片状态
    show_images_status()

    return data
