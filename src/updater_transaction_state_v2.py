"""Crash-safe staging lifecycle for transactional radio installs."""


def install_transaction_state(core):
    os = core.os
    gui = core.UpdaterGUI

    def remove_dir(path):
        if os.path.isdir(path):
            core.shutil.rmtree(path)

    def tx_target(self, path):
        tx = getattr(self, "_install_tx", None)
        if not tx:
            return path
        absolute = os.path.abspath(path)
        live = os.path.abspath(tx["live"])
        stage = os.path.abspath(tx["stage"])
        if os.path.normcase(absolute) == os.path.normcase(live):
            return stage
        try:
            if os.path.commonpath([absolute, live]) == live:
                return os.path.join(stage, os.path.relpath(absolute, live))
        except ValueError:
            pass
        return path

    def abort_tx(self):
        tx = getattr(self, "_install_tx", None)
        if not tx:
            return
        try:
            remove_dir(tx["stage"])
            if os.path.isdir(tx["backup"]) and not os.path.exists(tx["live"]):
                os.replace(tx["backup"], tx["live"])
                self.log("  Restored previous installation")
        except Exception as error:
            self.log(f"  Transaction cleanup warning: {error}")
        finally:
            self._install_tx = None

    def begin_tx(self, live):
        live = os.path.abspath(live)
        owner = core.threading.current_thread()
        tx = getattr(self, "_install_tx", None)
        if tx:
            same_live = os.path.normcase(tx["live"]) == os.path.normcase(live)
            if same_live and tx.get("owner") is owner:
                return tx["stage"]
            abort_tx(self)

        parent = os.path.dirname(live)
        name = os.path.basename(live)
        stage_prefix = f".{name}-stage-"
        backup = live + ".update-backup"

        if os.path.isdir(backup) and not os.path.exists(live):
            os.replace(backup, live)
            self.log("  Restored an interrupted update backup")
        elif os.path.isdir(backup):
            remove_dir(backup)

        for entry in os.listdir(parent):
            if entry.startswith(stage_prefix):
                remove_dir(os.path.join(parent, entry))

        stage = core.tempfile.mkdtemp(prefix=stage_prefix, dir=parent)
        try:
            if os.path.isdir(live):
                remove_dir(stage)
                core.shutil.copytree(live, stage, copy_function=core.shutil.copy2)
        except Exception:
            remove_dir(stage)
            raise

        self._install_tx = {
            "live": live,
            "stage": stage,
            "backup": backup,
            "owner": owner,
        }
        self.log(f"  Staging update in {os.path.basename(stage)}")
        return stage

    def commit_tx(self):
        tx = getattr(self, "_install_tx", None)
        if not tx:
            return True
        live, stage, backup = tx["live"], tx["stage"], tx["backup"]
        if not self._is_suite_source_dir(stage):
            raise RuntimeError("Staged suite is missing main.lua/main.luac")

        moved = False
        try:
            remove_dir(backup)
            if os.path.isdir(live):
                os.replace(live, backup)
                moved = True
            os.replace(stage, live)
        except Exception as error:
            if os.path.isdir(live):
                remove_dir(live)
            if moved and os.path.isdir(backup):
                os.replace(backup, live)
            raise RuntimeError(
                "Activation failed; the previous installation was restored"
            ) from error

        self._install_tx = None
        try:
            remove_dir(backup)
        except Exception as error:
            self.log(f"  Backup cleanup warning: {error}")
        self.log("✓ Staged installation activated")
        return True

    gui._transaction_target = tx_target
    gui._begin_install_transaction = begin_tx
    gui._abort_install_transaction = abort_tx
    gui._commit_install_transaction = commit_tx
