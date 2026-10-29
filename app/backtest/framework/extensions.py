"""Custom strategy loader — discovers and validates per-ticker custom strategies."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Callable

_custom_registry: dict[str, Callable] = {}


def register_custom(name: str):
    """Decorator to register a custom strategy function.

    Usage::

        @register_custom("my_strategy")
        def my_strategy(df):
            ...
            return entries, exits

    The decorated function becomes available via ``load_custom_strategies``.
    """

    def wrapper(fn: Callable) -> Callable:
        _custom_registry[name] = fn
        return fn

    return wrapper


def _resolve_framework_import():
    """Resolve the framework package for aliasing, working from any CWD.

    The custom strategy files use ``from framework.extensions import register_custom``.
    This must resolve to the same ``_custom_registry`` that this module defines.

    Strategy:
    1. Find the project root from this file's own location.
    2. Add it to ``sys.path`` so ``app.backtest.framework`` resolves.
    3. Pre-populate ``sys.modules['app.backtest.framework.extensions']`` with
       the ALREADY-LOADED ``framework.extensions`` module so the relative
       import inside ``framework/__init__.py`` reuses it instead of creating
       a second copy.
    4. Import the package, then alias bare names for convenience.

    Returns
    -------
    tuple[module, module]
        (framework_pkg, extensions_mod) — both from the project root import.
    """
    # Path to this file:  .../stock-market-ta-local/app/backtest/framework/extensions.py
    _this_file = Path(__file__).resolve()
    # parents[0]=framework, [1]=backtest, [2]=app, [3]=project root
    _project_root = _this_file.parents[3]

    # Add the PROJECT ROOT so "app" is importable.
    _root_str = str(_project_root)
    if _root_str not in sys.path:
        sys.path.insert(0, _root_str)

    # CRITICAL: Before importing the package, pre-register the already-loaded
    # ``framework.extensions`` module under the dotted name.  When
    # ``framework/__init__.py`` does ``from .extensions import ...``, Python
    # checks ``sys.modules`` first and finds our entry, reusing the SAME
    # module object (and therefore the same ``_custom_registry``).
    _existing_ext = sys.modules.get("framework.extensions")
    if _existing_ext is not None:
        sys.modules["app.backtest.framework.extensions"] = _existing_ext

    # Now import — the relative import inside __init__.py will find our
    # pre-populated entry and reuse the same module object.
    _fw = importlib.import_module("app.backtest.framework")

    # Retrieve extensions via sys.modules (not as package attribute, since
    # __init__.py does ``from .extensions import ...`` not ``import .extensions``)
    _imported_ext = sys.modules["app.backtest.framework.extensions"]

    # Safety check (fail fast if our assumption broke)
    assert _imported_ext is _existing_ext, (
        f"Module mismatch! _imported_ext={id(_imported_ext)} != "
        f"_existing_ext={id(_existing_ext)}"
    )

    # Alias bare names so ``import framework`` works everywhere.
    sys.modules["framework"] = _fw
    sys.modules["framework.extensions"] = _imported_ext

    return _fw, _imported_ext


def load_custom_strategies(
    custom_dir: str | Path,
    module_names: list[str] | None = None,
) -> dict[str, Callable]:
    """Discover and load custom strategy Python files from *custom_dir*.

    Parameters
    ----------
    custom_dir : str | Path
        Directory containing ``*.py`` files with @register_custom strategies.
    module_names : list[str] | None
        If given, only load modules with these names (without .py suffix).
        Pass None to load every ``*.py`` file in the directory.

    Returns
    -------
    dict[str, Callable]
        Mapping of strategy name → signal function.
    """
    custom_dir = Path(custom_dir)
    _custom_registry.clear()

    # Ensure `from framework.extensions import register_custom` in custom modules
    # resolves to THIS module object, not a duplicate loaded via sys.path.
    _fw, _ext = _resolve_framework_import()

    files = list(custom_dir.glob("*.py"))
    files = [f for f in files if f.name != "__init__.py"]

    for fp in files:
        if module_names is not None and fp.stem not in module_names:
            continue
        spec = importlib.util.spec_from_file_location(fp.stem, fp)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

    return dict(_custom_registry)


def validate_custom_strategies(
    strategies: dict[str, Callable],
    df: "pd.DataFrame",  # type ignored to avoid circular import
    custom_indicators: dict[str, list[str]] | None = None,
) -> list[str]:
    """Validate that custom strategies reference columns present in data.

    Parameters
    ----------
    strategies : dict
        Mapping of name → signal function.
    df : pd.DataFrame
        The data DataFrame the strategies will run against.
    custom_indicators : dict | None
        Optional mapping of strategy name → list of expected column names.
        If a listed column is missing from *df*, a warning is returned.

    Returns
    -------
    list[str]
        List of warning messages (empty if all OK).
    """
    warnings = []
    available_cols = set(df.columns)

    if custom_indicators:
        for sname, cols in custom_indicators.items():
            for col in cols:
                if col not in available_cols:
                    warnings.append(
                        f"Custom strategy '{sname}' references missing column: '{col}'"
                    )

    # Dry-run each strategy to catch runtime errors
    for name, fn in strategies.items():
        try:
            entries, exits = fn(df)
            if len(entries) != len(df):
                warnings.append(
                    f"Custom strategy '{name}' returned mismatched lengths: "
                    f"entries={len(entries)}, df={len(df)}"
                )
        except Exception as exc:
            warnings.append(
                f"Custom strategy '{name}' failed during validation: {exc}"
            )

    return warnings
