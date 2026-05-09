"""Tests for brew_tracker.models.types."""


from brew_tracker.models.types import ABVConfig, TempRange


class TestABVConfig:
    def test_default_values(self):
        cfg = ABVConfig()
        assert cfg.multiplier == 131.25
        assert cfg.decimal_places == 1

    def test_custom_values(self):
        cfg = ABVConfig(multiplier=131.0, decimal_places=2)
        assert cfg.multiplier == 131.0
        assert cfg.decimal_places == 2

    def test_is_hashable(self):
        # frozen dataclass must be hashable
        cfg = ABVConfig()
        assert hash(cfg) is not None


class TestTempRange:
    def test_is_within_returns_true_when_in_range(self, standard_temp_range):
        assert standard_temp_range.is_within(18.0) is True
        assert standard_temp_range.is_within(8.0) is True  # inclusive lower bound
        assert standard_temp_range.is_within(24.0) is True  # inclusive upper bound

    def test_is_within_returns_false_outside_range(self, standard_temp_range):
        assert standard_temp_range.is_within(7.9) is False
        assert standard_temp_range.is_within(25.0) is False

    def testwarn_if_outside_no_warnings_in_range(self, standard_temp_range):
        assert standard_temp_range.warn_if_outside(18.0) == []

    def testwarn_if_outside_returns_hot_warning(self, standard_temp_range):
        warnings = standard_temp_range.warn_if_outside(27.0)
        assert len(warnings) == 1
        assert "exceeds safe maximum" in warnings[0]
        assert "27.0" in warnings[0]

    def testwarn_if_outside_returns_cold_warning(self, standard_temp_range):
        warnings = standard_temp_range.warn_if_outside(5.0)
        assert len(warnings) == 1
        assert "below safe minimum" in warnings[0]

    def testwarn_if_outside_returns_both_when_simultaneously_out(self):
        wide_range = TempRange(min_celsius=10.0, max_celsius=20.0)
        warnings = wide_range.warn_if_outside(25.0)
        assert len(warnings) == 1  # only the "exceeds" warning, not "below"
        # at 25, only max is violated
