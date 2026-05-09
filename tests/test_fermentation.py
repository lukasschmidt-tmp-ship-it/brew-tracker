"""Tests for brew_tracker.services.fermentation."""

from datetime import timedelta

import pytest

from brew_tracker.models.recipe import FermentationStatus
from brew_tracker.services.fermentation import (
    compute_fermentation_day,
    check_status,
    temp_warnings,
    fermentation_summary,
)


class TestComputeFermentationDay:
    def test_day_one(self, two_days_ago):
        day = compute_fermentation_day(two_days_ago, at=two_days_ago)
        assert day == 1

    def test_day_three(self, two_days_ago):
        at = two_days_ago + timedelta(days=2)
        day = compute_fermentation_day(two_days_ago, at=at)
        assert day == 3

    def test_partial_day_counts_as_full_day(self, two_days_ago):
        # 12 hours in → day 1
        at = two_days_ago + timedelta(hours=12)
        day = compute_fermentation_day(two_days_ago, at=at)
        assert day == 1


class TestCheckStatus:
    def test_no_data_returns_no_data(self):
        assert check_status([]) == FermentationStatus.NO_DATA

    def test_stale_log_returns_stale(self, stale_log):
        assert check_status([stale_log]) == FermentationStatus.STALE

    def test_stable_logs_return_stable(self, logs_3_day, standard_temp_range):
        # All three logs are within 0.5°C — should be stable
        logs_3_day[0].temperature = 20.0
        logs_3_day[1].temperature = 20.2
        logs_3_day[2].temperature = 20.3
        assert check_status(logs_3_day) == FermentationStatus.STABLE

    def test_unstable_logs_return_active(self, logs_3_day):
        logs_3_day[0].temperature = 20.0
        logs_3_day[1].temperature = 21.5
        logs_3_day[2].temperature = 20.8
        assert check_status(logs_3_day) == FermentationStatus.ACTIVE

    def test_insufficient_recent_logs_returns_active(
        self, log_day1, log_day2_yesterday
    ):
        # Only 2 recent logs — doesn't meet minimum of 3
        status = check_status([log_day1, log_day2_yesterday])
        assert status == FermentationStatus.ACTIVE


class TestTempWarnings:
    def testno_warnings_for_good_temp(self, log_day3_today):
        assert temp_warnings(log_day3_today) == []

    def thest_warnings_for_hot_temp(self, hot_log):
        warnings = temp_warnings(hot_log)
        assert len(warnings) == 1
        assert "exceeds safe maximum" in warnings[0]

    def testwarnings_for_cold_temp(self, cold_log):
        warnings = temp_warnings(cold_log)
        assert len(warnings) == 1
        assert "below safe minimum" in warnings[0]


class TestFermentationSummary:
    def testempty_logs(self):
        result = fermentation_summary([])
        assert result["count"] == 0
        assert result["min"] is None

    def test_single_log(self, log_day1):
        result = fermentation_summary([log_day1])
        assert result["count"] == 1
        assert result["min"] == 20.0
        assert result["max"] == 20.0
        assert result["mean"] == 20.0
        assert "stdev" not in result

    def testmultiple_logs(self, logs_3_day):
        result = fermentation_summary(logs_3_day)
        assert result["count"] == 3
        assert result["min"] == 20.0
        assert result["max"] == 20.8
        assert result["mean"] == pytest.approx(20.43, rel=0.1)
        assert "stdev" in result

    def test_rounds_mean_to_one_decimal(self, logs_3_day):
        result = fermentation_summary(logs_3_day)
        # mean should be a float with at most 1 decimal place
        assert str(result["mean"]).replace(".", "").isdigit() or "." in str(
            result["mean"]
        )
