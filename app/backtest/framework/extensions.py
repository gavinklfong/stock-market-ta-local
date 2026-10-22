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

    files = list(custom_dir.glob("*.py"))
    files = [f for f in files if f.name != "__init__.py"]

    for fp in files:
        if module_names is not None and fp.stem not in module_names:
            continue
        spec = importlib.util.spec_from_file_location(fp.stem, fp)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            # Make the backtest framework discoverable
            sys.path.insert(0, str(custom_dir.parent))
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
