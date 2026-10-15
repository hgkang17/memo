from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from memo_widget.repository import NoteRepository


class NoteRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repository = NoteRepository(Path(self.temp_dir.name) / "notes.db")

    def tearDown(self) -> None:
        self.repository.close()
        self.temp_dir.cleanup()

    def test_create_save_and_reload_rich_note(self) -> None:
        note = self.repository.create_note(x=25, y=40)
        note.title = "오늘 할 일"
        note.content_html = "<p><span style='background:#fff176'>보고서</span></p>"
        note.completed = True
        note.color = "#CFEBD8"
        note.width = 420
        note.card_height = 364
        note.checklist_json = '{"0":true}'
        note.opacity = 70
        saved = self.repository.save_note(note)

        loaded = self.repository.get_note(saved.id)

        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded.title, "오늘 할 일")
        self.assertIn("background:#fff176", loaded.content_html)
        self.assertTrue(loaded.completed)
        self.assertEqual(loaded.color, "#CFEBD8")
        self.assertEqual((loaded.x, loaded.y, loaded.width), (25, 40, 420))
        self.assertEqual(loaded.card_height, 364)
        self.assertEqual(loaded.checklist_json, '{"0":true}')
        self.assertEqual(loaded.opacity, 70)

    def test_delete_removes_only_requested_note(self) -> None:
        first = self.repository.create_note()
        second = self.repository.create_note()

        self.repository.delete_note(first.id)

        self.assertIsNone(self.repository.get_note(first.id))
        self.assertIsNotNone(self.repository.get_note(second.id))

    def test_existing_database_gains_new_card_columns(self) -> None:
        database_path = self.repository.database_path
        self.repository.close()
        connection = sqlite3.connect(database_path)
        connection.execute("ALTER TABLE notes DROP COLUMN card_height")
        connection.execute("ALTER TABLE notes DROP COLUMN checklist_json")
        connection.execute("ALTER TABLE notes DROP COLUMN opacity")
        connection.commit()
        connection.close()

        self.repository = NoteRepository(database_path)
        created = self.repository.create_note()

        self.assertEqual(created.card_height, 238)
        loaded = self.repository.get_note(created.id)
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded.card_height, 238)
        self.assertEqual(loaded.checklist_json, "{}")
        self.assertEqual(loaded.opacity, 100)


if __name__ == "__main__":
    unittest.main()
