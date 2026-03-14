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
- `src/app.py` — remove theme imports, `CUSTOM_THEMES`/`AVAILABLE_THEMES` usage, `ctrl+t` binding, `action_change_theme`, theme registration in `on_mount`, theme loading from config
- `src/config.py` — remove `DEFAULT_THEME`, `get_theme`/`set_theme` methods and module-level functions

### 2. New `src/color_config.py`

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
        # Load from ~/.backlog/config.json, merge with defaults

    def get_status_color(self, status_value: str) -> str:
        # User override > default

    def get_priority_color(self, priority_value: str) -> str:
        # User override > default

    def set_status_color(self, status_value: str, color: str) -> None:
        # Persist to config.json

    def set_priority_color(self, priority_value: str, color: str) -> None:
        # Persist to config.json
```

**Config format** (`~/.backlog/config.json`):
```json
{
  "status_colors": {"todo": "#61AFEF"},
  "priority_colors": {"high": "#FF0000"}
}
```

Unset enum values fall back to `DEFAULT_*` constants.

### 3. Modify `src/colors.py`

- Remove `STATUS_COLORS`, `PRIORITY_COLORS`, `CATEGORY_COLORS` constants
- Remove `colorize_category`, `category_color` functions
- Keep `STATUS_DISPLAY`, `PRIORITY_DISPLAY`, `NEXT_STATUS`
- `colorize_status(status, color_config)` — get color from `color_config.get_status_color()`
- `colorize_priority(priority, color_config)` — get color from `color_config.get_priority_color()`

### 4. Modify `src/app.py`

- `__init__`: create `self.color_config = ColorConfig()`
- `_refresh_table`: Category column passes plain text string; Status/Priority pass `self.color_config` to colorize functions
- Remove all theme-related imports and code

### 5. Testing

- Update existing tests to remove theme assertions
- Unit tests for `ColorConfig`: defaults, user overrides, partial overrides, missing config file
- Unit tests for `colorize_status`/`colorize_priority` with custom `ColorConfig`
