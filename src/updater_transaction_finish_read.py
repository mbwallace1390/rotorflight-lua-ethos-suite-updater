"""Finalize a staged installation before reporting its installed version."""


def install_transaction_finish_hook(core):
    gui = core.UpdaterGUI
    previous = gui.read_main_lua_version

    def read_version(self, path):
        if getattr(self, "_install_tx", None):
            self._commit_install_transaction()
        return previous(self, path)

    gui.read_main_lua_version = read_version
