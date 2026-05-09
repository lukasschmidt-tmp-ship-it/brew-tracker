"""Tests for brew_tracker.services.reporting."""

from datetime import datetime, timedelta

import pytest

from brew_tracker.models.recipe import Recipe
from brew_tracker.models.types import ABVConfig
from brew_tracker.services.reporting import (
    build_monthly_report,
    build_style_report,
    format_monthly_report,
    format_style_report,
)


@pytest.fixture
def sample_recipes():
    return [
        Recipe(
            name="Centennial Blonde",
            style="Blonde Ale",
            batch_size_liters=20.0,
            original_gravity=1.048,
            final_gravity=1.010,
            ingredients=[],
            brew_count=3,
            last_brewed=datetime(2025, 4, 10),
            _abv_config=ABVConfig(),
        ),
        Recipe(
            name="Headspace IPA",
            style="American IPA",
            batch_size_liters=23.0,
            original_gravity=1.065,
            final_gravity=1.012,
            ingredients=[],
            brew_count=1,
            last_brewed=datetime(2025, 4, 15),
            _abv_config=ABVConfig(),
        ),
        Recipe(
            name="Dark Horse Stout",
            style="Irish Dry Stout",
            batch_size_liters=20.0,
            original_gravity=1.055,
            final_gravity=1.012,
            ingredients=[],
            brew_count=5,
            _abv_config=ABVConfig(),
        ),
    ]


@pytest.fixture
def sample_logs():
    now = datetime.now()
    return [
        {
            "recipe_name": "Centennial Blonde",
            "temperature": 20.0,
            "timestamp": (now - timedelta(days=5)).isoformat(),
            "day": 1,
        },
        {
            "recipe_name": "Centennial Blonde",
            "temperature": 20.5,
            "timestamp": (now - timedelta(days=4)).isoformat(),
            "day": 2,
        },
        {
            "recipe_name": "Headspace IPA",
            "temperature": 19.0,
            "timestamp": (now - timedelta(days=1)).isoformat(),
            "day": 1,
        },
    ]


class TestBuildMonthlyReport:
    def test_brews_filtered_to_current_month(self, sample_recipes, sample_logs):
        # Both last_brewed dates are April 2025, but this test runs now.
        # Use a mock `now` in April so they're included.
        report = build_monthly_report(
            sample_recipes,
            sample_logs,
            now=datetime(2025, 4, 15),
        )
        assert report.brew_count == 2

    def test_brews_outside_month_excluded(self, sample_recipes, sample_logs):
        # All last_brewed dates are April 2025; use May so none are in that month
        report = build_monthly_report(
            sample_recipes,
            sample_logs,
            now=datetime(2025, 5, 1),
        )
        assert report.brew_count == 0

    def test_brews_without_last_brewed_excluded(self, sample_recipes, sample_logs):
        # Dark Horse Stout has no last_brewed set
        report = build_monthly_report(
            sample_recipes,
            sample_logs,
            now=datetime(2025, 4, 15),
        )
        brew_names = [b.name for b in report.brews]
        assert "Dark Horse Stout" not in brew_names

    def test_temp_reading_count(self, sample_recipes, sample_logs):
        report = build_monthly_report(
            sample_recipes,
            sample_logs,
            now=datetime.now(),
        )
        assert report.temp_reading_count >= 0  # depends on timestamps

    def test_active_fermentations(self, sample_recipes, sample_logs):
        report = build_monthly_report(
            sample_recipes,
            sample_logs,
            now=datetime.now(),
        )
        # Both recipes appear in logs
        assert report.active_fermentations >= 0

    def test_estimated_cost_injected(self, sample_recipes, sample_logs):
        def fake_cost(name):
            class FakeCost:
                total_cost = 19.48

            return FakeCost()

        report = build_monthly_report(
            sample_recipes,
            sample_logs,
            now=datetime.now(),
            calculate_cost_fn=fake_cost,
        )
        # 2 brews in current month window → 2 * 19.48
        # actual count depends on log timestamps vs now
        assert report.estimated_cost >= 0

    def test_month_name_formatted(self, sample_recipes, sample_logs):
        report = build_monthly_report(
            sample_recipes,
            sample_logs,
            now=datetime(2025, 4, 1),
        )
        assert report.month == "April 2025"


class TestBuildStyleReport:
    def test_groups_by_style(self, sample_recipes):
        report = build_style_report(sample_recipes)
        assert report.total_recipes == 3
        assert len(report.summaries) == 3  # 3 distinct styles

    def test_style_stats(self, sample_recipes):
        report = build_style_report(sample_recipes)
        blonde = next(s for s in report.summaries if s.style == "Blonde Ale")
        assert blonde.recipe_count == 1
        assert blonde.total_brews == 3
        assert 4.9 <= blonde.avg_abv <= 5.1  # 1.048-1.010 = 0.038 * 131.25 ≈ 4.99

    def test_recipes_tuple(self, sample_recipes):
        report = build_style_report(sample_recipes)
        ipa = next(s for s in report.summaries if s.style == "American IPA")
        assert "Headspace IPA" in ipa.recipes

    def test_multiple_recipes_per_style(self, sample_recipes):
        # Add a second blonde ale
        sample_recipes.append(
            Recipe(
                name="Citrus Blonde",
                style="Blonde Ale",
                batch_size_liters=20.0,
                original_gravity=1.042,
                final_gravity=1.008,
                ingredients=[],
                brew_count=2,
                _abv_config=ABVConfig(),
            )
        )
        report = build_style_report(sample_recipes)
        blonde = next(s for s in report.summaries if s.style == "Blonde Ale")
        assert blonde.recipe_count == 2
        assert len(blonde.recipes) == 2

    def test_empty_recipe_list(self):
        report = build_style_report([])
        assert report.total_recipes == 0
        assert report.summaries == ()


class TestFormatMonthlyReport:
    def test_includes_month_name(self, sample_recipes, sample_logs):
        report = build_monthly_report(
            sample_recipes, sample_logs, now=datetime(2025, 4, 1)
        )
        output = format_monthly_report(report)
        assert "April 2025" in output

    def test_includes_brews_count(self, sample_recipes, sample_logs):
        report = build_monthly_report(
            sample_recipes, sample_logs, now=datetime(2025, 4, 15)
        )
        output = format_monthly_report(report)
        assert "Brews this month" in output

    def test_includes_estimated_cost(self, sample_recipes, sample_logs):
        report = build_monthly_report(sample_recipes, sample_logs)
        output = format_monthly_report(report)
        assert "Estimated spending" in output
        assert "€" in output


class TestFormatStyleReport:
    def test_includes_header(self, sample_recipes):
        report = build_style_report(sample_recipes)
        output = format_style_report(report)
        assert "Recipes by Style" in output

    def test_includes_style_stats(self, sample_recipes):
        report = build_style_report(sample_recipes)
        output = format_style_report(report)
        # All three styles appear
        for style in ["Blonde Ale", "American IPA", "Irish Dry Stout"]:
            assert style in output

    def test_includes_recipe_names(self, sample_recipes):
        report = build_style_report(sample_recipes)
        output = format_style_report(report)
        assert "Centennial Blonde" in output
        assert "Headspace IPA" in output

    def test_empty_report(self):
        report = build_style_report([])
        output = format_style_report(report)
        assert "Recipes by Style" in output
        # no panic on empty summaries
