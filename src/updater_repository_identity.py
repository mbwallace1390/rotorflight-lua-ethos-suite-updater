"""Repository identity and links for Michael Wallace's updater fork."""

UPDATER_REPOSITORY = "mbwallace1390/rotorflight-lua-ethos-suite-updater"
UPDATER_REPO_URL = f"https://github.com/{UPDATER_REPOSITORY}"
UPDATER_RELEASES_URL = f"{UPDATER_REPO_URL}/releases"
UPDATER_API_URL = f"https://api.github.com/repos/{UPDATER_REPOSITORY}"
UPDATER_LOGO_URL = (
    f"https://raw.githubusercontent.com/{UPDATER_REPOSITORY}/master/src/logo.png"
)


def apply_repository_identity(core):
    """Point updater self-links at this repository without changing suite source."""
    core.UPDATER_REPOSITORY = UPDATER_REPOSITORY
    core.UPDATER_REPO_URL = UPDATER_REPO_URL
    core.UPDATER_RELEASES_URL = UPDATER_RELEASES_URL
    core.UPDATER_API_URL = UPDATER_API_URL
    core.LOGO_URL = UPDATER_LOGO_URL
    core.UPDATER_INFO_URL = UPDATER_RELEASES_URL

    gui = core.UpdaterGUI
    previous_setup_ui = gui.setup_ui

    def setup_ui(self):
        previous_setup_ui(self)

        if hasattr(self, "update_notice_button"):
            self.update_notice_button.configure(text="Latest Updater Release")

        if hasattr(self, "update_notice"):
            self.updater_repo_label = core.ttk.Label(
                self.update_notice,
                text=f"Updater source: {UPDATER_REPOSITORY}",
            )
            self.updater_repo_label.pack(side=core.tk.LEFT)

            self.updater_repo_button = core.ttk.Button(
                self.update_notice,
                text="GitHub Repository",
                command=lambda: core.webbrowser.open(UPDATER_REPO_URL),
            )
            self.updater_repo_button.pack(side=core.tk.RIGHT, padx=(0, 8))

    gui.setup_ui = setup_ui
