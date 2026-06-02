# -*- coding: utf-8 -*-
"""
工具配置入口
产品信息从 output/product.json 动态读取
"""
import os
from pathlib import Path
from product_manager import load_product, IMAGES_DIR

# ── 图片目录 ──────────────────────────────────────────
# (re-exported from product_manager for backward compat)

# ── Google 登录（用于需要 Google 账号才能提交的目录站）──
# 从环境变量读取，或在本地创建 .env 文件（参考 .env.example）
GOOGLE_EMAIL    = os.environ.get("GOOGLE_EMAIL", "")
GOOGLE_PASSWORD = os.environ.get("GOOGLE_PASSWORD", "")

# ── 产品信息（动态加载，每次调用均读取最新 JSON）────────
def get_product() -> dict:
    """从磁盘读取最新产品配置（支持同一次运行中途修改）"""
    return load_product()

# 向后兼容：模块级 PRODUCT（仅首次 import 时读取一次）
PRODUCT = load_product()
