"""Selectable Rotorflight Lua suite repositories."""

import json

OFFICIAL_SOURCE = "Official Rotorflight"
MICHAEL_SOURCE = "Michael Wallace RFSuite Master"
SOURCE_OPTIONS = (OFFICIAL_SOURCE, MICHAEL_SOURCE)

MICHAEL_REPOSITORY = "mbwallace1390/rotorflight-lua-ethos-suite"
MICHAEL_REPO_URL = f"https://github.com/{MICHAEL_REPOSITORY}"
MICHAEL_API_URL = f"https://api.github.com/repos/{MICHAEL_REPOSITORY}"
MICHAEL_MASTER_ARCHIVE = f"{MICHAEL_REPO_URL}/archive/refs/heads/master.zip"


def apply_suite_sources(core):
    """Add Michael's master as an install source beside official builds."""
    gui = core.UpdaterGUI
    previous_init = gui.__init__
    previous_setup_ui = gui.setup_ui
    previous_load_settings = gui._load_user_settings
    previous_save_settings = gui._save_user_settings
    previous_bind_settings = gui._bind_settings_autosave
    previous_fetch_versions = gui.fetch_version_list
    previous_update_selected = gui._update_selected_version
    previous_update_combo = gui._update_version_combo
    previous_snapshot = gui._snapshot_update_selection
    previous_get_download = gui.get_download_url_and_name
    previous_controls = gui._set_update_controls_running
    previous_update_main_version = gui.update_main_lua_version

    def source_value(self):
        snapshot = getattr(self, "_update_selection", None) or {}
        if not self._is_ui_thread() and snapshot.get("suite_source"):
            return snapshot["suite_source"]
        return self.selected_suite_source.get()

    def custom_entry(self):
        return getattr(
            self,
            "_michael_master_entry",
            {
                "display_name": MICHAEL_SOURCE,
                "tag_name": "wallace-master",
                "locale": core.DEFAULT_LOCALE,
                "download_url": MICHAEL_MASTER_ARCHIVE,
                "is_asset": False,
                "version_type": core.VERSION_MASTER,
                "repository": MICHAEL_REPOSITORY,
                "commit_sha": "",
            },
        )

    def init(self, root):
        self.selected_suite_source = core.tk.StringVar(value=OFFICIAL_SOURCE)
        self._michael_master_entry = None
        self._official_version_before_custom = None
        self._source_ui_custom = False
        previous_init(self, root)

    def load_settings(self):
        previous_load_settings(self)
        try:
            if not core.os.path.isfile(self.settings_path):
                return
            with open(self.settings_path, "r", encoding="utf-8") as settings_file:
                data = json.load(settings_file)
            source = str(data.get("suite_source", OFFICIAL_SOURCE)).strip()
            if source in SOURCE_OPTIONS:
                self.selected_suite_source.set(source)
        except Exception:
            return

    def save_settings(self, *_args):
        previous_save_settings(self)
        try:
            with open(self.settings_path, "r", encoding="utf-8") as settings_file:
                data = json.load(settings_file)
            if not isinstance(data, dict):
                data = {}
            data["suite_source"] = self.selected_suite_source.get()
            with open(self.settings_path, "w", encoding="utf-8") as settings_file:
                json.dump(data, settings_file, indent=2)
        except Exception as error:
            if hasattr(self, "log_text"):
                self.log(f"Could not save suite source selection: {error}")

    def bind_settings(self):
        previous_bind_settings(self)
        self.selected_suite_source.trace_add("write", self._save_user_settings)

    def setup_ui(self):
        previous_setup_ui(self)
        version_frame = self.version_filter_combo.master

        source_label = core.ttk.Label(
            version_frame,
            text="Suite source:",
            font=("Arial", 9),
        )
        source_label.grid(
            row=2, column=0, padx=(0, 10), pady=(8, 2), sticky="E"
        )

        self.suite_source_combo = core.ttk.Combobox(
            version_frame,
            textvariable=self.selected_suite_source,
            values=SOURCE_OPTIONS,
            state="readonly",
            width=34,
        )
        self.suite_source_combo.grid(
            row=2, column=1, padx=(0, 14), pady=(8, 2), sticky="W"
        )
        self.suite_source_combo.bind(
            "<<ComboboxSelected>>",
            lambda _event: self._on_suite_source_changed(),
        )

        self.suite_source_note = core.ttk.Label(
            version_frame,
            text="Official releases or Michael's current master",
            font=("Arial", 8),
        )
        self.suite_source_note.grid(
            row=2, column=2, columnspan=3, padx=(0, 0), pady=(8, 2), sticky="W"
        )

    def fetch_versions(self):
        versions = previous_fetch_versions(self)
        entry = custom_entry(self)
        try:
            request = core.Request(
                f"{MICHAEL_API_URL}/commits/master",
                headers={"User-Agent": "Rotorflight-Radio-Updater"},
            )
            with self.urlopen_insecure(
                request, timeout=core.DOWNLOAD_TIMEOUT
            ) as response:
                commit = json.loads(response.read().decode("utf-8"))
            sha = str(commit.get("sha", "")).strip()
            if sha:
                sha7 = sha[:7]
                entry = {
                    "display_name": f"Michael Wallace RFSuite Master ({sha7})",
                    "tag_name": f"wallace-{sha7}",
                    "locale": core.DEFAULT_LOCALE,
                    "download_url": f"{MICHAEL_REPO_URL}/archive/{sha}.zip",
                    "is_asset": False,
                    "version_type": core.VERSION_MASTER,
                    "repository": MICHAEL_REPOSITORY,
                    "commit_sha": sha,
                }
        except Exception as error:
            self.log(
                "Could not resolve Michael RFSuite master commit; "
                f"using the master archive: {error}"
            )
        self._michael_master_entry = entry
        return versions

    def apply_source_ui(self):
        source = self.selected_suite_source.get()
        custom = source == MICHAEL_SOURCE
        if custom:
            if not self._source_ui_custom:
                self._official_version_before_custom = self.selected_version.get()
            self._source_ui_custom = True
            self.selected_version.set(core.VERSION_MASTER)
            self.version_filter_combo.current(2)
            self.version_filter_combo.configure(state="disabled")
            entry = custom_entry(self)
            self.version_combo.configure(
                values=(entry["display_name"],), state="readonly"
            )
            self.version_combo.current(0)
            self.suite_source_note.configure(
                text=f"GitHub: {MICHAEL_REPOSITORY} / master"
            )
        else:
            if self._source_ui_custom and self._official_version_before_custom:
                self.selected_version.set(self._official_version_before_custom)
            self._source_ui_custom = False
            self.version_filter_combo.configure(state="readonly")
            channel_index = {
                core.VERSION_RELEASE: 0,
                core.VERSION_SNAPSHOT: 1,
                core.VERSION_MASTER: 2,
            }.get(self.selected_version.get(), 0)
            self.version_filter_combo.current(channel_index)
            previous_update_combo(self)
            self.suite_source_note.configure(
                text="Official releases, snapshots, and development builds"
            )

    def update_selected(self):
        if self.selected_suite_source.get() == MICHAEL_SOURCE:
            self.selected_version.set(core.VERSION_MASTER)
            self._apply_suite_source_ui()
            return
        return previous_update_selected(self)

    def update_combo(self):
        if self.selected_suite_source.get() == MICHAEL_SOURCE:
            self._apply_suite_source_ui()
            return
        return previous_update_combo(self)

    def snapshot(self):
        data = previous_snapshot(self)
        data["suite_source"] = self.selected_suite_source.get()
        if data["suite_source"] == MICHAEL_SOURCE:
            data["suite_source_entry"] = dict(custom_entry(self))
        return data

    def get_download(self):
        if source_value(self) == MICHAEL_SOURCE:
            snapshot = getattr(self, "_update_selection", None) or {}
            entry = snapshot.get("suite_source_entry") or custom_entry(self)
            self.log(
                "Suite source: "
                f"{entry.get('repository', MICHAEL_REPOSITORY)} / master"
            )
            return (
                entry["download_url"],
                entry["tag_name"],
                entry["is_asset"],
            )
        self.log("Suite source: rotorflight/rotorflight-lua-ethos-suite")
        return previous_get_download(self)

    def set_controls(self, running):
        result = previous_controls(self, running)

        def update_source_controls():
            state = "disabled" if running else "readonly"
            if hasattr(self, "suite_source_combo"):
                self.suite_source_combo.configure(state=state)
            self.locale_combo.configure(state=state)
            self.version_combo.configure(state=state)
            if running:
                self.version_filter_combo.configure(state="disabled")
            elif self.selected_suite_source.get() == MICHAEL_SOURCE:
                self.version_filter_combo.configure(state="disabled")
            else:
                self.version_filter_combo.configure(state="readonly")

        self._call_ui(update_source_controls, wait=False)
        return result

    def update_main_version(self, path, suffix):
        if source_value(self) == MICHAEL_SOURCE:
            self.log("Preserving version suffix from Michael RFSuite master")
            return True
        return previous_update_main_version(self, path, suffix)

    gui._suite_source_value = source_value
    gui._michael_suite_entry = custom_entry
    gui._apply_suite_source_ui = apply_source_ui
    gui._on_suite_source_changed = apply_source_ui
    gui.__init__ = init
    gui._load_user_settings = load_settings
    gui._save_user_settings = save_settings
    gui._bind_settings_autosave = bind_settings
    gui.setup_ui = setup_ui
    gui.fetch_version_list = fetch_versions
    gui._update_selected_version = update_selected
    gui._update_version_combo = update_combo
    gui._snapshot_update_selection = snapshot
    gui.get_download_url_and_name = get_download
    gui._set_update_controls_running = set_controls
    gui.update_main_lua_version = update_main_version

    core.OFFICIAL_SUITE_SOURCE = OFFICIAL_SOURCE
    core.MICHAEL_SUITE_SOURCE = MICHAEL_SOURCE
    core.MICHAEL_SUITE_REPOSITORY = MICHAEL_REPOSITORY
