import sys
import tempfile
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import update_radio_gui as updater
from updater_suite_sources import (
    MICHAEL_REPOSITORY,
    MICHAEL_SOURCE,
    OFFICIAL_SOURCE,
    SOURCE_OPTIONS,
)


class SuiteSourceTests(unittest.TestCase):
    def test_selector_contains_official_and_michael_sources(self):
        self.assertEqual(
            SOURCE_OPTIONS,
            (OFFICIAL_SOURCE, MICHAEL_SOURCE),
        )
        self.assertEqual(
            MICHAEL_REPOSITORY,
            "mbwallace1390/rotorflight-lua-ethos-suite",
        )

    def test_custom_snapshot_uses_pinned_master_archive(self):
        gui = updater.UpdaterGUI.__new__(updater.UpdaterGUI)
        gui._is_ui_thread = lambda: False
        gui.log = lambda *_args: None
        gui._update_selection = {
            "suite_source": MICHAEL_SOURCE,
            "suite_source_entry": {
                "download_url": (
                    "https://github.com/mbwallace1390/"
                    "rotorflight-lua-ethos-suite/archive/"
                    "0123456789abcdef.zip"
                ),
                "tag_name": "wallace-0123456",
                "is_asset": False,
                "repository": MICHAEL_REPOSITORY,
            },
        }

        self.assertEqual(
            gui.get_download_url_and_name(),
            (
                "https://github.com/mbwallace1390/"
                "rotorflight-lua-ethos-suite/archive/"
                "0123456789abcdef.zip",
                "wallace-0123456",
                False,
            ),
        )

    def test_custom_source_preserves_main_lua_version(self):
        gui = updater.UpdaterGUI.__new__(updater.UpdaterGUI)
        gui._is_ui_thread = lambda: False
        gui.log = lambda *_args: None
        gui._update_selection = {"suite_source": MICHAEL_SOURCE}

        with tempfile.TemporaryDirectory() as tmp:
            main_lua = Path(tmp) / "main.lua"
            original = (
                'local config = { version = {major = 2, minor = 3, '
                'revision = 0, suffix = "smooth2"} }\n'
            )
            main_lua.write_text(original, encoding="utf-8")

            self.assertTrue(
                gui.update_main_lua_version(str(main_lua), "wallace-0123456")
            )
            self.assertEqual(main_lua.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
