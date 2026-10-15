from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import QMessageBox

from .version import APP_VERSION

if TYPE_CHECKING:
    from .application import MemoApplication


RELEASE_API_URL = "https://api.github.com/repos/hgkang17/memo/releases/latest"
RELEASE_PAGE_URL = "https://github.com/hgkang17/memo/releases/latest"
RELEASE_ASSET_NAME = "MemoSticker.exe"


def _version_tuple(value: str) -> tuple[int, ...]:
    numbers = re.findall(r"\d+", value)
    return tuple(int(number) for number in numbers[:4]) or (0,)


class UpdateManager(QObject):
    """Check GitHub Releases and replace a frozen one-file executable safely."""

    def __init__(self, controller: "MemoApplication", parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.controller = controller
        self.network = QNetworkAccessManager(self)
        self._check_reply: QNetworkReply | None = None
        self._download_reply: QNetworkReply | None = None
        self._download_file = None
        self._download_path: Path | None = None
        self._download_digest: str | None = None
        self._interactive = False

    def check_for_updates(self, *, interactive: bool = False) -> None:
        if self._check_reply is not None or self._download_reply is not None:
            if interactive:
                QMessageBox.information(
                    self.controller.window,
                    "업데이트 확인",
                    "이미 업데이트를 확인하고 있습니다.",
                )
            return
        if not interactive and not self._automatic_check_is_due():
            return

        self._interactive = interactive
        request = QNetworkRequest(QUrl(RELEASE_API_URL))
        request.setRawHeader(b"Accept", b"application/vnd.github+json")
        request.setRawHeader(b"User-Agent", b"MemoSticker-Updater")
        self._check_reply = self.network.get(request)
        self._check_reply.finished.connect(self._check_finished)

    def _automatic_check_is_due(self) -> bool:
        value = self.controller.repository.get_setting("last_update_check")
        if not value:
            return True
        try:
            checked_at = datetime.fromisoformat(value)
            if checked_at.tzinfo is None:
                checked_at = checked_at.replace(tzinfo=timezone.utc)
        except ValueError:
            return True
        return datetime.now(timezone.utc) - checked_at >= timedelta(hours=6)

    def _check_finished(self) -> None:
        reply = self._check_reply
        self._check_reply = None
        if reply is None:
            return
        error = reply.error()
        payload = bytes(reply.readAll())
        error_text = reply.errorString()
        reply.deleteLater()
        self.controller.repository.set_setting(
            "last_update_check", datetime.now(timezone.utc).isoformat(timespec="seconds")
        )

        if error != QNetworkReply.NetworkError.NoError:
            if self._interactive:
                QMessageBox.warning(
                    self.controller.window,
                    "업데이트 확인 실패",
                    f"GitHub에 연결하지 못했습니다.\n{error_text}",
                )
            return

        try:
            release = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            if self._interactive:
                QMessageBox.warning(
                    self.controller.window,
                    "업데이트 확인 실패",
                    "GitHub 응답을 읽을 수 없습니다.",
                )
            return

        latest_version = str(release.get("tag_name", "")).lstrip("vV")
        if _version_tuple(latest_version) <= _version_tuple(APP_VERSION):
            if self._interactive:
                QMessageBox.information(
                    self.controller.window,
                    "업데이트 확인",
                    f"현재 최신 버전입니다.\n버전 {APP_VERSION}",
                )
            return

        asset = next(
            (
                item
                for item in release.get("assets", [])
                if item.get("name") == RELEASE_ASSET_NAME
            ),
            None,
        )
        if not asset or not asset.get("browser_download_url"):
            if self._interactive:
                QMessageBox.warning(
                    self.controller.window,
                    "업데이트 파일 없음",
                    f"새 버전 {latest_version}은 있지만 {RELEASE_ASSET_NAME} 파일이 없습니다.\n"
                    f"{RELEASE_PAGE_URL}",
                )
            return

        answer = QMessageBox.question(
            self.controller.window,
            "새 버전 발견",
            f"메모 스티커 {latest_version} 버전이 있습니다.\n지금 업데이트할까요?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        digest = asset.get("digest")
        self._download_digest = str(digest) if digest else None
        self._start_download(str(asset["browser_download_url"]), latest_version)

    def _start_download(self, url: str, version: str) -> None:
        self._download_path = Path(tempfile.gettempdir()) / f"MemoSticker-{version}.update.exe"
        self._download_file = self._download_path.open("wb")
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader(b"User-Agent", b"MemoSticker-Updater")
        request.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy,
        )
        self._download_reply = self.network.get(request)
        self._download_reply.readyRead.connect(self._write_download_chunk)
        self._download_reply.finished.connect(self._download_finished)
        if self.controller.tray is not None:
            self.controller.tray.showMessage(
                "메모 스티커",
                "새 버전을 다운로드하고 있습니다.",
            )

    def _write_download_chunk(self) -> None:
        if self._download_reply is None or self._download_file is None:
            return
        self._download_file.write(bytes(self._download_reply.readAll()))

    def _download_finished(self) -> None:
        reply = self._download_reply
        self._download_reply = None
        if reply is None:
            return
        self._write_download_chunk()
        error = reply.error()
        error_text = reply.errorString()
        reply.deleteLater()
        if self._download_file is not None:
            self._download_file.close()
            self._download_file = None

        if error != QNetworkReply.NetworkError.NoError or self._download_path is None:
            self._discard_download()
            QMessageBox.warning(
                self.controller.window,
                "업데이트 다운로드 실패",
                error_text,
            )
            return

        if not self._digest_matches(self._download_path, self._download_digest):
            self._discard_download()
            QMessageBox.critical(
                self.controller.window,
                "업데이트 검증 실패",
                "다운로드한 파일의 SHA-256 값이 GitHub 릴리즈 정보와 다릅니다.",
            )
            return

        self._install_download(self._download_path)

    @staticmethod
    def _digest_matches(path: Path, expected: str | None) -> bool:
        if not expected or not expected.lower().startswith("sha256:"):
            return True
        actual = hashlib.sha256(path.read_bytes()).hexdigest().lower()
        return actual == expected.split(":", 1)[1].strip().lower()

    def _install_download(self, update_path: Path) -> None:
        if not getattr(sys, "frozen", False):
            QMessageBox.information(
                self.controller.window,
                "업데이트 다운로드 완료",
                f"개발 모드에서는 자동 교체하지 않습니다.\n다운로드 위치:\n{update_path}",
            )
            return

        current_executable = Path(sys.executable).resolve()
        script_path = Path(tempfile.gettempdir()) / f"memo-sticker-update-{os.getpid()}.ps1"
        script_path.write_text(
            """param([string]$Current, [string]$Update, [int]$AppPid)
try { Wait-Process -Id $AppPid -Timeout 30 -ErrorAction SilentlyContinue } catch {}
$replaced = $false
for ($i = 0; $i -lt 20 -and -not $replaced; $i++) {
  try {
    Copy-Item -LiteralPath $Update -Destination $Current -Force -ErrorAction Stop
    $replaced = $true
  } catch {
    Start-Sleep -Milliseconds 500
  }
}
if ($replaced) {
  Start-Process -FilePath $Current
  Remove-Item -LiteralPath $Update -Force -ErrorAction SilentlyContinue
}
Remove-Item -LiteralPath $PSCommandPath -Force -ErrorAction SilentlyContinue
""",
            encoding="utf-8-sig",
        )
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        subprocess.Popen(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-WindowStyle",
                "Hidden",
                "-File",
                str(script_path),
                str(current_executable),
                str(update_path),
                str(os.getpid()),
            ],
            creationflags=creation_flags,
            close_fds=True,
        )
        self.controller.quit()

    def _discard_download(self) -> None:
        if self._download_file is not None:
            self._download_file.close()
            self._download_file = None
        if self._download_path is not None:
            self._download_path.unlink(missing_ok=True)
        self._download_path = None
