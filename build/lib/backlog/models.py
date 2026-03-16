"""Backlog Item data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class Status(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class Priority(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class BacklogItem:
    title: str
    description: str = ""
    status: Status = Status.TODO
    category: str = ""
    priority: Priority = Priority.MEDIUM
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        now = datetime.now()
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "category": self.category,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }

    @staticmethod
    def _safe_enum(enum_cls, value, default):
        """Return the enum member for *value*, falling back to *default*."""
        if value is None:
            return default
        try:
            return enum_cls(value)
        except ValueError:
            return default

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BacklogItem:
        return cls(
            id=data.get("id"),
            title=data["title"],
            description=data.get("description", ""),
            status=cls._safe_enum(Status, data.get("status"), Status.TODO),
            category=data.get("category", ""),
            priority=cls._safe_enum(Priority, data.get("priority"), Priority.MEDIUM),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            deleted_at=datetime.fromisoformat(data["deleted_at"]) if data.get("deleted_at") else None,
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
        )
