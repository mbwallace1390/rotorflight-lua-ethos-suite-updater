#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hardened entry point for the Rotorflight Lua Ethos Suite updater."""

import updater_core as _core
from updater_gui_safety import apply_gui_safety as _apply_gui_safety
from updater_hardening import apply_hardening as _apply_hardening
from updater_repository_identity import apply_repository_identity as _apply_repository_identity
from updater_security import apply_verified_https as _apply_verified_https
from updater_suite_sources import apply_suite_sources as _apply_suite_sources
from updater_transaction_proxy_active import install_transaction_state as _install_transaction_state

_apply_hardening(_core)
_apply_verified_https(_core)
_install_transaction_state(_core)
_apply_repository_identity(_core)
_apply_gui_safety(_core)
_apply_suite_sources(_core)

for _name in dir(_core):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_core, _name)

# Preserve the original module's public and internal import surface for existing
# callers while keeping the large application implementation in updater_core.
__all__ = [name for name in globals() if not name.startswith("__")]


if __name__ == "__main__":
    _core.main()
