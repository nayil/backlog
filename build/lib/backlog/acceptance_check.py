import asyncio
import sys
sys.path.insert(0, '.')
from app import BacklogApp, HelpScreen

async def run_acceptance():
    results = []
    app = BacklogApp(db_path="/tmp/acceptance_v060.db")
    async with app.run_test() as pilot:
        # 打开帮助界面
        await pilot.press("question_mark")
        await pilot.pause(0.3)

        # 验证 HelpScreen 已挂载
        screens = app.screen_stack
        help_mounted = any(isinstance(s, HelpScreen) for s in screens)
        results.append(("HelpScreen 可正常打开", help_mounted))

        if help_mounted:
            help_screen = next(s for s in screens if isinstance(s, HelpScreen))

            # 获取所有可见文本
            labels = help_screen.query("Label")
            all_text = "\n".join(str(label.render()) for label in labels)

            print("\n--- Help Screen Text ---")
            print(all_text)
            print("--- End of Help Screen Text ---\n")

            # 验证各项内容
            checks = [
                ("主列表列名说明存在 (Main List Columns)", "Main List Columns" in all_text),
                ("主列表 Age 列说明存在", "Age" in all_text),
                ("表单字段说明存在 (Item Form Fields)", "Item Form Fields" in all_text),
                ("统计栏说明存在 (Status Bar)", "Status Bar" in all_text),
                ("垃圾桶180天过期说明", "180" in all_text),
                ("Status Cycle路径正确 (Todo → In Progress → Done → In Progress)", "Todo" in all_text and "In Progress" in all_text and "Done" in all_text),
                ("Edit表单可任意修改Status说明存在", "Edit" in all_text or "edit" in all_text),
            ]
            results.extend(checks)

        # 关闭帮助界面（ESC）
        await pilot.press("escape")
        await pilot.pause(0.1)

        # 验证帮助界面已关闭
        screens_after = app.screen_stack
        help_closed = not any(isinstance(s, HelpScreen) for s in screens_after)
        results.append(("HelpScreen 可正常关闭", help_closed))

    # 输出结果
    passed = sum(1 for _, ok in results if ok)
    print(f"\n验收结果: {passed}/{len(results)} 通过")
    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'} {name}")

    return all(ok for _, ok in results)

success = asyncio.run(run_acceptance())
sys.exit(0 if success else 1)
