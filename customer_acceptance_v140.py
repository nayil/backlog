#!/usr/bin/env python3
"""
Customer Acceptance Test for v1.4.0: ItemFormScreen ConfirmDiscardScreen
Runs the actual BacklogApp and verifies discard confirmation flow.
"""

import asyncio
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from screens import ItemFormScreen, ConfirmDiscardScreen
from app import BacklogApp


def get_form_screen(app):
    """Get ItemFormScreen from screen stack."""
    for s in reversed(app.screen_stack):
        if isinstance(s, ItemFormScreen):
            return s
    return None


def has_confirm_discard(app):
    """Check if ConfirmDiscardScreen is on stack."""
    return any(isinstance(s, ConfirmDiscardScreen) for s in app.screen_stack)


async def scenario_1_unsaved_esc_shows_confirm():
    """a -> input title -> Esc -> should show ConfirmDiscardScreen."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "backlog.db")
        app = BacklogApp(db_path=db_path)
        async with app.run_test() as pilot:
            await pilot.pause(0.1)
            await pilot.press("a")
            await pilot.pause(0.2)
            form = get_form_screen(app)
            if not form:
                return False, "ItemFormScreen did not open after 'a'"
            # Simulate user typing title
            form.query_one("#inp-title").value = "test"
            await pilot.press("escape")
            await pilot.pause(0.2)
            if not has_confirm_discard(app):
                return False, "ConfirmDiscardScreen did not appear after Esc with unsaved changes"
            return True, "OK"


async def scenario_2_n_returns_to_form():
    """With confirm open, N -> back to form."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "backlog.db")
        app = BacklogApp(db_path=db_path)
        async with app.run_test() as pilot:
            await pilot.pause(0.1)
            await pilot.press("a")
            await pilot.pause(0.2)
            form = get_form_screen(app)
            if not form:
                return False, "ItemFormScreen did not open"
            form.query_one("#inp-title").value = "test"
            await pilot.press("escape")
            await pilot.pause(0.2)
            if not has_confirm_discard(app):
                return False, "ConfirmDiscardScreen did not appear"
            await pilot.press("n")
            await pilot.pause(0.2)
            if has_confirm_discard(app):
                return False, "ConfirmDiscardScreen still visible after N"
            if form not in app.screen_stack:
                return False, "Form closed after N (should stay open)"
            return True, "OK"


async def scenario_3_y_closes_form():
    """With confirm open, Y -> form closes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "backlog.db")
        app = BacklogApp(db_path=db_path)
        async with app.run_test() as pilot:
            await pilot.pause(0.1)
            await pilot.press("a")
            await pilot.pause(0.2)
            form = get_form_screen(app)
            if not form:
                return False, "ItemFormScreen did not open"
            form.query_one("#inp-title").value = "test"
            await pilot.press("escape")
            await pilot.pause(0.2)
            if not has_confirm_discard(app):
                return False, "ConfirmDiscardScreen did not appear"
            await pilot.press("y")
            await pilot.pause(0.2)
            if form in app.screen_stack:
                return False, "Form still open after Y (should close)"
            return True, "OK"


async def scenario_4_no_changes_esc_direct_close():
    """a -> no input -> Esc -> direct close, no confirm."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "backlog.db")
        app = BacklogApp(db_path=db_path)
        async with app.run_test() as pilot:
            await pilot.pause(0.1)
            await pilot.press("a")
            await pilot.pause(0.2)
            form = get_form_screen(app)
            if not form:
                return False, "ItemFormScreen did not open"
            # Do NOT modify any field
            await pilot.press("escape")
            await pilot.pause(0.2)
            if has_confirm_discard(app):
                return False, "ConfirmDiscardScreen appeared when no changes (should not)"
            if form in app.screen_stack:
                return False, "Form still open after Esc with no changes (should close)"
            return True, "OK"


async def main():
    results = []
    scenarios = [
        ("有修改时按 Esc 弹出 ConfirmDiscardScreen", scenario_1_unsaved_esc_shows_confirm),
        ("选 N 回到表单继续编辑", scenario_2_n_returns_to_form),
        ("选 Y 关闭表单", scenario_3_y_closes_form),
        ("无修改时按 Esc 直接关闭不弹确认", scenario_4_no_changes_esc_direct_close),
    ]
    for name, coro in scenarios:
        try:
            ok, msg = await coro()
            results.append((name, ok, msg))
            print(f"[{'PASS' if ok else 'FAIL'}] {name}: {msg}")
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"[FAIL] {name}: {e}")

    passed = sum(1 for _, ok, _ in results if ok)
    failed = len(results) - passed
    print()
    print("=" * 50)
    print("CUSTOMER ACCEPTANCE SUMMARY")
    print("=" * 50)
    print(f"PASSED: {passed}  FAILED: {failed}  TOTAL: {len(results)}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
