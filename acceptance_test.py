"""
Customer Acceptance Test for Backlog Tool v0.3.0
Tests: Category Autocomplete + Export/Import (JSON & CSV)
"""

import sys
import os
import tempfile
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

PASS = "PASS"
FAIL = "FAIL"
results = []

def check(name, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((name, status, detail))
    print(f"[{status}] {name}" + (f": {detail}" if detail else ""))
    return condition


# ─────────────────────────────────────────────
# Test 1: IO Service round-trip (JSON & CSV)
# ─────────────────────────────────────────────
print("\n=== Test 1: IO Service Functional Tests ===")

try:
    from io_service import export_json, export_csv, import_json, import_csv
    from models import BacklogItem, Status, Priority
    from repository import BacklogRepository
    check("io_service module import", True)
except Exception as e:
    check("io_service module import", False, str(e))
    print("Cannot continue IO tests.")
    io_ok = False
else:
    io_ok = True

if io_ok:
    # Create an in-memory-like repo using a temp SQLite file
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        repo = BacklogRepository(db_path)

        # Seed data
        items_seed = [
            BacklogItem(title="Task Alpha", category="team", status=Status.TODO, priority=Priority.HIGH),
            BacklogItem(title="Task Beta",  category="product", status=Status.IN_PROGRESS, priority=Priority.MEDIUM),
            BacklogItem(title="Task Gamma", category="team", status=Status.TODO, priority=Priority.LOW),
        ]
        for item in items_seed:
            repo.create(item)

        all_items = repo.list()
        check("Seeded 3 items into repo", len(all_items) == 3, f"count={len(all_items)}")
        original_titles = {item.title for item in all_items}

        # ---- JSON round-trip ----
        json_path = os.path.join(tmpdir, "export.json")
        exported_count = export_json(all_items, json_path)
        check("export_json returns count=3", exported_count == 3, f"returned={exported_count}")
        check("export_json file exists", os.path.exists(json_path))

        with open(json_path) as f:
            raw = json.load(f)
        check("export_json produces list", isinstance(raw, list))
        check("export_json list length=3", len(raw) == 3, f"len={len(raw)}")

        # Import into a fresh DB
        db_path2 = os.path.join(tmpdir, "test2.db")
        repo2 = BacklogRepository(db_path2)
        imported_count, skipped_count = import_json(json_path, repo2)
        check("import_json returns (3, 0)", (imported_count, skipped_count) == (3, 0),
              f"got ({imported_count}, {skipped_count})")

        items2 = repo2.list()
        check("import_json inserted 3 records", len(items2) == 3, f"count={len(items2)}")

        # Titles preserved
        imported_titles = {item.title for item in items2}
        check("import_json preserves titles", original_titles == imported_titles)

        # ---- CSV round-trip ----
        csv_path = os.path.join(tmpdir, "export.csv")
        exported_csv_count = export_csv(all_items, csv_path)
        check("export_csv returns count=3", exported_csv_count == 3, f"returned={exported_csv_count}")
        check("export_csv file exists", os.path.exists(csv_path))

        with open(csv_path) as f:
            content = f.read()
        check("export_csv has header row", "title" in content.lower() or "Title" in content,
              f"first 100 chars: {content[:100]}")

        db_path3 = os.path.join(tmpdir, "test3.db")
        repo3 = BacklogRepository(db_path3)
        imported_csv_count, skipped_csv = import_csv(csv_path, repo3)
        check("import_csv returns (3, 0)", (imported_csv_count, skipped_csv) == (3, 0),
              f"got ({imported_csv_count}, {skipped_csv})")

        items3 = repo3.list()
        check("import_csv inserted 3 records", len(items3) == 3, f"count={len(items3)}")

        titles3 = {item.title for item in items3}
        check("import_csv preserves titles", original_titles == titles3)

        # Special characters in CSV
        db_path4 = os.path.join(tmpdir, "test4.db")
        repo4 = BacklogRepository(db_path4)
        special = BacklogItem(
            title='Task with, comma and "quotes"',
            category="special",
            description="line1\nline2",
            status=Status.TODO,
            priority=Priority.HIGH,
        )
        repo4.create(special)
        special_items = repo4.list()
        csv_special_path = os.path.join(tmpdir, "special.csv")
        export_csv(special_items, csv_special_path)
        db_path5 = os.path.join(tmpdir, "test5.db")
        repo5 = BacklogRepository(db_path5)
        cnt, skip = import_csv(csv_special_path, repo5)
        items5 = repo5.list()
        check("CSV handles special chars (comma/quotes/newline)", cnt == 1 and len(items5) == 1,
              f"imported={cnt}, items={len(items5)}")
        if items5:
            check("CSV special char title preserved", items5[0].title == special.title,
                  f"got={items5[0].title!r}")


# ─────────────────────────────────────────────
# Test 2: Category Autocomplete code verification
# ─────────────────────────────────────────────
print("\n=== Test 2: Category Autocomplete Code Verification ===")

try:
    import ast
    app_path = os.path.join(os.path.dirname(__file__), "src", "app.py")
    with open(app_path) as f:
        source = f.read()
    tree = ast.parse(source)
    check("app.py parses without syntax error", True)
except SyntaxError as e:
    check("app.py parses without syntax error", False, str(e))
    source = ""
    tree = None

if tree:
    # Check SuggestFromList is imported
    suggest_imported = "SuggestFromList" in source
    check("SuggestFromList referenced in app.py", suggest_imported)

    # Check ItemFormScreen accepts categories param
    class_found = False
    categories_param = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "ItemFormScreen":
            class_found = True
            for item in ast.walk(node):
                if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                    args = [a.arg for a in item.args.args]
                    if "categories" in args:
                        categories_param = True
    check("ItemFormScreen class exists", class_found)
    check("ItemFormScreen.__init__ accepts 'categories' param", categories_param)

    # Check SuggestFromList is used inside ItemFormScreen
    suggest_used = "SuggestFromList" in source
    check("SuggestFromList used in app.py", suggest_used)


# ─────────────────────────────────────────────
# Test 3: app.py Health Check
# ─────────────────────────────────────────────
print("\n=== Test 3: app.py Basic Health Check ===")

try:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "app", os.path.join(os.path.dirname(__file__), "src", "app.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    check("app.py imports without error", True)
except Exception as e:
    check("app.py imports without error", False, str(e))
    mod = None

if mod:
    check("ExportScreen class exists", hasattr(mod, "ExportScreen"))
    check("ImportScreen class exists", hasattr(mod, "ImportScreen"))

    app_cls = getattr(mod, "BacklogApp", None)
    check("BacklogApp class exists", app_cls is not None)

    if app_cls:
        bindings = getattr(app_cls, "BINDINGS", [])
        binding_keys = []
        for b in bindings:
            if hasattr(b, "key"):
                binding_keys.append(b.key)
            elif isinstance(b, (list, tuple)) and len(b) >= 1:
                binding_keys.append(b[0])
        bindings_str = str(bindings)
        has_ctrl_e = "ctrl+e" in bindings_str.lower() or "ctrl+e" in binding_keys
        has_ctrl_i = "ctrl+i" in bindings_str.lower() or "ctrl+i" in binding_keys
        check("BacklogApp.BINDINGS contains ctrl+e", has_ctrl_e, f"bindings={binding_keys}")
        check("BacklogApp.BINDINGS contains ctrl+i", has_ctrl_i, f"bindings={binding_keys}")


# ─────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────
print("\n" + "="*50)
print("ACCEPTANCE TEST SUMMARY")
print("="*50)
passed = sum(1 for _, s, _ in results if s == PASS)
failed = sum(1 for _, s, _ in results if s == FAIL)
print(f"PASSED: {passed}  FAILED: {failed}  TOTAL: {len(results)}")
print()
if failed:
    print("FAILED TESTS:")
    for name, status, detail in results:
        if status == FAIL:
            print(f"  - {name}: {detail}")
print()
print("OVERALL:", PASS if failed == 0 else FAIL)
sys.exit(0 if failed == 0 else 1)
