"""Render a deterministic single-window preview for visual review."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication  # noqa: E402
from PySide6.QtGui import QTextCursor  # noqa: E402

from memo_widget.application import MemoApplication  # noqa: E402


def main() -> int:
    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory() as directory:
        controller = MemoApplication(app, Path(directory) / "preview.db")
        board = controller.window
        board.resize(470, 860)

        completed = next(iter(board.cards.values()))
        completed.title_edit.setText("자료 전달")
        completed.editor.setPlainText("검토가 끝난 파일을 공유했습니다.")
        completed.complete_check.setChecked(True)
        completed.set_card_height(220, persist=False)

        second = controller.create_note()
        second.title_edit.setText("장보기")
        second.editor.setPlainText("우유, 원두, 키친타월")
        second.set_card_height(210, persist=False)
        second.set_card_opacity(85)

        active = controller.create_note()
        active.title_edit.setText("오늘 꼭 끝낼 일")
        active.editor.setHtml(
            "<p>회의자료 정리하고 "
            '<span style="background-color:#fff176">수정사항</span> 반영하기</p>'
            '<p><span style="color:#225ea8">오후 3시</span> 전에 전달</p>'
        )
        active.set_card_height(258, persist=False)
        cursor = active.editor.textCursor()
        cursor.setPosition(0)
        active.editor.setTextCursor(cursor)
        active.editor.toggle_current_check_item()
        active.editor.toggle_block_checked(active.editor.document().findBlockByNumber(0))

        app.processEvents()
        output = Path(".impeccable/review/window.png")
        output.parent.mkdir(parents=True, exist_ok=True)
        saved = board.grab().save(str(output))

        for card in board.cards.values():
            card._save_timer.stop()
        board._geometry_timer.stop()
        board._force_close = True
        board.close()
        if controller.tray is not None:
            controller.tray.hide()
        controller.repository.close()

    print(f"saved={saved} path={output}")
    return 0 if saved else 1


if __name__ == "__main__":
    raise SystemExit(main())
