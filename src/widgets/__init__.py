"""Widgets package."""

from .pagination import calc_total_pages, clamp_page
from .stats_bar import StatsBar

__all__ = ["calc_total_pages", "clamp_page", "StatsBar"]
