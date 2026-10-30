"""Unit tests for common.py — save_state / load_state helpers."""

import json
import os
import tempfile

import pytest

from common import load_state, save_state


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _tmp_file(suffix=".json"):
    """Create a temp file and return its path."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    return path


# ---------------------------------------------------------------------------
# save_state tests
# ---------------------------------------------------------------------------


class TestSaveState:
    """Test save_state writes valid JSON files."""

    def test_writes_simple_dict(self):
        """save_state should write a simple dict to disk."""
        path = _tmp_file()
        save_state({"key": "value"}, path)
        assert os.path.exists(path)
        with open(path) as f:
            data = json.load(f)
        assert data == {"key": "value"}

    def test_writes_nested_dict(self):
        """save_state should handle nested dicts and lists."""
        path = _tmp_file()
        state = {
            "_version": 1,
            "prev_row_count": 100,
            "metrics": {"accuracy": 0.95, "tags": ["a", "b"]},
        }
        save_state(state, path)
        with open(path) as f:
            data = json.load(f)
        assert data["_version"] == 1
        assert data["prev_row_count"] == 100
        assert data["metrics"]["accuracy"] == 0.95
        assert data["metrics"]["tags"] == ["a", "b"]

    def test_creates_state_directory(self):
        """save_state should create parent directories if they don't exist."""
        fd, parent = tempfile.mkstemp(suffix=".d")
        os.close(fd)
        os.unlink(parent)  # remove so mkdir can create it
        path = os.path.join(parent, "sub", "state.json")
        save_state({"x": 1}, path)
        assert os.path.exists(path)
        with open(path) as f:
            assert json.load(f) == {"x": 1}

    def test_writes_empty_dict(self):
        """save_state should handle an empty dict."""
        path = _tmp_file()
        save_state({}, path)
        with open(path) as f:
            assert json.load(f) == {}

    def test_writes_list_values(self):
        """save_state should handle list values in state dict."""
        path = _tmp_file()
        save_state({"values": [1.0, 2.0, 3.0]}, path)
        with open(path) as f:
            assert json.load(f) == {"values": [1.0, 2.0, 3.0]}

    def test_writes_none_values(self):
        """save_state should handle None values."""
        path = _tmp_file()
        save_state({"key": None, "other": "val"}, path)
        with open(path) as f:
            assert json.load(f) == {"key": None, "other": "val"}

    def test_persists_overwrite(self):
        """Calling save_state twice should overwrite the previous file."""
        path = _tmp_file()
        save_state({"step": 1}, path)
        save_state({"step": 2}, path)
        with open(path) as f:
            assert json.load(f) == {"step": 2}


# ---------------------------------------------------------------------------
# load_state tests
# ---------------------------------------------------------------------------


class TestLoadState:
    """Test load_state reads JSON files correctly."""

    def test_reads_valid_json(self):
        """load_state should return the parsed dict from a valid JSON file."""
        path = _tmp_file()
        data = {"count": 42, "active": True}
        with open(path, "w") as f:
            json.dump(data, f)
        result = load_state(path)
        assert result == data

    def test_returns_none_for_missing_file(self):
        """load_state should return None when the file does not exist."""
        result = load_state("/nonexistent/path/state.json")
        assert result is None

    def test_returns_none_for_invalid_json(self):
        """load_state should return None for a corrupted JSON file."""
        path = _tmp_file()
        with open(path, "w") as f:
            f.write("{broken json!!!}")
        result = load_state(path)
        assert result is None

    def test_returns_none_for_empty_file(self):
        """load_state should return None for an empty file."""
        path = _tmp_file()
        with open(path, "w") as f:
            pass
        result = load_state(path)
        assert result is None

    def test_returns_none_for_whitespace_only(self):
        """load_state should return None for whitespace-only content."""
        path = _tmp_file()
        with open(path, "w") as f:
            f.write("   \n  \t  ")
        result = load_state(path)
        assert result is None

    def test_returns_complex_nested_structure(self):
        """load_state should correctly load deeply nested structures."""
        path = _tmp_file()
        data = {
            "a": {"b": {"c": {"d": [1, 2, 3]}}},
            "mixed": {"int": 1, "float": 1.5, "str": "hello", "bool": True, "null": None},
        }
        with open(path, "w") as f:
            json.dump(data, f)
        result = load_state(path)
        assert result == data

    def test_nonexistent_directory_returns_none(self):
        """load_state should return None when the parent directory doesn't exist."""
        result = load_state("/does/not/exist/state.json")
        assert result is None


# ---------------------------------------------------------------------------
# Round-trip tests
# ---------------------------------------------------------------------------


class TestSaveLoadRoundTrip:
    """Test save_state followed by load_state produces identical data."""

    def test_simple_round_trip(self):
        """Basic round-trip should preserve data exactly."""
        path = _tmp_file()
        original = {"x": 1, "y": 2}
        save_state(original, path)
        loaded = load_state(path)
        assert loaded == original

    def test_round_trip_preserves_types(self):
        """Types should be preserved through save/load cycle."""
        path = _tmp_file()
        original = {"int": 42, "float": 3.14, "str": "hello", "bool": True, "null": None}
        save_state(original, path)
        loaded = load_state(path)
        assert loaded["int"] == 42 and isinstance(loaded["int"], int)
        assert loaded["float"] == 3.14 and isinstance(loaded["float"], float)
        assert loaded["str"] == "hello"
        assert loaded["bool"] is True
        assert loaded["null"] is None

    def test_round_trip_with_large_dict(self):
        """Round-trip should handle large state dicts."""
        path = _tmp_file()
        original = {f"key_{i}": i * 2.5 for i in range(1000)}
        save_state(original, path)
        loaded = load_state(path)
        assert loaded == original

    def test_load_after_delete_file(self):
        """load_state should return None after the file is deleted."""
        path = _tmp_file()
        save_state({"x": 1}, path)
        assert load_state(path) == {"x": 1}
        os.unlink(path)
        assert load_state(path) is None

    def test_directory_path_not_file(self):
        """load_state should return None when given a directory path."""
        path = tempfile.mkdtemp()
        result = load_state(path)
        assert result is None
