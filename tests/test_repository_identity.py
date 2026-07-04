import sys
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import update_radio_gui as updater


class RepositoryIdentityTests(unittest.TestCase):
    def test_updater_self_links_use_michael_repository(self):
        repository = "mbwallace1390/rotorflight-lua-ethos-suite-updater"
        self.assertEqual(updater.UPDATER_REPOSITORY, repository)
        self.assertEqual(
            updater.UPDATER_REPO_URL,
            f"https://github.com/{repository}",
        )
        self.assertEqual(
            updater.UPDATER_INFO_URL,
            f"https://github.com/{repository}/releases",
        )
        self.assertEqual(
            updater.LOGO_URL,
            f"https://raw.githubusercontent.com/{repository}/master/src/logo.png",
        )

    def test_suite_download_source_remains_official_rotorflight(self):
        self.assertEqual(
            updater.GITHUB_REPO_URL,
            "https://github.com/rotorflight/rotorflight-lua-ethos-suite",
        )
        self.assertEqual(
            updater.GITHUB_API_URL,
            "https://api.github.com/repos/rotorflight/rotorflight-lua-ethos-suite",
        )


if __name__ == "__main__":
    unittest.main()
