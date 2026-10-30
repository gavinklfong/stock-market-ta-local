"""Shared helpers for calculate_ta tests."""

import os
import pytest


def _state_path(output_path):
    """Compute the state file path for a given output CSV path.

    State files are stored in a ``state/`` subdirectory alongside the
    output CSV, named ``<basename>_state.json``.
    """
    base = output_path.rsplit(".", 1)[0]
    state_dir = os.path.join(os.path.dirname(output_path), "state")
    return os.path.join(state_dir, os.path.basename(base) + "_state.json")


# ---------------------------------------------------------------------------
# pytest hook: make ``_state_path`` available as a builtin in test modules
# ---------------------------------------------------------------------------

def _inject_helpers():
    """Inject module-level helpers into every test module's globals.

    This lets ``test_foo.py`` code call ``_state_path(out)`` without an
    explicit ``from conftest import _state_path`` import.
    """
    import builtins
    builtins._state_path = _state_path


def pytest_configure(config):
    _inject_helpers()
