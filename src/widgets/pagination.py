"""Pagination utilities for DRY page calculation."""


def calc_total_pages(total_count: int, page_size: int) -> int:
    """Return total pages; minimum 1."""
    return max(1, (total_count + page_size - 1) // page_size)


def clamp_page(page: int, total_pages: int) -> int:
    """Clamp page to valid range [0, total_pages-1]."""
    return max(0, min(page, total_pages - 1))
