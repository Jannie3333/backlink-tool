# -*- coding: utf-8 -*-
"""
外链工具箱 v2.0 - 终端版
"""
import sys
import os

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def banner():
    print("=" * 55)
    print("  外链工具箱 v2.0")
    print("=" * 55)

def menu():
    from product_manager import load_product
    clear()
    banner()
    # 显示当前产品名
    p = load_product()
    prod_name = p.get("name", "（未设置）")
    prod_domain = p.get("domain", "")
    print()
    print(f"  当前产品：{prod_name}  {prod_domain}")
    print()
    print("  请选择工作模式：")
    print()
    print("  [1]  外链调研")
    print("       输入竞品域名，查询 Ahrefs 外链 + 找联系邮箱")
    print()
    print("  [2]  直接提交外链")
    print(f"       输入最多 20 个域名，自动提交 {prod_name}")
    print()
    print("  [3]  完整流程（调研 -> 提交）")
    print("       先调研竞品外链，再对这些网站自动提交")
    print()
    print("  [4]  外链追踪")
    print(f"       检查已提交网站是否收录了 {prod_name}")
    print("       发现上线时桌面弹窗通知")
    print()
    print("  [5]  产品信息设置")
    print("       新增/修改产品信息 + 管理上传图片")
    print()
    print("  [0]  退出")
    print()
    return input("  输入编号：").strip()


# ─── 打印提交结果表格 ──────────────────────────────────
def print_result_table(results: list, title: str = "提交结果"):
    STATUS_LABEL = {
        "success":        "成功",
        "no_entry":       "无入口",
        "login_required": "需登录",
        "error":          "失败",
        "skipped":        "跳过",
    }
    col1, col2, col3 = 35, 10, 38
    sep = f"  +{'-'*col1}+{'-'*col2}+{'-'*col3}+"
    print()
    print(f"  == {title} ==")
    print(sep)
    print(f"  | {'域名':<{col1-1}}| {'结果':<{col2-1}}| {'备注':<{col3-1}}|")
    print(sep)
    for r in results:
        domain = r.get("domain", "")[:col1-2]
        status = STATUS_LABEL.get(r.get("status",""), r.get("status",""))[:col2-2]
        note   = r.get("note","")[:col3-2]
        print(f"  | {domain:<{col1-1}}| {status:<{col2-1}}| {note:<{col3-1}}|")
    print(sep)
    ok       = sum(1 for r in results if r["status"] == "success")
    no_entry = sum(1 for r in results if r["status"] == "no_entry")
    login    = sum(1 for r in results if r["status"] == "login_required")
    err      = sum(1 for r in results if r["status"] in ("error","unknown"))
    print(f"  合计：{len(results)} 个  |  成功 {ok}  |  无入口 {no_entry}  |  需登录 {login}  |  失败 {err}")
    print()


def print_tracking_table(records: list, title: str = "追踪状态"):
    STATUS_LABEL = {
        "pending":   "待检查",
        "live":      "已上线",
        "not_found": "未收录",
    }
    col1, col2, col3, col4 = 32, 10, 26, 18
    sep = f"  +{'-'*col1}+{'-'*col2}+{'-'*col3}+{'-'*col4}+"
    print()
    print(f"  == {title} ==")
    print(sep)
    print(f"  | {'域名':<{col1-1}}| {'状态':<{col2-1}}| {'上线链接':<{col3-1}}| {'最近检查':<{col4-1}}|")
    print(sep)
    for r in records:
        domain   = r.get("domain","")[:col1-2]
        status   = STATUS_LABEL.get(r.get("status",""), r.get("status",""))[:col2-2]
        live_url = r.get("live_url","")[:col3-2]
        checked  = r.get("checked_at","")[:col4-2]
        print(f"  | {domain:<{col1-1}}| {status:<{col2-1}}| {live_url:<{col3-1}}| {checked:<{col4-1}}|")
    print(sep)
    live    = sum(1 for r in records if r["status"] == "live")
    pending = sum(1 for r in records if r["status"] == "pending")
    notfnd  = sum(1 for r in records if r["status"] == "not_found")
    print(f"  合计：{len(records)} 个  |  已上线 {live}  |  待检查 {pending}  |  未收录 {notfnd}")
    print()


def ask_continue_or_stop(all_results: list, batch_num: int) -> bool:
    print()
    print(f"  -- 第 {batch_num} 批完成，累计已提交 {len(all_results)} 个站 --")
    print()
    print("  流程是否结束？")
    print("  [1] 继续提交下一批")
    print("  [2] 结束并输出完整报告")
    print()
    return input("  输入编号：").strip() == "1"


# ─── 核心：提交循环 ────────────────────────────────────
def submit_loop(initial_domains: list = None):
    from submitter import run_submissions
    from excel_helper import save_submit_report
    import submissions_store as store

    all_results  = []
    batch_num    = 0
    domain_queue = list(initial_domains) if initial_domains else []

    while True:
        if domain_queue:
            batch        = domain_queue[:20]
            domain_queue = domain_queue[20:]
        else:
            print()
            print("  粘贴域名（每行一个，最多 20 个，输完后输入空行回车）：")
            print()
            lines = []
            while True:
                line = input("  ").strip()
                if not line:
                    break
                lines.append(line)
                if len(lines) >= 20:
                    print("  （已达 20 个，自动开始）")
                    break
            batch = [
                d.replace("https://","").replace("http://","").strip("/")
                for d in lines if d.strip()
            ]
            if not batch:
                print("  未输入域名，退出提交。")
                break

        if not batch:
            break

        batch_num += 1
        print(f"\n  开始提交第 {batch_num} 批（共 {len(batch)} 个）...\n")

        def log(msg):
            print(" ", msg)

        results = run_submissions(batch, log_cb=log)
        all_results.extend(results)

        # 把成功提交的域名加入追踪列表
        submitted_ok = [r["domain"] for r in results
                        if r["status"] in ("success",)]
        if submitted_ok:
            added = store.add_submissions(submitted_ok, batch_note=f"第{batch_num}批")
            print(f"\n  [追踪] 已将 {added} 个新域名加入追踪列表")

        # 显示本批表格
        print_result_table(results, title=f"第 {batch_num} 批提交结果")

        # 询问继续 or 停止
        has_more = len(domain_queue) > 0
        if has_more:
            print(f"  队列中还有 {len(domain_queue)} 个域名")
            go = input("  继续下一批？(y/n)：").strip().lower()
            if go != "y":
                break
        else:
            if not ask_continue_or_stop(all_results, batch_num):
                break

    # 最终报告
    if all_results:
        print()
        print_result_table(all_results, title=f"完整报告（共 {batch_num} 批）")
        filepath = save_submit_report(all_results)
        print(f"  Excel 报告已保存：{filepath}")

    print()
    input("  按 Enter 返回主菜单...")


# ─── 模式 5：产品信息设置 ────────────────────────────────
def mode_product_setup():
    from product_manager import run_product_setup, show_images_status
    clear(); banner()
    run_product_setup()
    print()
    input("  按 Enter 返回主菜单...")


# ─── 模式 1：外链调研 ──────────────────────────────────
def mode_research():
    from scraper import run_scraper
    from excel_helper import save_research_excel

    clear(); banner()
    print("\n[模式 1]  外链调研\n")

    competitor = input("  输入竞品域名（如 runwayml.com）：").strip()
    if not competitor:
        competitor = "runwayml.com"
    try:
        max_links = int(input("  最多查几条外链？（默认 20）：").strip() or "20")
    except ValueError:
        max_links = 20

    print()

    def log(msg):
        print(" ", msg)

    results = run_scraper(competitor, log_cb=log, max_sites=max_links)

    if results:
        filepath = save_research_excel(results, competitor)
        print()
        print(f"  [完成] 共 {len(results)} 条外链，Excel 已保存：")
        print(f"  {filepath}")
    else:
        print("  [警告] 未获取到数据。")

    print()
    input("  按 Enter 返回主菜单...")
    return results


# ─── 模式 2：直接提交 ──────────────────────────────────
def mode_direct_submit():
    clear(); banner()
    print("\n[模式 2]  直接提交外链\n")
    submit_loop(initial_domains=None)


# ─── 模式 3：完整流程 ──────────────────────────────────
def mode_full():
    from scraper import run_scraper
    from excel_helper import save_research_excel

    clear(); banner()
    print("\n[模式 3]  完整流程（调研 -> 提交）\n")

    print("  Step 1/2  外链调研")
    competitor = input("  输入竞品域名（如 runwayml.com）：").strip()
    if not competitor:
        competitor = "runwayml.com"
    try:
        max_links = int(input("  最多查几条外链？（默认 20）：").strip() or "20")
    except ValueError:
        max_links = 20

    print()

    def log(msg):
        print(" ", msg)

    research = run_scraper(competitor, log_cb=log, max_sites=max_links)

    if not research:
        print("  [错误] 未获取到外链数据，终止。")
        input("  按 Enter 返回主菜单...")
        return

    r_path  = save_research_excel(research, competitor)
    domains = [r["referring_domain"] for r in research if r.get("referring_domain")]
    print(f"\n  调研完成：{len(domains)} 个域名，Excel：{r_path}")

    print(f"\n  Step 2/2  提交外链（共 {len(domains)} 个站）")
    confirm = input("  是否开始自动提交？(y/n)：").strip().lower()
    if confirm != "y":
        input("  已取消，按 Enter 返回主菜单...")
        return

    submit_loop(initial_domains=domains)


# ─── 模式 4：外链追踪 ──────────────────────────────────
def mode_tracker():
    import submissions_store as store
    from tracker import run_check, run_auto_loop

    clear(); banner()
    print("\n[模式 4]  外链追踪\n")

    all_records = store.get_all()
    if not all_records:
        print("  暂无提交记录。请先用模式 [2] 或 [3] 提交外链。")
        print()
        input("  按 Enter 返回主菜单...")
        return

    # 显示当前追踪状态
    print_tracking_table(all_records, title="当前追踪列表")

    pending_count  = sum(1 for r in all_records if r["status"] == "pending")
    notfnd_count   = sum(1 for r in all_records if r["status"] == "not_found")
    live_count     = sum(1 for r in all_records if r["status"] == "live")

    print(f"  待检查：{pending_count}  |  未收录：{notfnd_count}  |  已上线：{live_count}")
    print()
    print("  选择操作：")
    print("  [1] 立即检查一次（只检查 pending 的）")
    print("  [2] 立即检查一次（重新检查全部，含未收录的）")
    print("  [3] 自动循环检查（每隔 N 小时检查一次）")
    print("  [0] 返回主菜单")
    print()
    choice = input("  输入编号：").strip()

    def log(msg):
        print(msg)

    if choice == "1":
        print()
        stats = run_check(log_cb=log, check_all=False)
        print()
        print(f"  检查完成：新上线 {stats['new_live']} 个 | 仍未收录 {stats['still_pending']} 个")
        print()
        # 刷新展示
        print_tracking_table(store.get_all(), title="更新后追踪状态")

    elif choice == "2":
        print()
        stats = run_check(log_cb=log, check_all=True)
        print()
        print(f"  检查完成：新上线 {stats['new_live']} 个 | 仍未收录 {stats['still_pending']} 个")
        print()
        print_tracking_table(store.get_all(), title="更新后追踪状态")

    elif choice == "3":
        try:
            hours = float(input("  每隔多少小时检查一次？（建议 12 或 24）：").strip() or "24")
        except ValueError:
            hours = 24
        print()
        try:
            run_auto_loop(interval_hours=hours, log_cb=log)
        except KeyboardInterrupt:
            print("\n  已停止自动追踪。")

    print()
    input("  按 Enter 返回主菜单...")


# ─── 主入口 ───────────────────────────────────────────
def main():
    from product_manager import product_config_exists, load_product

    if not product_config_exists():
        # 首次运行：强制填写产品信息
        clear(); banner()
        print()
        print("  首次使用，请先填写产品信息（完成后即可使用全部功能）。")
        print()
        mode_product_setup()
    else:
        # 已有配置：询问继续还是切换产品
        p = load_product()
        clear(); banner()
        print()
        print(f"  当前产品：{p.get('name','')}  ({p.get('domain','')})")
        print()
        print("  请选择：")
        print(f"  [1]  继续给 {p.get('name','')} 提交外链")
        print("  [2]  切换 / 新增产品")
        print()
        sel = input("  输入编号：").strip()
        if sel == "2":
            mode_product_setup()

    while True:
        choice = menu()
        if   choice == "1": mode_research()
        elif choice == "2": mode_direct_submit()
        elif choice == "3": mode_full()
        elif choice == "4": mode_tracker()
        elif choice == "5": mode_product_setup()
        elif choice == "0":
            clear()
            print("  再见！")
            sys.exit(0)

if __name__ == "__main__":
    main()
