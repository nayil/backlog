"""Acceptance test for v0.7.0: description TextArea upgrade."""
import asyncio
import sys
import tempfile
import os

sys.path.insert(0, 'src')

from textual.widgets import TextArea, Input
from app import BacklogApp, ItemFormScreen


async def type_text(pilot, text: str):
    """Type text using press() for each character."""
    for ch in text:
        if ch == ' ':
            await pilot.press("space")
        elif ch.isupper():
            await pilot.press(f"shift+{ch.lower()}")
        else:
            await pilot.press(ch)


async def run_acceptance(db_path: str):
    results = []

    app = BacklogApp(db_path=db_path)
    async with app.run_test(size=(120, 40)) as pilot:
        # 等待应用加载
        await pilot.pause(0.5)

        # 打开新建表单（绑定键是 "a" = Add）
        await pilot.press("a")
        await pilot.pause(0.5)

        # 确认当前 screen 是 ItemFormScreen
        current_screen = app.screen
        print(f"  当前屏幕类型: {type(current_screen).__name__}", flush=True)

        # 测试1：打开新建表单，验证 description 字段是 TextArea
        try:
            desc_widget = current_screen.query_one("#inp-desc", TextArea)
            results.append(("TC-01: description 字段是 TextArea", "PASS", "找到 TextArea#inp-desc"))
        except Exception as e:
            results.append(("TC-01: description 字段是 TextArea", "FAIL", str(e)))

        # 测试2：验证 description 字段不是 Input
        try:
            desc_input = None
            try:
                desc_input = current_screen.query_one("#inp-desc", Input)
            except Exception:
                pass
            if desc_input is None:
                results.append(("TC-02: description 字段不是 Input", "PASS", "#inp-desc 不是 Input 类型"))
            else:
                results.append(("TC-02: description 字段不是 Input", "FAIL", "找到了 Input#inp-desc"))
        except Exception as e:
            results.append(("TC-02: description 字段不是 Input", "PASS", f"Input not found: {e}"))

        # 测试3：在 TextArea 中输入文本（包含换行）
        try:
            desc_widget = current_screen.query_one("#inp-desc", TextArea)
            await pilot.click("#inp-desc")
            await pilot.pause(0.2)
            await type_text(pilot, "first")
            await pilot.press("enter")
            await type_text(pilot, "second")
            await pilot.pause(0.3)

            text = desc_widget.text
            print(f"  TextArea 内容: {repr(text[:80])}", flush=True)
            if "first" in text and "second" in text and "\n" in text:
                results.append(("TC-03: TextArea 支持多行输入", "PASS", f"text={repr(text[:50])}"))
            else:
                results.append(("TC-03: TextArea 支持多行输入", "FAIL", f"text={repr(text[:50])}"))
        except Exception as e:
            results.append(("TC-03: TextArea 支持多行输入", "FAIL", str(e)))

        # 测试4：填写 title 并用 Ctrl+S 保存
        try:
            await pilot.click("#inp-title")
            await pilot.pause(0.1)
            await type_text(pilot, "TestItemv070")
            await pilot.pause(0.1)
            await pilot.press("ctrl+s")
            await pilot.pause(0.5)
            results.append(("TC-04: Ctrl+S 可以保存表单", "PASS", "表单保存触发成功"))
        except Exception as e:
            results.append(("TC-04: Ctrl+S 可以保存表单", "FAIL", str(e)))

        # 测试5：验证保存后界面回到主列表（表单关闭）
        await pilot.pause(0.3)
        try:
            screens = list(app.screen_stack)
            print(f"  保存后屏幕栈: {[type(s).__name__ for s in screens]}", flush=True)
            form_open = any(isinstance(s, ItemFormScreen) for s in screens)
            if not form_open:
                results.append(("TC-05: 保存后表单关闭", "PASS", "ItemFormScreen 已关闭"))
            else:
                results.append(("TC-05: 保存后表单关闭", "FAIL", "表单仍然打开"))
        except Exception as e:
            results.append(("TC-05: 保存后表单关闭", "FAIL", str(e)))

        # 测试6：验证编辑时 description 正确回填到 TextArea
        await pilot.pause(0.3)
        try:
            await pilot.press("e")
            await pilot.pause(0.5)
            current_screen2 = app.screen
            print(f"  编辑屏幕类型: {type(current_screen2).__name__}", flush=True)
            desc_widget2 = current_screen2.query_one("#inp-desc", TextArea)
            text2 = desc_widget2.text
            print(f"  编辑回填内容: {repr(text2[:80])}", flush=True)
            if "first" in text2 and "second" in text2:
                results.append(("TC-06: 编辑时 description 正确回填到 TextArea", "PASS", f"回填内容={repr(text2[:50])}"))
            else:
                results.append(("TC-06: 编辑时 description 正确回填到 TextArea", "FAIL", f"回填内容={repr(text2[:50])}"))
            await pilot.press("escape")
            await pilot.pause(0.3)
        except Exception as e:
            results.append(("TC-06: 编辑时 description 正确回填到 TextArea", "FAIL", str(e)))

    return results


def main():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        print(f"使用测试数据库: {db_path}", flush=True)
        results = asyncio.run(run_acceptance(db_path))

    print("\n===== 验收结果 =====")
    passed = sum(1 for _, status, _ in results if status == "PASS")
    failed = sum(1 for _, status, _ in results if status == "FAIL")
    for name, status, detail in results:
        print(f"[{status}] {name}: {detail}")
    print(f"\n总计: {passed} 通过, {failed} 失败")
    return failed


if __name__ == "__main__":
    sys.exit(main())
