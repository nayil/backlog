"""MainTable widget — DataTable with backlog-specific behavior."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Callable, Optional

from textual.widgets import DataTable, Static

from colors import colorize_priority, colorize_status
from display import truncate_title
from models import Status

if TYPE_CHECKING:
    from color_config import ColorConfig
    from config import BacklogConfig
    from repository import BacklogRepository

COL_TO_SORT = {
    "Status": "status",
    "Category": "category",
    "Priority": "priority",
    "Age": "age",
}


class MainTable(DataTable):
    """DataTable with refresh, selected_item_id, Preview linkage, and sorting."""

    def __init__(
        self,
        repo: "BacklogRepository",
        config: "BacklogConfig",
        color_config: "ColorConfig",
        preview_title: Static,
        preview_desc: Static,
        on_sort_changed: Optional[Callable[[Optional[str], bool], None]] = None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._repo = repo
        self._config = config
        self._color_config = color_config
        self._preview_title = preview_title
        self._preview_desc = preview_desc
        self._on_sort_changed = on_sort_changed
        self._sort_by: Optional[str] = None
        self._sort_asc = True
        self._col_keys: dict = {}

    def on_mount(self) -> None:
        self.cursor_type = "row"
        col_keys = self.add_columns("ID", "Category", "Title", "Status", "Priority", "Age")
        self._col_keys = {
            "ID": col_keys[0],
            "Category": col_keys[1],
            "Title": col_keys[2],
            "Status": col_keys[3],
            "Priority": col_keys[4],
            "Age": col_keys[5],
        }

    def refresh(self, *args, **kwargs) -> None:
        """Load and display table data. App passes already clamped page; no count here.
        When called with no args (from DataTable.clear) or with widget kwargs (repaint, etc),
        delegates to parent.
        """
        load_keys = {"filter_status", "filter_category", "filter_keyword", "page", "page_size", "sort_by", "sort_asc"}
        if not (args or load_keys & set(kwargs)):
            super().refresh()
            return
        filter_status = kwargs.get("filter_status")
        filter_category = kwargs.get("filter_category")
        filter_keyword = kwargs.get("filter_keyword")
        page = kwargs.get("page", 0)
        page_size = kwargs.get("page_size", 20)
        sort_by = kwargs.get("sort_by")
        sort_asc = kwargs.get("sort_asc", True)

        self._sort_by = sort_by
        self._sort_asc = sort_asc
        self.clear()
        self.move_cursor(row=0, animate=False)
        items = self._repo.list(
            status=filter_status,
            category=filter_category,
            keyword=filter_keyword,
            limit=page_size,
            offset=page * page_size,
            sort_by=sort_by,
            sort_asc=sort_asc,
        )
        now = datetime.now()
        for item in items:
            age_str = f"{(now - item.created_at).days}d" if item.created_at else "-"
            self.add_row(
                str(item.id),
                item.category or "-",
                truncate_title(item.title, self._config.get_title_truncate_length()),
                colorize_status(item.status, self._color_config),
                colorize_priority(item.priority, self._color_config),
                age_str,
                key=str(item.id),
            )
        super().refresh()
        if not items:
            self._clear_preview()

    @property
    def selected_item_id(self) -> Optional[int]:
        if self.row_count == 0:
            return None
        try:
            row_key, _ = self.coordinate_to_cell_key(self.cursor_coordinate)
            return int(row_key.value)
        except Exception:
            return None

    def _clear_preview(self) -> None:
        self._preview_title.update("")
        self._preview_desc.update("")

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.row_key is None:
            return
        try:
            item_id = int(str(event.row_key.value))
        except (ValueError, TypeError):
            return
        item = self._repo.get(item_id)
        if item:
            self._preview_title.update(item.title or "")
            self._preview_desc.update(item.description or "(No description)")
        else:
            self._clear_preview()

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        col_label = str(event.label).rstrip(" \u2191\u2193").strip()
        sort_field = COL_TO_SORT.get(col_label)
        if sort_field is None:
            return
        if self._sort_by == sort_field:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_by = sort_field
            self._sort_asc = True
        self._update_column_labels()
        if self._on_sort_changed:
            self._on_sort_changed(self._sort_by, self._sort_asc)

    def _update_column_labels(self) -> None:
        base_labels = {
            "ID": "ID",
            "Title": "Title",
            "Status": "Status",
            "Category": "Category",
            "Priority": "Priority",
            "Age": "Age",
        }
        sort_col = {v: k for k, v in COL_TO_SORT.items()}.get(self._sort_by)
        for col_name, col_key in self._col_keys.items():
            label = base_labels[col_name]
            if col_name == sort_col:
                label += " \u2191" if self._sort_asc else " \u2193"
            self.columns[col_key].label = label
        super().refresh()
