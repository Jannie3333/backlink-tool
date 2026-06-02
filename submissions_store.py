# -*- coding: utf-8 -*-
"""
提交记录存储
保存每次提交的域名 + 状态，供追踪模块使用
"""
import json
from pathlib import Path
from datetime import datetime

STORE_FILE = Path(__file__).parent / "output" / "submissions.json"


def _load() -> list:
    STORE_FILE.parent.mkdir(exist_ok=True)
    if not STORE_FILE.exists():
        return []
    try:
        return json.loads(STORE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(records: list):
    STORE_FILE.parent.mkdir(exist_ok=True)
    STORE_FILE.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def add_submissions(domains: list, batch_note: str = ""):
    """将一批新提交的域名写入记录（已存在的不重复添加）"""
    records   = _load()
    existing  = {r["domain"] for r in records}
    ts        = datetime.now().strftime("%Y-%m-%d %H:%M")
    added     = 0
    for d in domains:
        d = d.strip()
        if d and d not in existing:
            records.append({
                "domain":       d,
                "submitted_at": ts,
                "status":       "pending",   # pending | live | not_found
                "live_url":     "",
                "checked_at":   "",
                "notified":     False,
                "note":         batch_note,
            })
            existing.add(d)
            added += 1
    _save(records)
    return added


def get_pending() -> list:
    """返回所有 status=pending 的记录"""
    return [r for r in _load() if r["status"] == "pending"]


def get_all() -> list:
    return _load()


def mark_live(domain: str, live_url: str = ""):
    records = _load()
    ts      = datetime.now().strftime("%Y-%m-%d %H:%M")
    for r in records:
        if r["domain"] == domain:
            r["status"]     = "live"
            r["live_url"]   = live_url
            r["checked_at"] = ts
    _save(records)


def mark_not_found(domain: str):
    records = _load()
    ts      = datetime.now().strftime("%Y-%m-%d %H:%M")
    for r in records:
        if r["domain"] == domain:
            r["checked_at"] = ts
            if r["status"] == "pending":
                r["status"] = "not_found"
    _save(records)


def mark_notified(domain: str):
    records = _load()
    for r in records:
        if r["domain"] == domain:
            r["notified"] = True
    _save(records)
