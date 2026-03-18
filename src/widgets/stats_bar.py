"""StatsBar widget for displaying backlog statistics."""

from textual.widgets import Static


class StatsBar(Static):
    """Static widget displaying total count, by_status, and page info."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__("", *args, **kwargs)

    def update_stats(
        self,
        total_count: int,
        by_status: dict,
        current_page: int,
        total_pages: int,
    ) -> None:
        text = (
            f" Total: {total_count}  |  "
            f"Todo: {by_status.get('todo', 0)}  |  "
            f"In Progress: {by_status.get('in_progress', 0)}  |  "
            f"Done: {by_status.get('done', 0)}  |  "
            f"Page {current_page}/{total_pages}  [N]ext  [P]rev"
        )
        self.update(text)
