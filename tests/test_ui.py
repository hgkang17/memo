from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QTextCursor  # noqa: E402
from PySide6.QtWidgets import QApplication, QFrame, QToolButton  # noqa: E402

from memo_widget.application import MemoApplication  # noqa: E402


class MemoWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.qt_app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.controller = MemoApplication(
            self.qt_app,
            Path(self.temp_dir.name) / "notes.db",
        )

    def tearDown(self) -> None:
        for card in self.controller.window.cards.values():
            card._save_timer.stop()
        self.controller.window._geometry_timer.stop()
        self.controller.window._force_close = True
        self.controller.window.close()
        if self.controller.tray is not None:
            self.controller.tray.hide()
        self.controller.repository.close()
        self.temp_dir.cleanup()

    def test_completion_changes_state_and_persists(self) -> None:
        card = next(iter(self.controller.window.cards.values()))
        card.title_edit.setText("배포 전 확인")
        card.editor.setPlainText("체크리스트")

        card.complete_check.setChecked(True)
        card.save_now()
        loaded = self.controller.repository.get_note(card.note.id)

        self.assertTrue(card.editor.isReadOnly())
        self.assertFalse(card.highlight_button.isEnabled())
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertTrue(loaded.completed)
        self.assertEqual(loaded.title, "배포 전 확인")

    def test_new_note_is_added_to_the_same_window(self) -> None:
        board = self.controller.window
        before = len(board.cards)

        created = self.controller.create_note()

        self.assertIs(self.controller.window, board)
        self.assertEqual(len(board.cards), before + 1)
        self.assertIn(created.note.id, board.cards)
        self.assertIs(board.cards[created.note.id], created)

    def test_highlight_is_stored_as_rich_text(self) -> None:
        card = next(iter(self.controller.window.cards.values()))
        card.editor.setPlainText("중요한 부분")
        cursor = card.editor.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        card.editor.setTextCursor(cursor)

        card.apply_highlight("#FFF176")
        card.save_now()
        loaded = self.controller.repository.get_note(card.note.id)

        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertIn("background-color:#fff176", loaded.content_html.lower())

    def test_window_geometry_uses_shared_settings(self) -> None:
        self.controller.window.resize(510, 700)

        self.controller.window.save_window_state()

        self.assertEqual(self.controller.repository.get_setting("window_width"), "510")
        self.assertEqual(self.controller.repository.get_setting("window_height"), "700")

    def test_each_card_height_can_be_changed_and_persisted(self) -> None:
        card = next(iter(self.controller.window.cards.values()))
        original = self.controller.repository.get_note(card.note.id)
        assert original is not None

        card.set_card_height(372, persist=True)
        loaded = self.controller.repository.get_note(card.note.id)

        self.assertEqual(card.height(), 372)
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded.card_height, 372)
        self.assertEqual(loaded.updated_at, original.updated_at)

    def test_normal_window_type_is_used_without_topmost_by_default(self) -> None:
        self.assertFalse(self.controller.always_on_top)
        flags = self.controller.window.windowFlags()
        self.assertEqual(
            flags & Qt.WindowType.WindowType_Mask,
            Qt.WindowType.Window,
        )
        self.assertFalse(flags & Qt.WindowType.WindowStaysOnTopHint)

    def test_card_format_controls_use_remembered_color_popup_buttons(self) -> None:
        card = next(iter(self.controller.window.cards.values()))
        card.editor.setPlainText("색상 적용")
        cursor = card.editor.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        card.editor.setTextCursor(cursor)

        card._select_highlight_color("#A7F3D0")
        card.save_now()
        loaded = self.controller.repository.get_note(card.note.id)

        self.assertEqual(
            card.highlight_button.popupMode(),
            QToolButton.ToolButtonPopupMode.MenuButtonPopup,
        )
        self.assertIsNone(card.findChild(QFrame, "cardToolbar"))
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertIn("#a7f3d0", loaded.content_html.lower())

    def test_checklist_line_is_checked_styled_and_persisted(self) -> None:
        card = next(iter(self.controller.window.cards.values()))
        card.editor.setPlainText("첫 번째 할 일\n두 번째 할 일")
        cursor = card.editor.textCursor()
        cursor.setPosition(0)
        card.editor.setTextCursor(cursor)

        card.editor.toggle_current_check_item()
        first_block = card.editor.document().findBlockByNumber(0)
        card.editor.toggle_block_checked(first_block)
        card.save_now()
        loaded = self.controller.repository.get_note(card.note.id)

        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded.checklist_json, '{"0":true}')
        self.assertIn("line-through", loaded.content_html.lower())

    def test_card_opacity_persists_without_changing_modified_time(self) -> None:
        card = next(iter(self.controller.window.cards.values()))
        original = self.controller.repository.get_note(card.note.id)
        assert original is not None

        card.set_card_opacity(70)
        loaded = self.controller.repository.get_note(card.note.id)

        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded.opacity, 70)
        self.assertEqual(loaded.updated_at, original.updated_at)

    def test_title_index_menu_lists_current_note_titles(self) -> None:
        first = next(iter(self.controller.window.cards.values()))
        first.title_edit.setText("첫 번째 메모")
        second = self.controller.create_note()
        second.title_edit.setText("두 번째 메모")

        self.controller.window._populate_title_index_menu()
        labels = [action.text() for action in self.controller.window.title_index_menu.actions()]

        self.assertIn("첫 번째 메모", labels)
        self.assertIn("두 번째 메모", labels)

    def test_editor_has_no_placeholder_copy(self) -> None:
        card = next(iter(self.controller.window.cards.values()))
        self.assertEqual(card.editor.placeholderText(), "")

    def test_show_window_restores_minimized_window(self) -> None:
        window = self.controller.window
        window.showMinimized()
        self.qt_app.processEvents()

        window.show_window()
        self.qt_app.processEvents()

        self.assertFalse(window.windowState() & Qt.WindowState.WindowMinimized)

    def test_created_and_updated_timestamps_are_visible(self) -> None:
        card = next(iter(self.controller.window.cards.values()))

        before = card.timestamp_label.text()
        card.title_edit.setText("시간 기록 확인")
        card.save_now()
        loaded = self.controller.repository.get_note(card.note.id)

        self.assertIn("작성", before)
        self.assertIn("수정", before)
        self.assertIn("작성", card.timestamp_label.text())
        self.assertIn("수정", card.timestamp_label.text())
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertTrue(loaded.created_at)
        self.assertTrue(loaded.updated_at)

    def test_closing_without_edits_does_not_change_modified_time(self) -> None:
        card = next(iter(self.controller.window.cards.values()))
        original = self.controller.repository.get_note(card.note.id)
        assert original is not None

        self.controller.window.save_all()
        reloaded = self.controller.repository.get_note(card.note.id)

        self.assertIsNotNone(reloaded)
        assert reloaded is not None
        self.assertEqual(reloaded.updated_at, original.updated_at)


if __name__ == "__main__":
    unittest.main()
