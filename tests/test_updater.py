from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from memo_widget.updater import UpdateManager, _version_tuple


class UpdateManagerTests(unittest.TestCase):
    def test_version_tuple_handles_release_tags(self) -> None:
        self.assertGreater(_version_tuple("v1.2.0"), _version_tuple("1.1.9"))
        self.assertEqual(_version_tuple("1.0.0"), (1, 0, 0))

    def test_sha256_digest_validation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "MemoSticker.exe"
            path.write_bytes(b"memo-sticker-release")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()

            self.assertTrue(UpdateManager._digest_matches(path, f"sha256:{digest}"))
            self.assertFalse(UpdateManager._digest_matches(path, "sha256:" + "0" * 64))


if __name__ == "__main__":
    unittest.main()
