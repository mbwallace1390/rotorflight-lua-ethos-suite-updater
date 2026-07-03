"""Active crash-safe transaction coordinator."""

from updater_transaction_proxy_v2 import enable


def install_transaction_state(core):
    enable(core)
