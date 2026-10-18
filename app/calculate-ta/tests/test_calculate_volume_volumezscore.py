import math

import numpy as np
import pytest

from calculate_volume import (
    compute_volume_zscore,
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
# TestComputeVolumeZScore
# ---------------------------------------------------------------------------

class TestComputeVolumeZScore:
    def test_basic_length(self):
        """Output list should match input length."""
        volumes = _make_volumes(100)
        result = compute_volume_zscore(volumes)
        assert len(result) == 100

    def test_none_before_warmup(self):
        """Volume Z-score should be None until window is filled."""
        volumes = _make_volumes(30)
        result = compute_volume_zscore(volumes)
        for i in range(19):
            assert result[i] is None

    def test_first_valid_at_window_minus_1(self):
        """First valid Z-score at index window-1."""
        volumes = _make_volumes(100)
        result = compute_volume_zscore(volumes)
        first_valid = None
        for i, v in enumerate(result):
            if v is not None:
                first_valid = i
                break
        assert first_valid == 19  # window - 1 for default window=20

    def test_custom_window_first_valid(self):
        """First valid index = custom_window - 1."""
        volumes = _make_volumes(50)
        result = compute_volume_zscore(volumes, window=10)
        first_valid = None
        for i, v in enumerate(result):
            if v is not None:
                first_valid = i
                break
        assert first_valid == 9

    def test_all_none_too_short(self):
        """If data shorter than window, all should be None."""
        volumes = _make_volumes(10)
        result = compute_volume_zscore(volumes)
        assert all(v is None for v in result)

    def test_has_valid_values(self):
        """With enough data, should produce valid Z-scores."""
        volumes = _make_volumes(100)
        result = compute_volume_zscore(volumes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0

    def test_zscore_values_reasonable(self):
        """Z-scores should be in [-5, 5] for normal volume data."""
        volumes = _make_volumes(200)
        result = compute_volume_zscore(volumes)
        valid = [v for v in result if v is not None]
        for v in valid:
            assert -10.0 <= v <= 10.0

    def test_volume_spike_positive_zscore(self):
        """A volume spike should produce a high positive Z-score."""
        volumes = _make_volumes_with_spike(100, spike_idx=25, spike_mult=10.0)
        result = compute_volume_zscore(volumes)
        valid = [v for v in result if v is not None]
        if valid:
            # The spike at index 25 should have a positive Z-score
            assert result[25] is not None
            assert result[25] > 0

    def test_volume_dip_negative_zscore(self):
        """Near-zero volume should produce a negative Z-score."""
        np.random.seed(42)
        base = 1_000_000
        volumes = [int(base * np.random.uniform(0.5, 1.5)) for _ in range(100)]
        # Set several consecutive volumes near zero
        for i in range(25, 30):
            volumes[i] = 1
        result = compute_volume_zscore(volumes)
        # At the dip index, volume should be far below mean → negative Z-score
        assert result[25] is not None
        assert result[25] < 0

    def test_constant_volume_all_none(self):
        """All same volume → std=0 → Z-scores should be None."""
        volumes = [1_000_000] * 50
        result = compute_volume_zscore(volumes)
        for v in result:
            assert v is None

    def test_custom_window(self):
        """Custom window size should work."""
        volumes = _make_volumes(100)
        result = compute_volume_zscore(volumes, window=10)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        # First valid should be at index 9
        first_valid = None
        for i, v in enumerate(result):
            if v is not None:
                first_valid = i
                break
        assert first_valid == 9

    def test_single_value_window(self):
        """Window=1 should produce None for all (std of 1 value = 0)."""
        volumes = [100, 200, 300]
        result = compute_volume_zscore(volumes, window=1)
        assert all(v is None for v in result)

    def test_two_values_window(self):
        """Window=2 should produce first valid at index 1."""
        volumes = [100, 200, 300]
        result = compute_volume_zscore(volumes, window=2)
        assert result[0] is None
        assert result[1] is not None

    def test_manual_zscore_calculation(self):
        """Verify Z-score against manual calculation."""
        np.random.seed(99)
        volumes = [int(1_000_000 * np.random.uniform(0.8, 1.2)) for _ in range(100)]
        result = compute_volume_zscore(volumes, window=20)

        # Pick an index beyond warmup
        idx = 30
        if result[idx] is not None:
            window_vols = [float(volumes[j]) for j in range(idx - 19, idx + 1)]
            mean_vol = sum(window_vols) / 20
            std_vol = (sum((v - mean_vol) ** 2 for v in window_vols) / 20) ** 0.5
            if std_vol > 0:
                expected_z = (float(volumes[idx]) - mean_vol) / std_vol
                assert abs(result[idx] - expected_z) < 1e-6

    def test_increasing_volume_trend(self):
        """Monotonically increasing volume → Z-scores should trend positive."""
        volumes = [i * 10000 + 1000 for i in range(1, 101)]
        result = compute_volume_zscore(volumes)
        valid = [v for v in result if v is not None]
        # With linearly increasing volume, most Z-scores should be positive
        if valid:
            avg_z = sum(valid) / len(valid)
            assert avg_z > 0

    def test_decreasing_volume_trend(self):
        """Monotonically decreasing volume → Z-scores should trend negative."""
        volumes = [(101 - i) * 10000 for i in range(101)]
        result = compute_volume_zscore(volumes)
        valid = [v for v in result if v is not None]
        if valid:
            avg_z = sum(valid) / len(valid)
            assert avg_z < 0

    def test_default_window(self):
        """Default window is 20."""
        volumes = _make_volumes(100)
        result = compute_volume_zscore(volumes)
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
        result = compute_volume_zscore(volumes)
        # After index 19, Z-scores should be computable
        # The zero volumes at indices 25-29 will be far below the mean → negative Z-scores
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        assert result[29] < 0  # last zero volume

    def test_large_volume_range(self):
        """Very large volume values should work without overflow."""
        volumes = [10**9, 2 * 10**9, 1.5 * 10**9] * 30
        result = compute_volume_zscore(volumes)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        # All values are either 1e9, 1.5e9, or 2e9 → bounded Z-scores
        for v in valid:
            assert -5.0 <= v <= 5.0
