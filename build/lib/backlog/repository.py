"""Backlog data storage layer using SQLite."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from models import BacklogItem, Priority, Status


class BacklogRepository:
    """SQLite-backed repository for BacklogItem CRUD operations."""

    def __init__(self, db_path: str = "backlog.db") -> None:
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._create_table()
        self._migrate_schema()
        self._purge_expired()

    def _create_table(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS backlog_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'todo',
                category TEXT NOT NULL DEFAULT '',
                priority TEXT NOT NULL DEFAULT 'medium',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                deleted_at TEXT DEFAULT NULL,
                expires_at TEXT DEFAULT NULL
            )
            """
        )
        self._conn.commit()

    def _migrate_schema(self) -> None:
        """Add new columns to existing tables if they are missing (backward compat)."""
        existing_columns = {
            row[1]
            for row in self._conn.execute("PRAGMA table_info(backlog_items)").fetchall()
        }
        for column, definition in [
            ("deleted_at", "TEXT DEFAULT NULL"),
            ("expires_at", "TEXT DEFAULT NULL"),
        ]:
            if column not in existing_columns:
                self._conn.execute(
                    f"ALTER TABLE backlog_items ADD COLUMN {column} {definition}"
                )
        self._conn.commit()

    def _row_to_item(self, row: sqlite3.Row) -> BacklogItem:
        keys = row.keys()
        return BacklogItem(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            status=Status(row["status"]),
            category=row["category"],
            priority=Priority(row["priority"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            deleted_at=datetime.fromisoformat(row["deleted_at"]) if "deleted_at" in keys and row["deleted_at"] else None,
            expires_at=datetime.fromisoformat(row["expires_at"]) if "expires_at" in keys and row["expires_at"] else None,
        )

    def create(self, item: BacklogItem) -> BacklogItem:
        now = datetime.now()
        cursor = self._conn.execute(
            """
            INSERT INTO backlog_items (title, description, status, category, priority, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.title,
                item.description,
                item.status.value,
                item.category,
                item.priority.value,
                (item.created_at or now).isoformat(),
                (item.updated_at or now).isoformat(),
            ),
        )
        self._conn.commit()
        item.id = cursor.lastrowid
        return item

    def get(self, item_id: int, include_deleted: bool = False) -> Optional[BacklogItem]:
        if include_deleted:
            query = "SELECT * FROM backlog_items WHERE id = ?"
        else:
            query = "SELECT * FROM backlog_items WHERE id = ? AND deleted_at IS NULL"
        row = self._conn.execute(query, (item_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_item(row)

    def _build_where_clause(
        self,
        status: Optional[Status] = None,
        category: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> tuple[str, List[Any]]:
        """Build the WHERE clause and params for active (non-deleted) items."""
        clause = "deleted_at IS NULL"
        params: List[Any] = []

        if status is not None:
            clause += " AND status = ?"
            params.append(status.value)
        if category is not None:
            clause += " AND category = ?"
            params.append(category)
        if keyword is not None:
            clause += " AND (title LIKE ? OR description LIKE ?)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])

        return clause, params

    def _build_trash_where_clause(
        self,
        keyword: Optional[str] = None,
    ) -> tuple[str, List[Any]]:
        """Build the WHERE clause and params for trash (soft-deleted, non-expired) items."""
        now = datetime.now().isoformat()
        clause = "deleted_at IS NOT NULL AND (expires_at IS NULL OR expires_at > ?)"
        params: List[Any] = [now]

        if keyword is not None:
            clause += " AND (title LIKE ? OR description LIKE ?)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])

        return clause, params

    def list(
        self,
        status: Optional[Status] = None,
        category: Optional[str] = None,
        keyword: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        sort_by: Optional[str] = None,
        sort_asc: bool = True,
    ) -> List[BacklogItem]:
        where, params = self._build_where_clause(status, category, keyword)

        _VALID_SORT_BY = {"priority", "category", "status", "age"}
        if sort_by not in _VALID_SORT_BY:
            order_clause = "id"
        elif sort_by == "priority":
            order_clause = "CASE priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 WHEN 'low' THEN 2 ELSE 3 END"
        elif sort_by == "status":
            order_clause = "CASE status WHEN 'in_progress' THEN 0 WHEN 'todo' THEN 1 WHEN 'done' THEN 2 ELSE 3 END"
        elif sort_by == "category":
            order_clause = "category"
        elif sort_by == "age":
            order_clause = "created_at"

        direction = "ASC" if sort_asc else "DESC"
        query = f"SELECT * FROM backlog_items WHERE {where} ORDER BY {order_clause} {direction}"

        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

        rows = self._conn.execute(query, params).fetchall()
        return [self._row_to_item(row) for row in rows]

    def count(
        self,
        status: Optional[Status] = None,
        category: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> int:
        """Return the total count of active items matching the given filters."""
        where, params = self._build_where_clause(status, category, keyword)
        query = f"SELECT COUNT(*) FROM backlog_items WHERE {where}"
        return self._conn.execute(query, params).fetchone()[0]

    def update(self, item_id: int, **fields: Any) -> Optional[BacklogItem]:
        existing = self.get(item_id)
        if existing is None:
            return None

        # Safety note: column names are safe from SQL injection because they are
        # checked against this hard-coded whitelist before being interpolated.
        allowed = {"title", "description", "status", "category", "priority"}
        updates: List[str] = []
        params: List[Any] = []

        for key, value in fields.items():
            if key not in allowed:
                continue
            if key == "status" and isinstance(value, Status):
                value = value.value
            elif key == "priority" and isinstance(value, Priority):
                value = value.value
            updates.append(f"{key} = ?")
            params.append(value)

        if not updates:
            return existing

        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(item_id)

        self._conn.execute(
            f"UPDATE backlog_items SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        self._conn.commit()
        return self.get(item_id)

    def delete(self, item_id: int) -> bool:
        """Soft-delete: set deleted_at=now and expires_at=now+180 days."""
        now = datetime.now()
        expires = now + timedelta(days=180)
        cursor = self._conn.execute(
            "UPDATE backlog_items SET deleted_at = ?, expires_at = ? WHERE id = ? AND deleted_at IS NULL",
            (now.isoformat(), expires.isoformat(), item_id),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def restore(self, item_id: int) -> Optional[BacklogItem]:
        """Restore a soft-deleted item by clearing deleted_at and expires_at."""
        cursor = self._conn.execute(
            "UPDATE backlog_items SET deleted_at = NULL, expires_at = NULL WHERE id = ? AND deleted_at IS NOT NULL",
            (item_id,),
        )
        self._conn.commit()
        if cursor.rowcount == 0:
            return None
        return self.get(item_id)

    def hard_delete(self, item_id: int) -> bool:
        """Permanently delete a record from the database."""
        cursor = self._conn.execute(
            "DELETE FROM backlog_items WHERE id = ?", (item_id,)
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def list_trash(
        self,
        keyword: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[BacklogItem]:
        """Return soft-deleted items that have not yet expired, newest first."""
        where, params = self._build_trash_where_clause(keyword)
        query = f"SELECT * FROM backlog_items WHERE {where} ORDER BY deleted_at DESC"

        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

        rows = self._conn.execute(query, params).fetchall()
        return [self._row_to_item(row) for row in rows]

    def count_trash(
        self,
        keyword: Optional[str] = None,
    ) -> int:
        """Return the total count of trash items matching the given keyword filter."""
        where, params = self._build_trash_where_clause(keyword)
        query = f"SELECT COUNT(*) FROM backlog_items WHERE {where}"
        return self._conn.execute(query, params).fetchone()[0]

    def _purge_expired(self) -> None:
        """Delete records whose expires_at is in the past."""
        now = datetime.now().isoformat()
        self._conn.execute(
            "DELETE FROM backlog_items WHERE expires_at IS NOT NULL AND expires_at <= ?",
            (now,),
        )
        self._conn.commit()

    def transition_status(
        self, item_id: int, new_status: Status
    ) -> Optional[BacklogItem]:
        """Transition item status with validation.

        Allowed transitions:
          TODO -> IN_PROGRESS
          IN_PROGRESS -> DONE
          IN_PROGRESS -> TODO  (back to todo)
          DONE -> IN_PROGRESS  (reopen)
        """
        item = self.get(item_id)
        if item is None:
            return None

        valid_transitions: Dict[Status, set] = {
            Status.TODO: {Status.IN_PROGRESS},
            Status.IN_PROGRESS: {Status.DONE, Status.TODO},
            Status.DONE: {Status.IN_PROGRESS},
        }

        if new_status not in valid_transitions.get(item.status, set()):
            raise ValueError(
                f"Invalid status transition: {item.status.value} -> {new_status.value}"
            )

        return self.update(item_id, status=new_status)

    def get_categories(self) -> List[str]:
        rows = self._conn.execute(
            "SELECT DISTINCT category FROM backlog_items WHERE category != '' AND deleted_at IS NULL ORDER BY category"
        ).fetchall()
        return [row["category"] for row in rows]

    def get_stats(self, category: Optional[str] = None) -> Dict[str, Any]:
        base = "FROM backlog_items WHERE deleted_at IS NULL"
        params: List[Any] = []
        if category is not None:
            base += " AND category = ?"
            params.append(category)

        total = self._conn.execute(
            f"SELECT COUNT(*) as cnt {base}", params
        ).fetchone()["cnt"]

        stats: Dict[str, Any] = {"total": total, "by_status": {}, "by_priority": {}}

        for s in Status:
            count = self._conn.execute(
                f"SELECT COUNT(*) as cnt {base} AND status = ?",
                [*params, s.value],
            ).fetchone()["cnt"]
            stats["by_status"][s.value] = count

        for p in Priority:
            count = self._conn.execute(
                f"SELECT COUNT(*) as cnt {base} AND priority = ?",
                [*params, p.value],
            ).fetchone()["cnt"]
            stats["by_priority"][p.value] = count

        return stats

    def __enter__(self) -> "BacklogRepository":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def close(self) -> None:
        self._conn.close()
