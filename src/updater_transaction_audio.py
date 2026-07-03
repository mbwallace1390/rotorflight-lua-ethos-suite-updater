"""Apply locale audio updates to the staged installation."""


def install_transaction_audio_hook(core):
    gui = core.UpdaterGUI
    previous = gui.copy_sound_pack

    def copy_audio(self, repo, dst, locale, use_phase=False):
        target = self._transaction_target(dst)
        return previous(self, repo, target, locale, use_phase=use_phase)

    gui.copy_sound_pack = copy_audio
