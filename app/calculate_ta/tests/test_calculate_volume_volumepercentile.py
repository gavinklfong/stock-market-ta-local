import math

import numpy as np
import pytest

from calculate_volume import (
    compute_volume_percentile,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_volumes(length, base=1_000_000, noise_range=0.3):
    """Generate volume data with moderate variation."""
    np.random.seed(0)
    return [int(base * np.random.uniform(1 - noise_range, 1 + noise_range))
            for _ in range(length)]


def _make_volumes_with_spike(length, base=1_000_000, spike_idx=25, spike_mult=5.0):
    """Generate volume data with a known spike at spike_idx."""
    volumes = _make_volumes(length, base)
    volumes[spike_idx] = int(base * spike_mult)
    return volumes


# ---------------------------------------------------------------------------
# TestComputeVolumePercentile
# ---------------------------------------------------------------------------

class TestComputeVolumePercentile:
    def test_basic_length(self):
        """Output list should match input length."""
        volumes = _make_volumes(100)
        result = compute_volume_percentile(volumes)
        assert len(result) == 100

    def test_none_before_warmup(self):
        """Volume percentile should be None until window is filled."""
        volumes = _make_volumes(30)
        result = compute_volume_percentile(volumes)
        for i in range(19):
            assert result[i] is None

    def test_first_valid_at_window_minus_1(self):
        """First valid percentile at index window-1."""
        volumes = _make_volumes(100)
        result = compute_volume_percentile(volumes)
        first_valid = None
        for i, v in enumerate(result):
            if v is not None:
                first_valid = i
                break
        assert first_valid == 19  # window - 1 for default window=20

    def test_custom_window_first_valid(self):
        """First valid index = custom_window - 1."""
        volumes = _make_volumes(50)
        result = compute_volume_percentile(volumes, window=10)
        first_valid = None
        for i, v in enumerate(result):
            if v is not None:
                first_valid = i
                break
        assert first_valid == 9

    def test_all_none_too_short(self):
        """If data shorter than window, all should be None."""
        volumes = _make_volumes(10)
        result = compute_volume_percentile(volumes)
        assert all(v is None for v in result)

    def test_has_valid_values(self):
        """With enough data, should produce valid percentiles."""
        volumes = _make_volumes(100)
        result = compute_volume_percentile(volumes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0

    def test_percentile_values_in_range(self):
        """Percentiles should be in [0, 100]."""
        volumes = _make_volumes(200)
        result = compute_volume_percentile(volumes)
        valid = [v for v in result if v is not None]
        for v in valid:
            assert 0 <= v <= 100

    def test_volume_spike_high_percentile(self):
        """A volume spike should produce a high percentile."""
        volumes = _make_volumes_with_spike(100, spike_idx=25, spike_mult=10.0)
        result = compute_volume_percentile(volumes)
        # The spike at index 25 should be higher than most of the window
        if result[25] is not None:
            assert result[25] > 90

    def test_volume_dip_low_percentile(self):
        """Near-zero volume should produce a low percentile."""
        np.random.seed(42)
        base = 1_000_000
        volumes = [int(base * np.random.uniform(0.5, 1.5)) for _ in range(100)]
        # Set several consecutive volumes near zero
        for i in range(25, 30):
            volumes[i] = 1
        result = compute_volume_percentile(volumes)
        # At the dip index, volume should be far below window → low percentile
        assert result[25] is not None
        assert result[25] < 10

    def test_constant_volume_zero_percentile(self):
        """All same volume → percentile should be 0 (nothing is strictly below)."""
        volumes = [1_000_000] * 50
        result = compute_volume_percentile(volumes)
        for i, v in enumerate(result):
            if v is not None:
                assert v == 0.0

    def test_custom_window(self):
        """Custom window size should work."""
        volumes = _make_volumes(100)
        result = compute_volume_percentile(volumes, window=10)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        # First valid should be at index 9
        first_valid = None
        for i, v in enumerate(result):
            if v is not None:
                first_valid = i
                break
        assert first_valid == 9

    def test_monotonically_increasing(self):
        """Monotonically increasing volume → percentile should trend toward 100."""
        volumes = [i * 10000 + 1000 for i in range(1, 101)]
        result = compute_volume_percentile(volumes)
        valid = [v for v in result if v is not None]
        # Last value should be 95% (99/100 values below it in the window)
        assert valid[-1] == 95.0

    def test_monotonically_decreasing(self):
        """Monotonically decreasing volume → percentile should trend toward 0."""
        volumes = [(101 - i) * 10000 for i in range(101)]
        result = compute_volume_percentile(volumes)
        valid = [v for v in result if v is not None]
        # Last value should be 0% (nothing below it)
        assert valid[-1] == 0.0

    def test_manual_percentile_calculation(self):
        """Verify percentile against manual calculation."""
        np.random.seed(99)
        volumes = [int(1_000_000 * np.random.uniform(0.8, 1.2)) for _ in range(100)]
        result = compute_volume_percentile(volumes, window=20)

        # Pick an index beyond warmup
        idx = 30
        if result[idx] is not None:
            window_vols = [float(volumes[j]) for j in range(idx - 19, idx + 1)]
            current_vol = float(volumes[idx])
            below_count = sum(1 for v in window_vols if v < current_vol)
            expected_p = (below_count / 20) * 100.0
            assert abs(result[idx] - expected_p) < 1e-6

    def test_default_window(self):
        """Default window is 20."""
        volumes = _make_volumes(100)
        result = compute_volume_percentile(volumes)
        first_valid = None
        for i, v in enumerate(result):
            if v is not None:
                first_valid = i
                break
        assert first_valid == 19  # 20 - 1

    def test_zero_volume_values(self):
        """Zero volumes should be handled gracefully."""
        np.random.seed(42)
        base = 1_000_000
        volumes = [int(base * np.random.uniform(0.8, 1.2)) for _ in range(25)]
        volumes += [0, 0, 0, 0, 0]
        result = compute_volume_percentile(volumes)
        # The zero volumes should be in the 0th percentile
        assert result[29] is not None
        assert result[29] == 0.0  # nothing below zero in the window

    def test_two_distinct_values(self):
        """Two alternating values should produce predictable percentiles."""
        # Alternating 100, 200 pattern
        volumes = [100 if i % 2 == 0 else 200 for i in range(100)]
        result = compute_volume_percentile(volumes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        # Even indices (value 100) → nothing below → 0th percentile
        # Odd indices (value 200) → half below → 50th percentile
        for i, v in enumerate(valid):
            original_idx = i + 19  # first valid at index 19
            if original_idx % 2 == 0:
                assert v == 0.0, f"Expected 0.0 at index {original_idx}, got {v}"
            else:
                assert v == 50.0, f"Expected 50.0 at index {original_idx}, got {v}"

    def test_large_volume_range(self):
        """Very large volume values should work without overflow."""
        volumes = [10**9, 2 * 10**9, 1.5 * 10**9] * 30
        result = compute_volume_percentile(volumes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        # Percentiles should be bounded and meaningful
        for v in valid:
            assert 0 <= v <= 100

    def test_all_same_except_one(self):
        """One outlier in uniform data should have high percentile."""
        volumes = [1_000_000] * 19 + [100_000_000]  # 20 values
        volumes += [1_000_000] * 80
        result = compute_volume_percentile(volumes)
        # The spike at index 19 should be 95th percentile (19/20 below)
        assert result[19] == 95.0
        # At index 20 the window is [100M, 1M×19], current=1M → 0th percentile
        assert result[20] == 0.0
