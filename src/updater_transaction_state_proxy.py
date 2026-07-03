"""Enable transaction state and its staged update hooks."""

from updater_transaction_state_impl import install_transaction_state as _install_state
from updater_transaction_copy import install_transaction_copy_hooks as _install_copy
from updater_transaction_audio import install_transaction_audio_hook as _install_audio
from updater_transaction_version import install_transaction_version_hook as _install_version
from updater_transaction_finish_read import install_transaction_finish_hook as _install_finish


def install_transaction_state(core):
    _install_state(core)
    _install_copy(core)
    _install_audio(core)
    _install_version(core)
    _install_finish(core)
