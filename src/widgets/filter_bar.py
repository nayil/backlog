"""FilterBar widget: Status and Category Select dropdowns."""

from __future__ import annotations

from typing import Optional

from textual.containers import Horizontal
from textual.widgets import Select

from models import Status


class FilterBar(Horizontal):
    """Horizontal container with Status and Category Select widgets."""

    def __init__(
        self,
        categories: list[str],
        filter_status: Optional[Status] = None,
        filter_category: Optional[str] = None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._categories = list(categories)
        self._filter_status = filter_status
        self._filter_category = filter_category

    def compose(self):
        status_val = self._filter_status.value if self._filter_status else "all"
        cat_val = self._filter_category or "all"
        status_options = [("All Status", "all")] + [
            (s.value.replace("_", " ").capitalize(), s.value) for s in Status
        ]
        cat_options = [("All Categories", "all")] + [(c, c) for c in self._categories]
        yield Select(
            status_options,
            value=status_val,
            id="sel-filter-status",
        )
        yield Select(
            cat_options,
            value=cat_val,
            id="sel-filter-category",
        )

    def set_categories(self, categories: list[str]) -> None:
        """Update category options. Call after mount when categories change."""
        self._categories = list(categories)
        try:
            sel = self.query_one("#sel-filter-category", Select)
            sel.set_options([("All Categories", "all")] + [(c, c) for c in self._categories])
        except Exception:
            pass  # Widget not mounted yet
