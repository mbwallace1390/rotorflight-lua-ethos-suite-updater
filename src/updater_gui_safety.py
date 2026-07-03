"""Install GUI dispatch, worker lifecycle, and close protection."""

from updater_close_safety import install_close_safety
from updater_gui_dispatch import install_gui_dispatch
from updater_worker_lifecycle import install_worker_lifecycle


def apply_gui_safety(core):
    install_gui_dispatch(core)
    install_worker_lifecycle(core)
    install_close_safety(core)
