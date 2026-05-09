"""Tests for brew_tracker.services.abv."""


from brew_tracker.models.types import ABVConfig
from brew_tracker.services.abv import calculate_abv


class TestCalculateABV:
    def test_standard_beer(self):
        # OG 1.050, FG 1.010 → (0.040) * 131.25 = 5.25
        assert calculate_abv(1.050, 1.010) == 5.3

    def test_high_gravity(self):
        # OG 1.080, FG 1.020 → (0.060) * 131.25 = 7.875 → 7.9
        assert calculate_abv(1.080, 1.020) == 7.9

    def test_low_gravity_session_beer(self):
        # OG 1.030, FG 1.005 → (0.025) * 131.25 = 3.28 → 3.3
        assert calculate_abv(1.030, 1.005) == 3.3

    def test_custom_multiplier(self):
        cfg = ABVConfig(multiplier=131.0)
        assert calculate_abv(1.050, 1.010, cfg) == 5.2  # 0.040 * 131 = 5.24

    def test_custom_decimal_places(self):
        cfg = ABVConfig(decimal_places=2)
        result = calculate_abv(1.050, 1.010, cfg)
        assert result == 5.25  # 5.248 → 5.25 with 2dp

    def test_zero_delta_gives_zero_abv(self):
        assert calculate_abv(1.000, 1.000) == 0.0

    def test_negative_delta(self):
        # FG > OG shouldn't happen, but function should handle it gracefully
        result = calculate_abv(1.010, 1.050)
        assert result < 0
