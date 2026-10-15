from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QPoint, QRect, QSize, QStandardPaths, Qt, QTimer, Signal
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QBrush,
    QColor,
    QFont,
    QIcon,
    QKeySequence,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QTextBlockUserData,
    QTextCharFormat,
    QTextCursor,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizeGrip,
    QSizePolicy,
    QStyle,
    QSystemTrayIcon,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .repository import Note, NoteRepository
from .updater import UpdateManager
from .version import APP_VERSION


HIGHLIGHT_COLORS = {
    "레몬": "#FFF176",
    "민트": "#A7F3D0",
    "코랄": "#FDB5A8",
    "블루": "#A9D6FF",
}

TEXT_COLORS = {
    "먹색": "#2D2A24",
    "레드": "#A33A32",
    "블루": "#225EA8",
    "그린": "#266A4A",
    "회색": "#6B6A64",
}

DEFAULT_CARD_HEIGHT = 238
MIN_CARD_HEIGHT = 210
MAX_CARD_HEIGHT = 720
CARD_HEIGHT_STEP = 24


def _format_timestamp(value: str) -> str:
    if not value:
        return "기록 없음"
    try:
        moment = datetime.fromisoformat(value)
        if moment.tzinfo is not None:
            moment = moment.astimezone()
        return moment.strftime("%Y.%m.%d %H:%M:%S")
    except ValueError:
        return value


def _swatch_icon(color: str, *, crossed: bool = False) -> QIcon:
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor("#4A463D"), 1))
    painter.setBrush(QBrush(QColor(color)))
    painter.drawRoundedRect(4, 4, 16, 16, 4, 4)
    if crossed:
        painter.setPen(QPen(QColor("#9B3D36"), 2))
        painter.drawLine(5, 19, 19, 5)
    painter.end()
    return QIcon(pixmap)


def _format_icon(kind: str, color: str | None) -> QIcon:
    """Draw compact, consistent formatting icons without font-symbol glyphs."""
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    ink = QColor("#38352E")

    if kind == "highlight":
        painter.setPen(QPen(ink, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(8, 15, 16, 7)
        painter.setPen(QPen(ink, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(7, 16, 10, 18)
        painter.drawLine(15, 6, 18, 9)
        swatch = QColor(color or "#FFFFFF")
        painter.setPen(QPen(swatch, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(5, 20, 19, 20)
        if color is None:
            painter.setPen(QPen(QColor("#A33A32"), 1.7))
            painter.drawLine(5, 21, 19, 17)
    elif kind == "text":
        font = QFont("Segoe UI Variable Text", 11)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(ink)
        painter.drawText(QRect(3, 0, 18, 18), Qt.AlignmentFlag.AlignCenter, "A")
        painter.setPen(
            QPen(QColor(color or "#2D2A24"), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        )
        painter.drawLine(5, 20, 19, 20)
    else:
        box = QRect(4, 4, 16, 16)
        painter.setPen(QPen(ink, 1.6))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(box, 4, 4)
        painter.setPen(
            QPen(
                QColor("#2F4A42"),
                2,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )
        painter.drawLine(7, 12, 10, 15)
        painter.drawLine(10, 15, 17, 8)

    painter.end()
    return QIcon(pixmap)


def _app_icon() -> QIcon:
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addRoundedRect(7, 6, 50, 52, 11, 11)
    painter.fillPath(path, QColor("#FFE16F"))
    painter.setPen(QPen(QColor("#39352B"), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawLine(18, 23, 45, 23)
    painter.drawLine(18, 33, 40, 33)
    painter.drawLine(18, 43, 34, 43)
    painter.end()
    return QIcon(pixmap)


class DragHeader(QFrame):
    """Frameless title bar that drags the single board window."""

    def __init__(self, window: "MemoBoardWindow") -> None:
        super().__init__(window)
        self._window = window
        self._drag_offset: QPoint | None = None
        self.setObjectName("dragHeader")
        self.setCursor(Qt.CursorShape.SizeAllCursor)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self._window.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self._window.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_offset = None
        super().mouseReleaseEvent(event)


class CardResizeHandle(QWidget):
    """Mouse- and keyboard-accessible vertical resize handle for one card."""

    def __init__(self, card: "MemoCard") -> None:
        super().__init__(card)
        self.card = card
        self._press_y: float | None = None
        self._press_height = DEFAULT_CARD_HEIGHT
        self.setObjectName("cardResizeHandle")
        self.setFixedHeight(18)
        self.setCursor(Qt.CursorShape.SizeVerCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setToolTip("위아래로 드래그해 메모 높이 조절 · 더블클릭해 기본 높이")
        self.setAccessibleName("메모 높이 조절")
        self.setAccessibleDescription("위아래 화살표 키 또는 마우스 드래그로 높이를 조절합니다")

    def paintEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor("#807B72") if not self.hasFocus() else QColor("#2F4A42")
        if self.card.note.completed:
            color = QColor("#77746D")
        painter.setPen(
            QPen(
                color,
                2,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )
        center_x = self.width() // 2
        center_y = self.height() // 2
        painter.drawLine(center_x - 18, center_y, center_x + 18, center_y)
        painter.end()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_y = event.globalPosition().y()
            self._press_height = self.card.height()
            self.setFocus(Qt.FocusReason.MouseFocusReason)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._press_y is not None and event.buttons() & Qt.MouseButton.LeftButton:
            delta = round(event.globalPosition().y() - self._press_y)
            self.card.set_card_height(self._press_height + delta, persist=False)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._press_y is not None and event.button() == Qt.MouseButton.LeftButton:
            self._press_y = None
            self.card.commit_card_height()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.card.set_card_height(DEFAULT_CARD_HEIGHT, persist=True)
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        if event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down):
            direction = -1 if event.key() == Qt.Key.Key_Up else 1
            step = CARD_HEIGHT_STEP * (2 if event.modifiers() & Qt.KeyboardModifier.ShiftModifier else 1)
            self.card.set_card_height(self.card.height() + direction * step, persist=True)
            event.accept()
            return
        if event.key() == Qt.Key.Key_Home:
            self.card.set_card_height(DEFAULT_CARD_HEIGHT, persist=True)
            event.accept()
            return
        super().keyPressEvent(event)


class ChecklistBlockData(QTextBlockUserData):
    def __init__(self, checked: bool = False) -> None:
        super().__init__()
        self.checked = checked


class ChecklistTextEdit(QTextEdit):
    """Rich-text editor with clickable, persisted per-paragraph checkboxes."""

    checklist_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setViewportMargins(0, 0, 0, 0)
        self._ensure_block_gutters()

    def setPlainText(self, text: str) -> None:
        super().setPlainText(text)
        self._ensure_block_gutters()

    def setHtml(self, text: str) -> None:
        super().setHtml(text)
        self._ensure_block_gutters()

    def keyPressEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().keyPressEvent(event)
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._ensure_block_gutters()

    def insertFromMimeData(self, source) -> None:  # type: ignore[no-untyped-def]
        super().insertFromMimeData(source)
        self._ensure_block_gutters()

    def _ensure_block_gutters(self) -> None:
        block = self.document().begin()
        while block.isValid():
            block_format = block.blockFormat()
            if block_format.leftMargin() < 24:
                block_format.setLeftMargin(24)
                cursor = QTextCursor(block)
                cursor.setBlockFormat(block_format)
            block = block.next()

    def toggle_current_check_item(self) -> None:
        if self.isReadOnly():
            return
        block = self.textCursor().block()
        data = block.userData()
        if isinstance(data, ChecklistBlockData):
            self._apply_checked_format(block, False)
            block.setUserData(None)
        else:
            block.setUserData(ChecklistBlockData(False))
        self.viewport().update()
        self.checklist_changed.emit()
        self.setFocus(Qt.FocusReason.ShortcutFocusReason)

    def toggle_block_checked(self, block) -> None:  # type: ignore[no-untyped-def]
        if self.isReadOnly():
            return
        data = block.userData()
        if not isinstance(data, ChecklistBlockData):
            return
        data.checked = not data.checked
        self._apply_checked_format(block, data.checked)
        self.viewport().update()
        self.checklist_changed.emit()

    def checklist_json(self) -> str:
        items: dict[str, bool] = {}
        block = self.document().begin()
        while block.isValid():
            data = block.userData()
            if isinstance(data, ChecklistBlockData):
                items[str(block.blockNumber())] = data.checked
            block = block.next()
        return json.dumps(items, ensure_ascii=False, separators=(",", ":"))

    def load_checklist_json(self, value: str) -> None:
        try:
            items = json.loads(value or "{}")
        except (TypeError, ValueError, json.JSONDecodeError):
            items = {}
        if not isinstance(items, dict):
            return
        for number, checked in items.items():
            try:
                block = self.document().findBlockByNumber(int(number))
            except (TypeError, ValueError):
                continue
            if not block.isValid():
                continue
            block.setUserData(ChecklistBlockData(bool(checked)))
            if checked:
                self._apply_checked_format(block, True)
        self.viewport().update()

    def _apply_checked_format(self, block, checked: bool) -> None:  # type: ignore[no-untyped-def]
        cursor = QTextCursor(block)
        cursor.movePosition(
            QTextCursor.MoveOperation.EndOfBlock,
            QTextCursor.MoveMode.KeepAnchor,
        )
        char_format = QTextCharFormat()
        char_format.setFontStrikeOut(checked)
        char_format.setForeground(QBrush(QColor("#85827B" if checked else "#302D25")))
        cursor.mergeCharFormat(char_format)

    def paintEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().paintEvent(event)
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        block = self.document().begin()
        while block.isValid():
            data = block.userData()
            if isinstance(data, ChecklistBlockData):
                cursor_rect = self.cursorRect(QTextCursor(block))
                box_size = 14
                top = cursor_rect.top() + max(1, (cursor_rect.height() - box_size) // 2)
                box = QRect(2, top, box_size, box_size)
                if box.bottom() >= 0 and box.top() <= self.viewport().height():
                    painter.setPen(QPen(QColor("#77736B"), 1.3))
                    painter.setBrush(QBrush(QColor("#69786F") if data.checked else QColor("#FFFFFF")))
                    painter.drawRoundedRect(box, 3, 3)
                    if data.checked:
                        painter.setPen(
                            QPen(
                                QColor("#FFFFFF"),
                                1.8,
                                Qt.PenStyle.SolidLine,
                                Qt.PenCapStyle.RoundCap,
                                Qt.PenJoinStyle.RoundJoin,
                            )
                        )
                        painter.drawLine(box.left() + 3, box.center().y(), box.left() + 6, box.bottom() - 3)
                        painter.drawLine(box.left() + 6, box.bottom() - 3, box.right() - 2, box.top() + 3)
            block = block.next()
        painter.end()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and event.position().x() <= 20:
            cursor = self.cursorForPosition(QPoint(25, round(event.position().y())))
            data = cursor.block().userData()
            if isinstance(data, ChecklistBlockData):
                self.toggle_block_checked(cursor.block())
                event.accept()
                return
        super().mousePressEvent(event)


class MemoCard(QFrame):
    delete_requested = Signal(int)
    changed = Signal(int)

    def __init__(self, controller: "MemoApplication", note: Note) -> None:
        super().__init__()
        self.controller = controller
        self.note = note
        self._ready = False
        self._dirty = False
        self._height_dirty = False
        self._highlight_color: str | None = HIGHLIGHT_COLORS["레몬"]
        self._text_color = TEXT_COLORS["먹색"]
        self.setObjectName("memoCard")

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(400)
        self._save_timer.timeout.connect(self.save_now)

        self._build_ui()
        self._load_note()
        self._ready = True
        self._apply_state_style()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        heading = QFrame()
        heading.setObjectName("cardHeading")
        heading_layout = QHBoxLayout(heading)
        heading_layout.setContentsMargins(12, 8, 8, 5)
        heading_layout.setSpacing(6)

        self.complete_check = QCheckBox("완료")
        self.complete_check.setToolTip("완료하면 이 메모가 회색으로 바뀝니다")
        self.complete_check.toggled.connect(self._completion_changed)
        heading_layout.addWidget(self.complete_check)

        self.title_edit = QLineEdit()
        self.title_edit.setObjectName("cardTitle")
        self.title_edit.setPlaceholderText("메모 제목")
        self.title_edit.setMaxLength(120)
        self.title_edit.textChanged.connect(self._content_changed)
        heading_layout.addWidget(self.title_edit, 1)

        self.checklist_button = QToolButton()
        self.checklist_button.setObjectName("formatButton")
        self.checklist_button.setIcon(_format_icon("checklist", None))
        self.checklist_button.setIconSize(QSize(22, 22))
        self.checklist_button.setFixedSize(32, 30)
        self.checklist_button.setToolTip("현재 줄에 체크박스 추가 또는 제거")
        self.checklist_button.setAccessibleName("현재 줄 체크박스 전환")
        self.checklist_button.clicked.connect(self._toggle_current_check_item)
        heading_layout.addWidget(self.checklist_button)

        self.highlight_button = QToolButton()
        self.highlight_button.setObjectName("formatButton")
        self.highlight_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.highlight_button.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.highlight_button.setMenu(self._create_highlight_menu())
        self.highlight_button.setFixedSize(38, 30)
        self.highlight_button.setIconSize(QSize(22, 22))
        self.highlight_button.setAccessibleName("형광펜")
        self.highlight_button.clicked.connect(self._apply_selected_highlight)
        heading_layout.addWidget(self.highlight_button)

        self.text_color_button = QToolButton()
        self.text_color_button.setObjectName("formatButton")
        self.text_color_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.text_color_button.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.text_color_button.setMenu(self._create_text_color_menu())
        self.text_color_button.setFixedSize(38, 30)
        self.text_color_button.setIconSize(QSize(22, 22))
        self.text_color_button.setAccessibleName("글자색")
        self.text_color_button.clicked.connect(self._apply_selected_text_color)
        heading_layout.addWidget(self.text_color_button)

        self.options_button = QToolButton()
        self.options_button.setObjectName("cardMenuButton")
        self.options_button.setText("설정")
        self.options_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.options_button.setMenu(self._create_options_menu())
        self.options_button.setToolTip("메모 삭제")
        heading_layout.addWidget(self.options_button)
        layout.addWidget(heading)

        self._refresh_format_buttons()

        meta = QFrame()
        meta.setObjectName("cardMeta")
        meta_layout = QHBoxLayout(meta)
        meta_layout.setContentsMargins(13, 0, 13, 5)
        self.timestamp_label = QLabel()
        self.timestamp_label.setObjectName("timestampLabel")
        self.timestamp_label.setWordWrap(True)
        self.timestamp_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        meta_layout.addWidget(self.timestamp_label, 1)
        layout.addWidget(meta)

        self.editor = ChecklistTextEdit()
        self.editor.setObjectName("cardEditor")
        self.editor.setAcceptRichText(True)
        self.editor.setFrameShape(QFrame.Shape.NoFrame)
        self.editor.document().setDocumentMargin(0)
        self.editor.setMinimumHeight(72)
        self.editor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.editor.textChanged.connect(self._content_changed)
        self.editor.checklist_changed.connect(self._content_changed)
        layout.addWidget(self.editor)

        self.resize_handle = CardResizeHandle(self)
        layout.addWidget(self.resize_handle)

    def _create_options_menu(self) -> QMenu:
        menu = QMenu(self)
        opacity_menu = menu.addMenu("투명도")
        opacity_group = QActionGroup(opacity_menu)
        opacity_group.setExclusive(True)
        self.opacity_actions: dict[int, QAction] = {}
        nearest_opacity = min((100, 85, 70, 55), key=lambda value: abs(value - self.note.opacity))
        for opacity in (100, 85, 70, 55):
            action = opacity_menu.addAction(f"{opacity}%")
            action.setCheckable(True)
            action.setChecked(opacity == nearest_opacity)
            opacity_group.addAction(action)
            action.triggered.connect(
                lambda checked=False, value=opacity: self.set_card_opacity(value)
            )
            self.opacity_actions[opacity] = action
        menu.addSeparator()
        delete_action = menu.addAction("메모 삭제")
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.note.id))
        return menu

    def _create_highlight_menu(self) -> QMenu:
        menu = QMenu(self)
        for label, color in HIGHLIGHT_COLORS.items():
            action = menu.addAction(_swatch_icon(color), label)
            action.triggered.connect(
                lambda checked=False, value=color: self._select_highlight_color(value)
            )
        menu.addSeparator()
        clear_action = menu.addAction(_swatch_icon("#FFFFFF", crossed=True), "형광펜 지우기")
        clear_action.triggered.connect(lambda: self._select_highlight_color(None))
        return menu

    def _create_text_color_menu(self) -> QMenu:
        menu = QMenu(self)
        for label, color in TEXT_COLORS.items():
            action = menu.addAction(_swatch_icon(color), label)
            action.triggered.connect(
                lambda checked=False, value=color: self._select_text_color(value)
            )
        return menu

    def _select_highlight_color(self, color: str | None) -> None:
        self._highlight_color = color
        self._refresh_format_buttons()
        self.apply_highlight(color)

    def _select_text_color(self, color: str) -> None:
        self._text_color = color
        self._refresh_format_buttons()
        self.apply_text_color(color)

    def _apply_selected_highlight(self) -> None:
        self.apply_highlight(self._highlight_color)

    def _apply_selected_text_color(self) -> None:
        self.apply_text_color(self._text_color)

    def _refresh_format_buttons(self) -> None:
        highlight_label = next(
            (label for label, value in HIGHLIGHT_COLORS.items() if value == self._highlight_color),
            "지우기",
        )
        text_label = next(
            (label for label, value in TEXT_COLORS.items() if value == self._text_color),
            "먹색",
        )
        self.highlight_button.setIcon(_format_icon("highlight", self._highlight_color))
        self.highlight_button.setToolTip(
            f"형광펜: {highlight_label} · 클릭해 적용, 화살표로 색 선택"
        )
        self.text_color_button.setIcon(_format_icon("text", self._text_color))
        self.text_color_button.setToolTip(
            f"글자색: {text_label} · 클릭해 적용, 화살표로 색 선택"
        )

    def _load_note(self) -> None:
        self.title_edit.setText(self.note.title)
        if self.note.content_html:
            self.editor.setHtml(self.note.content_html)
        self.editor.load_checklist_json(self.note.checklist_json)
        self.complete_check.setChecked(self.note.completed)
        self._update_timestamp_label()
        self.set_card_height(self.note.card_height, persist=False, mark_dirty=False)

    def _update_timestamp_label(self) -> None:
        created = _format_timestamp(self.note.created_at)
        updated = _format_timestamp(self.note.updated_at)
        self.timestamp_label.setText(f"작성 {created}  ·  수정 {updated}")

    def _content_changed(self) -> None:
        if self._ready:
            self._dirty = True
            self._save_timer.start()

    def save_now(self) -> None:
        if not self._ready or not self._dirty:
            return
        self.note.title = self.title_edit.text().strip()
        self.note.content_html = self.editor.toHtml() if self.editor.toPlainText() else ""
        self.note.checklist_json = self.editor.checklist_json()
        self.note = self.controller.repository.save_note(self.note)
        self._dirty = False
        self._height_dirty = False
        self._update_timestamp_label()
        self.changed.emit(self.note.id)

    def set_card_height(
        self,
        height: int,
        *,
        persist: bool,
        mark_dirty: bool = True,
    ) -> None:
        bounded = max(MIN_CARD_HEIGHT, min(MAX_CARD_HEIGHT, int(height)))
        changed = self.note.card_height != bounded or self.height() != bounded
        if changed:
            self.note.card_height = bounded
            self.setFixedHeight(bounded)
            self.resize_handle.update()
        if self._ready and mark_dirty and changed:
            self._height_dirty = True
        if persist:
            self.commit_card_height()

    def commit_card_height(self) -> None:
        if not self._ready or not self._height_dirty:
            return
        self.controller.repository.save_card_height(self.note.id, self.note.card_height)
        self._height_dirty = False

    def set_card_opacity(self, opacity: int) -> None:
        bounded = max(40, min(100, int(opacity)))
        if self.note.opacity == bounded:
            return
        self.note.opacity = bounded
        self.controller.repository.save_card_opacity(self.note.id, bounded)
        action = self.opacity_actions.get(bounded)
        if action is not None:
            action.setChecked(True)
        self._apply_state_style()

    def _completion_changed(self, completed: bool) -> None:
        if not self._ready:
            return
        self.note.completed = completed
        self._dirty = True
        self._apply_state_style()
        self.save_now()

    def _apply_state_style(self) -> None:
        completed = self.note.completed
        surface = QColor("#D8D6CF") if completed else QColor("#FFFFFF")
        surface_alpha = round(255 * self.note.opacity / 100)
        surface_css = (
            f"rgba({surface.red()}, {surface.green()}, {surface.blue()}, {surface_alpha})"
        )
        ink = "#5B5954" if completed else "#302D25"
        subdued = "#77746D" if completed else "#716A58"

        self.setStyleSheet(
            f"""
            QFrame#memoCard {{
                background: {surface_css};
                border: 1px solid rgba(70, 63, 47, 42);
                border-radius: 12px;
            }}
            QFrame#cardHeading {{
                background: transparent;
                border-top-left-radius: 11px;
                border-top-right-radius: 11px;
            }}
            QFrame#cardMeta {{
                background: transparent;
            }}
            QWidget#cardResizeHandle {{
                background: transparent;
                border-top: 1px solid rgba(70, 63, 47, 22);
                border-bottom-left-radius: 11px;
                border-bottom-right-radius: 11px;
            }}
            QLineEdit#cardTitle {{
                background: transparent;
                border: 0;
                border-bottom: 2px solid transparent;
                color: {ink};
                font-size: 17px;
                font-weight: 700;
                padding: 2px 0 4px 0;
                selection-background-color: #625A45;
                selection-color: #FFFDF7;
            }}
            QLineEdit#cardTitle:focus {{
                border-bottom-color: #625A45;
            }}
            QLabel#timestampLabel {{
                color: {subdued};
                font-size: 10px;
                padding-bottom: 1px;
            }}
            QTextEdit#cardEditor {{
                background: transparent;
                border: 0;
                color: {ink};
                font-size: 14px;
                padding: 8px 13px 10px 4px;
                selection-background-color: #625A45;
                selection-color: #FFFDF7;
            }}
            QTextEdit#cardEditor:read-only {{
                color: {subdued};
            }}
            QCheckBox {{
                color: {ink};
                spacing: 6px;
                font-size: 12px;
                font-weight: 700;
            }}
            QToolButton {{
                background: rgba(255, 255, 255, 115);
                border: 1px solid rgba(48, 45, 37, 42);
                border-radius: 7px;
                color: {ink};
                padding: 5px 8px;
                font-size: 11px;
                font-weight: 600;
            }}
            QToolButton#formatButton {{
                padding: 2px;
            }}
            QToolButton#formatButton::menu-button {{
                subcontrol-origin: padding;
                subcontrol-position: right;
                width: 10px;
                border-left: 1px solid rgba(48, 45, 37, 34);
            }}
            QToolButton#cardMenuButton {{
                padding: 5px 7px;
            }}
            QToolButton:hover {{
                background: rgba(255, 255, 255, 205);
                border-color: rgba(48, 45, 37, 72);
            }}
            QToolButton:pressed {{
                background: rgba(225, 221, 211, 210);
            }}
            QToolButton:focus, QCheckBox:focus {{
                border: 2px solid #514C3E;
            }}
            QToolButton:disabled {{
                color: {subdued};
                background: rgba(255, 255, 255, 35);
            }}
            QMenu {{
                background: #FFFDF7;
                color: #2D2A24;
                border: 1px solid #D8D2C4;
                padding: 6px;
            }}
            QMenu::item {{
                padding: 7px 24px 7px 8px;
                border-radius: 5px;
            }}
            QMenu::item:selected {{
                background: #F0E8D8;
            }}
            """
        )

        self.title_edit.setReadOnly(completed)
        self.editor.setReadOnly(completed)
        self.checklist_button.setEnabled(not completed)
        self.highlight_button.setEnabled(not completed)
        self.text_color_button.setEnabled(not completed)

        title_font = self.title_edit.font()
        title_font.setStrikeOut(completed)
        self.title_edit.setFont(title_font)
        editor_font = self.editor.font()
        editor_font.setStrikeOut(completed)
        self.editor.setFont(editor_font)
        self.resize_handle.update()

    def _toggle_current_check_item(self) -> None:
        self.editor.toggle_current_check_item()

    def apply_highlight(self, color: str | None) -> None:
        char_format = QTextCharFormat()
        if color is None:
            char_format.clearBackground()
        else:
            char_format.setBackground(QBrush(QColor(color)))
        self._merge_character_format(char_format)

    def apply_text_color(self, color: str) -> None:
        char_format = QTextCharFormat()
        char_format.setForeground(QBrush(QColor(color)))
        self._merge_character_format(char_format)

    def _merge_character_format(self, char_format: QTextCharFormat) -> None:
        cursor = self.editor.textCursor()
        cursor.mergeCharFormat(char_format)
        self.editor.mergeCurrentCharFormat(char_format)
        self.editor.setFocus(Qt.FocusReason.ShortcutFocusReason)
        self._dirty = True
        self._save_timer.start()


class MemoBoardWindow(QWidget):
    def __init__(self, controller: "MemoApplication", notes: list[Note]) -> None:
        super().__init__()
        self.controller = controller
        self.cards: dict[int, MemoCard] = {}
        self._ready = False
        self._force_close = False

        self.setWindowTitle("메모 스티커")
        self.setWindowIcon(controller.icon)
        self.setMinimumSize(350, 420)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._apply_window_flags()

        self._geometry_timer = QTimer(self)
        self._geometry_timer.setSingleShot(True)
        self._geometry_timer.setInterval(450)
        self._geometry_timer.timeout.connect(self.save_window_state)

        self._build_ui()
        for note in reversed(notes):
            self.add_card(note, focus=False)
        self._restore_geometry(notes)
        self._ready = True
        self.refresh_summary()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 10)
        outer.setSpacing(0)

        self.board = QFrame()
        self.board.setObjectName("board")
        self.board.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        outer.addWidget(self.board)

        board_layout = QVBoxLayout(self.board)
        board_layout.setContentsMargins(0, 0, 0, 0)
        board_layout.setSpacing(8)

        self.header = DragHeader(self)
        self.header.setFixedHeight(42)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(13, 4, 13, 2)
        header_layout.setSpacing(6)
        header_layout.addStretch(1)

        self.add_button = QPushButton("메모 추가")
        self.add_button.setObjectName("primaryButton")
        self.add_button.setToolTip("새 메모 추가 (Ctrl+N)")
        self.add_button.clicked.connect(self.controller.create_note)
        header_layout.addWidget(self.add_button)

        self.menu_button = QPushButton("메뉴")
        self.menu_button.setObjectName("headerButton")
        self.menu_button.setMenu(self._create_window_menu())
        header_layout.addWidget(self.menu_button)

        self.minimize_button = QToolButton()
        self.minimize_button.setObjectName("windowControl")
        self.minimize_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarMinButton)
        )
        self.minimize_button.setFixedSize(34, 32)
        self.minimize_button.setToolTip("최소화")
        self.minimize_button.setAccessibleName("최소화")
        self.minimize_button.clicked.connect(self.minimize_window)
        header_layout.addWidget(self.minimize_button)

        self.hide_button = QToolButton()
        self.hide_button.setObjectName("windowControl")
        self.hide_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarCloseButton))
        self.hide_button.setFixedSize(34, 32)
        self.hide_button.setToolTip("창 숨기기")
        self.hide_button.setAccessibleName("창 숨기기")
        self.hide_button.clicked.connect(self.hide_window)
        header_layout.addWidget(self.hide_button)
        board_layout.addWidget(self.header)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("memoScroll")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.scroll_area.viewport().setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.scroll_host = QWidget()
        self.scroll_host.setObjectName("scrollHost")
        self.scroll_host.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.cards_layout = QVBoxLayout(self.scroll_host)
        self.cards_layout.setContentsMargins(13, 4, 13, 13)
        self.cards_layout.setSpacing(10)
        self.cards_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinAndMaxSize)

        self.empty_state = QFrame()
        self.empty_state.setObjectName("emptyState")
        empty_layout = QVBoxLayout(self.empty_state)
        empty_layout.setContentsMargins(24, 44, 24, 44)
        empty_layout.setSpacing(8)
        empty_title = QLabel("아직 메모가 없습니다")
        empty_title.setObjectName("emptyTitle")
        empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_title)
        empty_text = QLabel("메모를 추가하면 이곳에 차곡차곡 쌓입니다.")
        empty_text.setObjectName("emptyText")
        empty_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_text.setWordWrap(True)
        empty_layout.addWidget(empty_text)
        empty_button = QPushButton("첫 메모 추가")
        empty_button.setObjectName("emptyButton")
        empty_button.clicked.connect(self.controller.create_note)
        empty_layout.addWidget(empty_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.cards_layout.addWidget(self.empty_state)
        self.cards_layout.addStretch(1)
        self.scroll_area.setWidget(self.scroll_host)
        board_layout.addWidget(self.scroll_area, 1)

        self.window_size_grip = QSizeGrip(self)
        self.window_size_grip.setFixedSize(18, 18)
        self.window_size_grip.setToolTip("드래그하여 창 크기 조절")
        self.window_size_grip.setAccessibleName("창 크기 조절")
        self._position_window_size_grip()

        new_action = QAction(self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.controller.create_note)
        self.addAction(new_action)

        self.setStyleSheet(
            """
            QFrame#board {
                background: transparent;
            }
            QFrame#dragHeader {
                background: transparent;
                border: 0;
            }
            QPushButton#primaryButton {
                background: #2F4A42;
                color: #FFFFFF;
                border: 0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton#primaryButton:hover {
                background: #3B5D52;
            }
            QPushButton#primaryButton:pressed {
                background: #243A34;
            }
            QPushButton#headerButton, QToolButton#windowControl {
                background: rgba(241, 238, 231, 150);
                color: #302D25;
                border: 1px solid rgba(70, 63, 47, 24);
                border-radius: 7px;
                padding: 6px 8px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton#headerButton:hover, QToolButton#windowControl:hover {
                background: rgba(255, 255, 255, 220);
                border-color: rgba(48, 45, 37, 52);
            }
            QPushButton#headerButton:pressed, QToolButton#windowControl:pressed {
                background: rgba(226, 222, 213, 220);
            }
            QPushButton:focus, QToolButton:focus {
                border: 2px solid #514C3E;
            }
            QScrollArea#memoScroll, QWidget#scrollHost {
                background: transparent;
            }
            QScrollArea#memoScroll > QWidget > QWidget {
                background: transparent;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 9px;
                margin: 3px 2px;
            }
            QScrollBar::handle:vertical {
                background: rgba(84, 80, 72, 92);
                min-height: 30px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(47, 74, 66, 150);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            QFrame#emptyState {
                background: rgba(255, 255, 255, 218);
                border: 1px solid rgba(65, 60, 50, 42);
                border-radius: 12px;
            }
            QLabel#emptyTitle {
                color: #3B372E;
                font-size: 16px;
                font-weight: 700;
            }
            QLabel#emptyText {
                color: #746D5E;
                font-size: 12px;
            }
            QPushButton#emptyButton {
                background: transparent;
                color: #3D392F;
                border: 1px solid #8F8675;
                border-radius: 7px;
                padding: 7px 11px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton#emptyButton:hover {
                background: #FFFDF7;
            }
            QSizeGrip {
                background: transparent;
            }
            QMenu {
                background: #FFFDF7;
                color: #2D2A24;
                border: 1px solid #D8D2C4;
                padding: 6px;
            }
            QMenu::item {
                padding: 7px 24px 7px 8px;
                border-radius: 5px;
            }
            QMenu::item:selected {
                background: #E7EEE9;
                color: #243A34;
            }
            """
        )

    def _create_window_menu(self) -> QMenu:
        menu = QMenu(self)
        self.title_index_menu = menu.addMenu("메모 제목으로 모아보기")
        self.title_index_menu.aboutToShow.connect(self._populate_title_index_menu)
        menu.addSeparator()
        self.always_on_top_action = menu.addAction("바탕화면에서 항상 표시")
        self.always_on_top_action.setCheckable(True)
        self.always_on_top_action.setChecked(self.controller.always_on_top)
        self.always_on_top_action.setToolTip("다른 프로그램을 사용할 때도 메모를 맨 위에 표시합니다")
        self.always_on_top_action.toggled.connect(self.set_always_on_top)
        menu.addSeparator()
        update_action = menu.addAction(f"업데이트 확인 · v{APP_VERSION}")
        update_action.triggered.connect(
            lambda: self.controller.updater.check_for_updates(interactive=True)
        )
        menu.addSeparator()
        quit_action = menu.addAction("앱 종료")
        quit_action.triggered.connect(self.controller.quit)
        return menu

    def _populate_title_index_menu(self) -> None:
        self.title_index_menu.clear()
        ordered_cards: list[MemoCard] = []
        for index in range(self.cards_layout.count()):
            widget = self.cards_layout.itemAt(index).widget()
            if isinstance(widget, MemoCard):
                ordered_cards.append(widget)

        if not ordered_cards:
            empty_action = self.title_index_menu.addAction("저장된 메모 없음")
            empty_action.setEnabled(False)
            return

        for card in ordered_cards:
            title = card.title_edit.text().strip() or "제목 없는 메모"
            prefix = "완료 · " if card.note.completed else ""
            action = self.title_index_menu.addAction(f"{prefix}{title[:40]}")
            action.triggered.connect(
                lambda checked=False, note_id=card.note.id: self.focus_note(note_id)
            )

    def add_card(self, note: Note, *, focus: bool = True) -> MemoCard:
        card = MemoCard(self.controller, note)
        card.delete_requested.connect(self.request_delete)
        card.changed.connect(self._card_changed)
        self.cards[note.id] = card
        self.cards_layout.insertWidget(0, card)
        self.refresh_summary()
        if focus:
            self.show_window()
            QTimer.singleShot(0, lambda: self._focus_card(card))
        return card

    def _focus_card(self, card: MemoCard) -> None:
        self.scroll_area.ensureWidgetVisible(card, 0, 12)
        card.title_edit.setFocus(Qt.FocusReason.OtherFocusReason)

    def _card_changed(self, note_id: int) -> None:
        self.refresh_summary()
        self.controller.note_changed(note_id)

    def request_delete(self, note_id: int) -> None:
        result = QMessageBox.question(
            self,
            "메모 삭제",
            "이 메모를 완전히 삭제할까요?\n삭제한 메모는 복구할 수 없습니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if result == QMessageBox.StandardButton.Yes:
            self.controller.delete_note(note_id)

    def remove_card(self, note_id: int) -> None:
        card = self.cards.pop(note_id, None)
        if card is not None:
            card._save_timer.stop()
            card.setParent(None)
            card.deleteLater()
        self.refresh_summary()

    def refresh_summary(self) -> None:
        total = len(self.cards)
        self.empty_state.setVisible(total == 0)

    def focus_note(self, note_id: int) -> None:
        card = self.cards.get(note_id)
        if card is not None:
            self.show_window()
            self._focus_card(card)

    def _restore_geometry(self, notes: list[Note]) -> None:
        fallback = notes[0] if notes else None
        x = self.controller.setting_int("window_x", fallback.x if fallback else 160)
        y = self.controller.setting_int("window_y", fallback.y if fallback else 120)
        width = self.controller.setting_int("window_width", max(420, fallback.width) if fallback else 430)
        height = self.controller.setting_int("window_height", max(560, fallback.height) if fallback else 650)
        desired = QRect(x, y, max(self.minimumWidth(), width), max(self.minimumHeight(), height))
        screen = QApplication.screenAt(desired.center()) or QApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            desired.moveLeft(max(available.left(), min(desired.left(), available.right() - 140)))
            desired.moveTop(max(available.top(), min(desired.top(), available.bottom() - 100)))
        self.setGeometry(desired)

    def save_all(self) -> None:
        for card in self.cards.values():
            card._save_timer.stop()
            card.save_now()
            card.commit_card_height()
        self.save_window_state()

    def save_window_state(self) -> None:
        if not self._ready:
            return
        repository = self.controller.repository
        repository.set_setting("window_x", self.x())
        repository.set_setting("window_y", self.y())
        repository.set_setting("window_width", self.width())
        repository.set_setting("window_height", self.height())

    def _apply_window_flags(self) -> None:
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window
        if self.controller.always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)

    def set_always_on_top(self, enabled: bool) -> None:
        if not self._ready:
            return
        was_visible = self.isVisible()
        self.controller.always_on_top = enabled
        self.controller.repository.set_setting("always_on_top", enabled)
        self._apply_window_flags()
        if was_visible:
            self.show()
            self.raise_()

    def show_window(self) -> None:
        self.controller.repository.set_setting("window_visible", True)
        state = self.windowState()
        if state & Qt.WindowState.WindowMinimized:
            self.setWindowState(
                (state & ~Qt.WindowState.WindowMinimized) | Qt.WindowState.WindowActive
            )
        self.show()
        QTimer.singleShot(0, self._bring_to_front)

    def _bring_to_front(self) -> None:
        if not self.isVisible():
            return
        self.raise_()
        self.activateWindow()

    def minimize_window(self) -> None:
        self.save_all()
        self.controller.repository.set_setting("window_visible", True)
        self.showMinimized()

    def hide_window(self) -> None:
        self.save_all()
        self.controller.repository.set_setting("window_visible", False)
        self.hide()
        if self.controller.tray is None:
            self.controller.quit()

    def moveEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().moveEvent(event)
        if self._ready:
            self._geometry_timer.start()

    def resizeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().resizeEvent(event)
        self._position_window_size_grip()
        if self._ready:
            self._geometry_timer.start()

    def _position_window_size_grip(self) -> None:
        if not hasattr(self, "window_size_grip"):
            return
        margin = 2
        self.window_size_grip.move(
            self.width() - self.window_size_grip.width() - margin,
            self.height() - self.window_size_grip.height() - margin,
        )
        self.window_size_grip.raise_()

    def closeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        if self._force_close:
            event.accept()
        else:
            event.ignore()
            self.hide_window()

    def force_close(self) -> None:
        self._force_close = True
        self.close()


class MemoApplication:
    def __init__(self, app: QApplication, database_path: str | Path | None = None) -> None:
        self.app = app
        self.icon = _app_icon()
        self.app.setWindowIcon(self.icon)
        self.repository = NoteRepository(database_path or self._default_database_path())
        self.updater = UpdateManager(self, app)
        self.tray: QSystemTrayIcon | None = None
        self.tray_menu: QMenu | None = None
        self._quitting = False
        window_behavior_revision = self.repository.get_setting("window_behavior_revision")
        if window_behavior_revision != "3":
            self.always_on_top = False
            self.repository.set_setting("always_on_top", False)
            self.repository.set_setting("window_behavior_revision", "3")
        else:
            self.always_on_top = self.repository.get_setting("always_on_top", "0") == "1"

        self._setup_tray()
        notes = self.repository.list_notes()
        if not notes:
            notes = [self.repository.create_note()]
        self.window = MemoBoardWindow(self, notes)
        self._rebuild_tray_menu()
        if self.repository.get_setting("window_visible", "1") == "1" or self.tray is None:
            self.window.show()
        if database_path is None:
            QTimer.singleShot(2500, lambda: self.updater.check_for_updates(interactive=False))

    @staticmethod
    def _default_database_path() -> Path:
        app_dir = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))
        return app_dir / "memos.db"

    def setting_int(self, key: str, default: int) -> int:
        value = self.repository.get_setting(key)
        try:
            return int(value) if value is not None else default
        except ValueError:
            return default

    def _setup_tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.app.setQuitOnLastWindowClosed(False)
        self.tray = QSystemTrayIcon(self.icon, self.app)
        self.tray.setToolTip("메모 스티커")
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()

    def create_note(self, *_args) -> MemoCard:  # type: ignore[no-untyped-def]
        note = self.repository.create_note()
        card = self.window.add_card(note)
        self._rebuild_tray_menu()
        return card

    def delete_note(self, note_id: int) -> None:
        self.window.remove_card(note_id)
        self.repository.delete_note(note_id)
        self._rebuild_tray_menu()

    def show_note(self, note_id: int) -> None:
        self.window.focus_note(note_id)

    def show_window(self, *_args) -> None:  # type: ignore[no-untyped-def]
        self.window.show_window()

    def note_changed(self, _note_id: int) -> None:
        self._rebuild_tray_menu()

    def _rebuild_tray_menu(self) -> None:
        if self.tray is None:
            return
        menu = QMenu()
        show_action = menu.addAction("메모 창 열기")
        show_action.triggered.connect(self.show_window)
        new_action = menu.addAction("메모 추가")
        new_action.triggered.connect(self.create_note)
        menu.addSeparator()

        notes = self.repository.list_notes()
        if notes:
            for note in notes[:12]:
                label = note.title.strip() or "제목 없는 메모"
                prefix = "완료 · " if note.completed else ""
                action = menu.addAction(f"{prefix}{label[:32]}")
                action.triggered.connect(lambda checked=False, note_id=note.id: self.show_note(note_id))
        else:
            empty = menu.addAction("저장된 메모 없음")
            empty.setEnabled(False)

        menu.addSeparator()
        quit_action = menu.addAction("종료")
        quit_action.triggered.connect(self.quit)
        self.tray_menu = menu
        self.tray.setContextMenu(menu)

    def _tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.show_window()

    def quit(self, *_args) -> None:  # type: ignore[no-untyped-def]
        if self._quitting:
            return
        self._quitting = True
        self.window.save_all()
        self.window.force_close()
        if self.tray is not None:
            self.tray.hide()
        self.repository.close()
        self.app.quit()


def run() -> int:
    app = QApplication(sys.argv)
    app.setOrganizationName("LocalTools")
    app.setApplicationName("MemoSticker")
    app.setApplicationDisplayName("메모 스티커")
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI Variable Text", 10))

    controller = MemoApplication(app)
    app.aboutToQuit.connect(lambda: None if controller._quitting else controller.quit())
    return app.exec()
