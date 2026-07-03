"""Route suite synchronization into the active staging directory."""


def install_transaction_copy_hooks(core):
    gui = core.UpdaterGUI
    previous_remove = gui.remove_stale_files_with_progress
    previous_copy = gui.copy_tree_with_progress

    def remove_stale(self, src, dst, use_phase=False):
        stage = self._begin_install_transaction(dst)
        return previous_remove(self, src, stage, use_phase=use_phase)

    def copy_tree(self, src, dst, use_phase=False):
        stage = self._begin_install_transaction(dst)
        return previous_copy(self, src, stage, use_phase=use_phase)

    gui.remove_stale_files_with_progress = remove_stale
    gui.copy_tree_with_progress = copy_tree
