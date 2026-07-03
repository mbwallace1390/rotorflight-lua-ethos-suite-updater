"""Enable crash-safe transactional installation hooks."""

from updater_transaction_state_v2 import install_transaction_state as _state
from updater_transaction_copy import install_transaction_copy_hooks as _copy
from updater_transaction_audio import install_transaction_audio_hook as _audio
from updater_transaction_version import install_transaction_version_hook as _version
from updater_transaction_finish_read import install_transaction_finish_hook as _finish


def enable(core):
    _state(core)
    _copy(core)
    _audio(core)
    _version(core)
    _finish(core)
