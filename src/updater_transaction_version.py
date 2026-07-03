"""Apply main.lua version changes to the staged installation."""


def install_transaction_version_hook(core):
    gui = core.UpdaterGUI
    previous = gui.update_main_lua_version

    def update_version(self, path, suffix):
        return previous(self, self._transaction_target(path), suffix)

    gui.update_main_lua_version = update_version
