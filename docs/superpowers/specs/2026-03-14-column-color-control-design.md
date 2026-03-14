# Column Color Independent Control Design

## Summary

Remove the theme system and implement per-column independent color control for the main backlog table. Only Status and Priority columns have configurable colors; all other columns use default terminal colors.

## Changes

### 1. Remove Theme System

**Delete files:**
- `src/themes.py`
- `src/screens/theme_screen.py`

**Modify files:**
- `src/screens/__init__.py` — remove `ThemeScreen` export
- `src/screens/help_screen.py` — remove `Ctrl+T Switch color theme` line (line 70)
- `src/app.py` — remove theme imports, `CUSTOM_THEMES`/`AVAILABLE_THEMES` usage, `ctrl+t` binding, `action_change_theme`, theme registration in `on_mount`, theme loading from config
- `src/config.py` — remove `DEFAULT_THEME`, `get_theme`/`set_theme` methods and module-level functions. Keep `BacklogConfig._load`/`_save` as shared config I/O infrastructure.

**Note:** Textual's built-in default theme (`textual-dark`) remains active and all `$variable` references in CSS (e.g., `$accent`, `$text`, `$primary`) will continue to resolve.

**Note:** Any existing `"theme"` key in `config.json` will be silently ignored going forward (no migration needed).

### 2. New `src/color_config.py`

`ColorConfig` delegates file I/O to `BacklogConfig._load`/`_save` (composition, not duplication) to avoid two classes independently writing to the same JSON file.

The `DEFAULT_*` constants are moved from `colors.py` (`STATUS_COLORS`/`PRIORITY_COLORS`), not redefined.

```python
class ColorConfig:
    DEFAULT_STATUS_COLORS = {
        "todo": "#61AFEF",
        "in_progress": "#E5C07B",
        "done": "#98C379",
    }
    DEFAULT_PRIORITY_COLORS = {
        "high": "#E06C75",
        "medium": "#E5C07B",
        "low": "#98C379",
    }

    def __init__(self):
        # Load from ~/.backlog/config.json via BacklogConfig, merge with defaults

    def get_status_color(self, status_value: str) -> str:
        # User override > default. Unknown keys silently ignored.

    def get_priority_color(self, priority_value: str) -> str:
        # User override > default. Unknown keys silently ignored.

    def set_status_color(self, status_value: str, color: str) -> None:
        # Validate hex format (#RRGGBB), raise ValueError if invalid.
        # Persist to config.json via BacklogConfig.

    def set_priority_color(self, priority_value: str, color: str) -> None:
        # Validate hex format (#RRGGBB), raise ValueError if invalid.
        # Persist to config.json via BacklogConfig.
```

**Config format** (`~/.backlog/config.json`):
```json
{
  "status_colors": {"todo": "#61AFEF"},
  "priority_colors": {"high": "#FF0000"}
}
```

- Unset enum values fall back to `DEFAULT_*` constants.
- Unknown keys in `status_colors`/`priority_colors` are silently ignored.
- Color values must be valid hex format (`#RRGGBB`); invalid values at read time fall back to defaults.

### 3. Modify `src/colors.py`

- Remove `STATUS_COLORS`, `PRIORITY_COLORS`, `CATEGORY_COLORS` constants (moved to `ColorConfig`)
- Remove `colorize_category`, `category_color` functions (category coloring is intentionally removed per user request)
- Keep `STATUS_DISPLAY`, `PRIORITY_DISPLAY`, `NEXT_STATUS`
- Change signatures (breaking change, no other call sites exist outside `_refresh_table`):
  - `colorize_status(status: Status, color_config: ColorConfig) -> Text`
  - `colorize_priority(priority: Priority, color_config: ColorConfig) -> Text`

### 4. Modify `src/app.py`

- `__init__`: create `self.color_config = ColorConfig()`
- `_refresh_table`: Category column passes plain text string; Status/Priority pass `self.color_config` to colorize functions
- Remove all theme-related imports and code

### 5. Testing

- Update existing tests to remove theme assertions
- Unit tests for `ColorConfig`:
  - Default values when no config file exists
  - User overrides merge correctly with defaults
  - Partial overrides (only some enum values set)
  - Invalid hex colors fall back to defaults
  - Unknown keys silently ignored
  - Malformed config.json (invalid JSON) falls back to all defaults
- Unit tests for `colorize_status`/`colorize_priority` with custom `ColorConfig`
- Manual verification: table renders correctly, colors apply to correct columns only
