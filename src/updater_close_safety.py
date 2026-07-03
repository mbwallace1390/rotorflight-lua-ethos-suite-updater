"""Safe window-close behavior while an updater worker is active."""


def install_close_safety(core):
    gui = core.UpdaterGUI
    previous_init = gui.__init__

    def request_close(self):
        thread = getattr(self, "update_thread", None)
        if thread is None or not thread.is_alive():
            self._ui_shutdown = True
            self.root.destroy()
            return
        if self._activation_in_progress:
            core.messagebox.showwarning(
                "Update Activating",
                "The radio installation is being activated and the window "
                "cannot be closed yet.",
            )
            return
        if not core.messagebox.askyesno(
            "Cancel Update",
            "An update is still running. Cancel it safely and close when the "
            "worker has stopped?",
        ):
            return
        self._close_requested = True
        self.cancel_update()
        self._poll_close_after_worker()

    def poll_close(self):
        thread = getattr(self, "update_thread", None)
        if thread is None or not thread.is_alive():
            self._ui_shutdown = True
            self.root.destroy()
            return
        self.root.after(100, self._poll_close_after_worker)

    def init(self, root):
        previous_init(self, root)
        self.root.after_idle(
            lambda: self.root.protocol("WM_DELETE_WINDOW", self.request_close)
        )

    gui.request_close = request_close
    gui._poll_close_after_worker = poll_close
    gui.__init__ = init
