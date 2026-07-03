"""Cooperative cancellation and single-worker update lifecycle."""

import threading


def install_worker_lifecycle(core):
    gui = core.UpdaterGUI
    previous_init = gui.__init__
    previous_process = gui.update_process
    previous_read_version = gui.read_main_lua_version
    previous_controls = gui._set_update_controls_running
    previous_commit = getattr(gui, "_commit_install_transaction", None)

    def set_update_controls(self, running):
        thread = getattr(self, "update_thread", None)
        if (
            not running
            and thread is not None
            and thread.is_alive()
            and threading.current_thread() is thread
        ):
            return None
        return previous_controls(self, running)

    def worker_done(self):
        thread = getattr(self, "update_thread", None)
        if thread is not None and thread.is_alive():
            self.root.after(25, self._worker_done)
            return
        self.update_thread = None
        self._set_update_controls_running(False)
        if self._close_requested:
            self._ui_shutdown = True
            self.root.destroy()

    def run_worker(self):
        try:
            previous_process(self)
        finally:
            if getattr(self, "_install_tx", None):
                try:
                    self._abort_install_transaction()
                except Exception as error:
                    self.log(f"Transaction cleanup warning: {error}")
            self._worker_finished.set()
            self._call_ui(self._worker_done, wait=False)

    def start_update(self):
        thread = getattr(self, "update_thread", None)
        if thread is not None and thread.is_alive():
            self.log("An update is already running")
            return
        core._ensure_work_dir()
        self._update_selection = self._snapshot_update_selection()
        self._cancel_event.clear()
        self._worker_finished.clear()
        self._close_requested = False
        self.is_updating = True
        self._set_update_controls_running(True)
        self.reset_steps()
        self.update_progress(0, "Starting...")
        self.update_thread = threading.Thread(
            target=self._run_update_worker,
            name="rfsuite-updater-worker",
            daemon=False,
        )
        self.update_thread.start()

    def cancel_update(self):
        thread = getattr(self, "update_thread", None)
        if thread is None or not thread.is_alive():
            return
        if self._activation_in_progress:
            core.messagebox.showwarning(
                "Update Activating",
                "The staged installation is being activated. "
                "Please wait for this short step to finish.",
            )
            return
        self._cancel_event.set()
        self.is_updating = False
        self.log("Cancellation requested; stopping at the next safe checkpoint")
        self.set_status("Cancelling safely...")
        self.update_progress(0, "Waiting for the current operation to stop...")

    def read_version(self, path):
        if self._cancel_event.is_set() and getattr(self, "_install_tx", None):
            self._abort_install_transaction()
            raise RuntimeError(
                "Update cancelled before activation; the current "
                "installation was left unchanged"
            )
        return previous_read_version(self, path)

    def init(self, root):
        self._cancel_event = threading.Event()
        self._worker_finished = threading.Event()
        self._activation_in_progress = False
        self._close_requested = False
        previous_init(self, root)

    gui._worker_done = worker_done
    gui._run_update_worker = run_worker
    gui._set_update_controls_running = set_update_controls
    gui.__init__ = init
    gui.start_update = start_update
    gui.cancel_update = cancel_update
    gui.read_main_lua_version = read_version

    if previous_commit is not None:
        def guarded_commit(self):
            self._activation_in_progress = True
            try:
                return previous_commit(self)
            finally:
                self._activation_in_progress = False

        gui._commit_install_transaction = guarded_commit
