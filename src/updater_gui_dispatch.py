"""Install main-thread dispatch around the existing updater GUI."""

from updater_ui_proxy import MessageboxProxy, ThreadAwareVariable, ThreadAwareWidget
from updater_ui_queue import install_ui_queue


def install_gui_dispatch(core):
    install_ui_queue(core)
    gui = core.UpdaterGUI
    previous_init = gui.__init__
    previous_get_download = gui.get_download_url_and_name
    dialog_proxy = MessageboxProxy(core.messagebox)
    core.messagebox = dialog_proxy

    def snapshot_selection(self):
        return {
            "version": self.selected_version.get(),
            "locale": self.selected_locale.get(),
            "version_display": self.version_combo.get(),
            "locale_display": self.locale_combo.get(),
        }

    def get_download(self):
        if self._is_ui_thread():
            return previous_get_download(self)
        snapshot = getattr(self, "_update_selection", None) or {}
        locale = snapshot.get("locale_display") or snapshot.get("locale")
        display = snapshot.get("version_display")
        selected = self.version_list.get(locale, {}).get(display)
        if selected is None:
            selected = self.version_list[core.DEFAULT_LOCALE]["Master"]
        return (
            selected["download_url"],
            selected["tag_name"],
            selected["is_asset"],
        )

    def init(self, root):
        self._update_selection = {}
        previous_init(self, root)
        self.selected_version = ThreadAwareVariable(
            self.selected_version, self, "version"
        )
        self.selected_locale = ThreadAwareVariable(
            self.selected_locale, self, "locale"
        )
        if hasattr(self, "progress_label"):
            self.progress_label = ThreadAwareWidget(self.progress_label, self)
        dialog_proxy.set_app(self)

    def wrap_ui_method(name):
        previous = getattr(gui, name, None)
        if previous is None:
            return

        def wrapped(self, *args, **kwargs):
            return self._call_ui(
                lambda: previous(self, *args, **kwargs), wait=False
            )

        setattr(gui, name, wrapped)

    gui._snapshot_update_selection = snapshot_selection
    gui.get_download_url_and_name = get_download
    gui.__init__ = init

    for name in (
        "log", "set_status", "update_progress", "reset_steps",
        "mark_step_done", "set_current_step", "_draw_segment_bar",
        "_start_segment_pulse", "_stop_segment_pulse",
        "_set_update_controls_running",
    ):
        wrap_ui_method(name)
