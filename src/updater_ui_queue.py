"""Thread-safe callback queue for Tkinter."""

import queue
import threading


def install_ui_queue(core):
    gui = core.UpdaterGUI
    previous_init = gui.__init__

    def is_ui_thread(self):
        return threading.get_ident() == getattr(
            self, "_ui_thread_ident", threading.get_ident()
        )

    def call_ui(self, callback, wait=False):
        if self._is_ui_thread() or not hasattr(self, "_ui_queue"):
            return callback()
        done = threading.Event() if wait else None
        result = {}
        self._ui_queue.put((callback, done, result))
        if not wait:
            return None
        if not done.wait(timeout=30):
            raise RuntimeError("Timed out waiting for the GUI thread")
        if "error" in result:
            raise result["error"]
        return result.get("value")

    def drain(self):
        if getattr(self, "_ui_shutdown", False):
            return
        while True:
            try:
                callback, done, result = self._ui_queue.get_nowait()
            except queue.Empty:
                break
            try:
                result["value"] = callback()
            except Exception as error:
                result["error"] = error
            finally:
                if done is not None:
                    done.set()
        try:
            self.root.after(25, self._drain_ui_queue)
        except Exception:
            self._ui_shutdown = True

    def init(self, root):
        self._ui_thread_ident = threading.get_ident()
        self._ui_queue = queue.Queue()
        self._ui_shutdown = False
        previous_init(self, root)
        self.root.after(25, self._drain_ui_queue)

    gui._is_ui_thread = is_ui_thread
    gui._call_ui = call_ui
    gui._drain_ui_queue = drain
    gui.__init__ = init
