from __future__ import annotations

import sqlite3
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(slots=True)
class Note:
    id: int
    title: str = ""
    content_html: str = ""
    # Kept for backward-compatible database reads; card rendering now uses a
    # fixed white active surface and a gray completed surface.
    color: str = "#FFFFFF"
    completed: bool = False
    always_on_top: bool = False
    visible: bool = True
    x: int = 160
    y: int = 140
    width: int = 380
    height: int = 460
    card_height: int = 238
    checklist_json: str = "{}"
    opacity: int = 100
    created_at: str = ""
    updated_at: str = ""


class NoteRepository:
    """Small SQLite repository with explicit, testable note persistence."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.database_path)
        self.connection.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL DEFAULT '',
                content_html TEXT NOT NULL DEFAULT '',
                color TEXT NOT NULL DEFAULT '#FFFFFF',
                completed INTEGER NOT NULL DEFAULT 0,
                always_on_top INTEGER NOT NULL DEFAULT 0,
                visible INTEGER NOT NULL DEFAULT 1,
                x INTEGER NOT NULL DEFAULT 160,
                y INTEGER NOT NULL DEFAULT 140,
                width INTEGER NOT NULL DEFAULT 380,
                height INTEGER NOT NULL DEFAULT 460,
                card_height INTEGER NOT NULL DEFAULT 238,
                checklist_json TEXT NOT NULL DEFAULT '{}',
                opacity INTEGER NOT NULL DEFAULT 100,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        columns = {
            str(row["name"])
            for row in self.connection.execute("PRAGMA table_info(notes)").fetchall()
        }
        if "card_height" not in columns:
            self.connection.execute(
                "ALTER TABLE notes ADD COLUMN card_height INTEGER NOT NULL DEFAULT 238"
            )
        if "checklist_json" not in columns:
            self.connection.execute(
                "ALTER TABLE notes ADD COLUMN checklist_json TEXT NOT NULL DEFAULT '{}'"
            )
        if "opacity" not in columns:
            self.connection.execute(
                "ALTER TABLE notes ADD COLUMN opacity INTEGER NOT NULL DEFAULT 100"
            )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    def create_note(self, *, x: int = 160, y: int = 140) -> Note:
        timestamp = _now()
        cursor = self.connection.execute(
            """
            INSERT INTO notes (color, x, y, created_at, updated_at)
            VALUES ('#FFFFFF', ?, ?, ?, ?)
            """,
            (x, y, timestamp, timestamp),
        )
        self.connection.commit()
        return Note(id=int(cursor.lastrowid), x=x, y=y, created_at=timestamp, updated_at=timestamp)

    def list_notes(self) -> list[Note]:
        rows = self.connection.execute(
            "SELECT * FROM notes ORDER BY completed ASC, updated_at DESC, id DESC"
        ).fetchall()
        return [self._from_row(row) for row in rows]

    def get_note(self, note_id: int) -> Note | None:
        row = self.connection.execute(
            "SELECT * FROM notes WHERE id = ?", (note_id,)
        ).fetchone()
        return self._from_row(row) if row else None

    def save_note(self, note: Note) -> Note:
        saved = replace(note, updated_at=_now())
        self.connection.execute(
            """
            UPDATE notes
               SET title = ?, content_html = ?, color = ?, completed = ?,
                   always_on_top = ?, visible = ?, x = ?, y = ?, width = ?,
                   height = ?, card_height = ?, checklist_json = ?, opacity = ?,
                   updated_at = ?
             WHERE id = ?
            """,
            (
                saved.title,
                saved.content_html,
                saved.color,
                int(saved.completed),
                int(saved.always_on_top),
                int(saved.visible),
                saved.x,
                saved.y,
                saved.width,
                saved.height,
                saved.card_height,
                saved.checklist_json,
                saved.opacity,
                saved.updated_at,
                saved.id,
            ),
        )
        self.connection.commit()
        return saved

    def delete_note(self, note_id: int) -> None:
        self.connection.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        self.connection.commit()

    def save_card_height(self, note_id: int, card_height: int) -> None:
        """Persist layout-only state without changing the note's modified time."""
        self.connection.execute(
            "UPDATE notes SET card_height = ? WHERE id = ?",
            (card_height, note_id),
        )
        self.connection.commit()

    def save_card_opacity(self, note_id: int, opacity: int) -> None:
        """Persist appearance-only state without changing the modified time."""
        self.connection.execute(
            "UPDATE notes SET opacity = ? WHERE id = ?",
            (opacity, note_id),
        )
        self.connection.commit()

    def get_setting(self, key: str, default: str | None = None) -> str | None:
        row = self.connection.execute(
            "SELECT value FROM app_settings WHERE key = ?", (key,)
        ).fetchone()
        return str(row["value"]) if row else default

    def set_setting(self, key: str, value: str | int | bool) -> None:
        stored = "1" if value is True else "0" if value is False else str(value)
        self.connection.execute(
            """
            INSERT INTO app_settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, stored),
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Note:
        return Note(
            id=int(row["id"]),
            title=str(row["title"]),
            content_html=str(row["content_html"]),
            color=str(row["color"]),
            completed=bool(row["completed"]),
            always_on_top=bool(row["always_on_top"]),
            visible=bool(row["visible"]),
            x=int(row["x"]),
            y=int(row["y"]),
            width=int(row["width"]),
            height=int(row["height"]),
            card_height=int(row["card_height"]),
            checklist_json=str(row["checklist_json"]),
            opacity=int(row["opacity"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )
