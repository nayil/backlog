#!/usr/bin/env python3
"""v1.3.0 客户验收自动化验证脚本：主表/回收站列顺序、Help 弹窗宽度与文案顺序。"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from app import BacklogApp, HelpScreen
from screens.trash import TrashScreen


async def run_verification():
    results = []
    app = BacklogApp(db_path="/tmp/verify_v130.db")

    async with app.run_test() as pilot:
        # 1. 主表列顺序：ID|Category|Title|Status|Priority|Age
        table = app.query_one("#table")
        main_cols = [str(c.label) for c in table.columns.values()]
        expected_main = ["ID", "Category", "Title", "Status", "Priority", "Age"]
        main_ok = main_cols == expected_main
        results.append(("主表列顺序 ID|Category|Title|Status|Priority|Age", main_ok, str(main_cols)))

        # 2. 打开回收站，验证列顺序
        await pilot.press("t")
        await pilot.pause(0.3)
        trash_screen = next((s for s in app.screen_stack if isinstance(s, TrashScreen)), None)
        trash_ok = False
        trash_cols_str = "N/A"
        if trash_screen:
            trash_table = trash_screen.query_one("#trash-table")
            trash_cols = [str(c.label) for c in trash_table.columns.values()]
            expected_trash = ["ID", "Category", "Title", "Deleted At", "Expires At"]
            trash_ok = trash_cols == expected_trash
            trash_cols_str = str(trash_cols)
        results.append(("回收站列顺序 ID|Category|Title|Deleted At|Expires At", trash_ok, trash_cols_str))

        # 关闭回收站
        await pilot.press("escape")
        await pilot.pause(0.2)

        # 3. 打开 Help，验证宽度与 Main List Columns 文案顺序
        await pilot.press("question_mark")
        await pilot.pause(0.3)
        help_screen = next((s for s in app.screen_stack if isinstance(s, HelpScreen)), None)
        help_width_ok = False
        help_order_ok = False
        if help_screen:
            # Help 宽度 80：由 test_help_screen_v130 已通过，此处通过源码快速校验
            import re
            help_py = Path(__file__).resolve().parent / "src" / "screens" / "help_screen.py"
            src = help_py.read_text()
            m = re.search(r"#help-container\s*\{[^}]*width\s*:\s*(\d+)\s*;", src, re.DOTALL)
            help_width_ok = m and int(m.group(1)) == 80
            # Main List Columns 文案顺序：ID, Category, Title, Status, Priority, Age
            labels = help_screen.query("Label")
            all_text = "\n".join(str(l.render()) for l in labels)
            idx_main = all_text.find("Main List Columns")
            if idx_main >= 0:
                block = all_text[idx_main : idx_main + 400]
                idx_id = block.find("ID")
                idx_cat = block.find("Category")
                idx_title = block.find("Title")
                idx_status = block.find("Status")
                idx_pri = block.find("Priority")
                idx_age = block.find("Age")
                help_order_ok = 0 <= idx_id < idx_cat < idx_title < idx_status < idx_pri < idx_age
        results.append(("Help 弹窗宽度 80", help_width_ok, "width 检查"))
        results.append(("Help Main List Columns 文案顺序 ID→Category→Title→Status→Priority→Age", help_order_ok, "文案顺序"))

        # 关闭 Help
        await pilot.press("escape")

    return results


def main():
    results = asyncio.run(run_verification())
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"\n=== v1.3.0 客户验收自动化验证 ===\n")
    print(f"结果: {passed}/{total} 通过\n")
    for name, ok, detail in results:
        status = "PASS" if ok else "FAIL"
        print(f"  {status} {name}")
        if not ok and detail:
            print(f"       详情: {detail}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
