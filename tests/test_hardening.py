import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import update_radio_gui as updater


class RadioTargetValidationTests(unittest.TestCase):
    def setUp(self):
        self.radio = updater.RadioInterface()

    def _scan(self, root, removable_only, is_removable):
        with (
            mock.patch.object(updater.sys, "platform", "linux"),
            mock.patch.object(self.radio, "_iter_mount_roots", return_value=iter([root])),
            mock.patch.object(self.radio, "_iter_lsblk_mounts", return_value=iter([])),
            mock.patch.object(self.radio, "_is_removable_mount", return_value=is_removable),
            mock.patch.object(self.radio, "_get_volume_label", return_value=None),
        ):
            return self.radio.find_scripts_dir_on_drives(
                removable_only=removable_only
            )

    def test_scripts_folder_alone_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "scripts").mkdir()
            self.assertIsNone(
                self._scan(tmp, removable_only=True, is_removable=True)
            )

    def test_legacy_markers_are_allowed_only_on_removable_media(self):
        with tempfile.TemporaryDirectory() as tmp:
            scripts = Path(tmp) / "scripts"
            scripts.mkdir()
            (Path(tmp) / "radio.bin").write_bytes(b"radio")
            (Path(tmp) / "models").mkdir()

            self.assertEqual(
                os.path.normpath(str(scripts)),
                self._scan(tmp, removable_only=True, is_removable=True),
            )
            self.assertIsNone(
                self._scan(tmp, removable_only=False, is_removable=False)
            )

    def test_cpuid_marker_allows_nonremovable_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            scripts = Path(tmp) / "scripts"
            scripts.mkdir()
            (Path(tmp) / "sdcard.cpuid").write_text("id", encoding="utf-8")

            self.assertEqual(
                os.path.normpath(str(scripts)),
                self._scan(tmp, removable_only=False, is_removable=False),
            )


class FileSyncSafetyTests(unittest.TestCase):
    def setUp(self):
        self.gui = updater.UpdaterGUI.__new__(updater.UpdaterGUI)
        self.gui.is_updating = True
        self.messages = []
        self.gui.log = self.messages.append
        self.gui.update_progress = lambda *_args, **_kwargs: None
        self.gui.attempt_chkdsk = lambda _path: False

    def test_same_size_same_timestamp_different_content_requires_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src.bin"
            dst = Path(tmp) / "dst.bin"
            src.write_bytes(b"AAAA")
            dst.write_bytes(b"BBBB")
            stamp = 1_700_000_000
            os.utime(src, (stamp, stamp))
            os.utime(dst, (stamp + 1, stamp + 1))

            self.assertTrue(self.gui._needs_copy_with_hash(str(src), str(dst)))

    def test_copy_failure_aborts_update(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dst = Path(tmp) / "dst"
            src.mkdir()
            (src / "file.lua").write_text("return true", encoding="utf-8")

            with mock.patch.object(
                updater.shutil, "copy2", side_effect=PermissionError("read-only")
            ):
                with self.assertRaisesRegex(RuntimeError, "file.lua"):
                    self.gui.copy_tree_with_progress(str(src), str(dst))

    def test_stale_delete_failure_aborts_update(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dst = Path(tmp) / "dst"
            src.mkdir()
            dst.mkdir()
            (dst / "obsolete.lua").write_text("old", encoding="utf-8")

            with mock.patch.object(
                updater.os, "remove", side_effect=PermissionError("read-only")
            ):
                with self.assertRaisesRegex(RuntimeError, "obsolete.lua"):
                    self.gui.remove_stale_files_with_progress(str(src), str(dst))


if __name__ == "__main__":
    unittest.main()
