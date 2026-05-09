"""Shared fixtures for brew_tracker tests."""

from datetime import datetime, timedelta

import pytest

from brew_tracker.models.recipe import FermentationLog, Recipe, Ingredient
from brew_tracker.models.types import ABVConfig, TempRange


@pytest.fixture
def abv_config():
    return ABVConfig()


@pytest.fixture
def standard_temp_range():
    return TempRange(min_celsius=8.0, max_celsius=24.0)


# ── Recipe fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def pale_ale_recipe() -> Recipe:
    return Recipe(
        id=1,
        name="Centennial Blonde",
        style="Blonde Ale",
        batch_size_liters=20.0,
        original_gravity=1.048,
        final_gravity=1.010,
        ingredients=[
            Ingredient("pilsner_malt", 4.5),
            Ingredient("cascade", 0.025),
            Ingredient("safale_us05", 1),
        ],
        notes="Simple summer ale",
        brew_count=3,
        created_at=datetime(2025, 3, 15),
        _abv_config=ABVConfig(),
    )


@pytest.fixture
def ipa_recipe() -> Recipe:
    return Recipe(
        id=2,
        name="Headspace IPA",
        style="American IPA",
        batch_size_liters=23.0,
        original_gravity=1.065,
        final_gravity=1.012,
        ingredients=[
            Ingredient("pale_ale_malt", 5.5),
            Ingredient("citra", 0.060),
            Ingredient("safale_us05", 1),
        ],
        notes="Dry-hopped at day 5",
        brew_count=1,
        _abv_config=ABVConfig(),
    )


@pytest.fixture
def pale_ale_dict() -> dict:
    return {
        "id": 1,
        "name": "Centennial Blonde",
        "style": "Blonde Ale",
        "batch_size_liters": 20.0,
        "original_gravity": 1.048,
        "final_gravity": 1.010,
        "ingredients": [
            {"name": "pilsner_malt", "amount_kg": 4.5, "unit": "kg"},
            {"name": "cascade", "amount_kg": 0.025, "unit": "kg"},
            {"name": "safale_us05", "amount_kg": 1.0, "unit": "packets"},
        ],
        "notes": "Simple summer ale",
        "created_at": "2025-03-15T10:00:00",
        "brew_count": 3,
        "last_brewed": None,
        "rating": None,
    }


@pytest.fixture
def ipa_dict() -> dict:
    return {
        "id": 2,
        "name": "Headspace IPA",
        "style": "American IPA",
        "batch_size_liters": 23.0,
        "original_gravity": 1.065,
        "final_gravity": 1.012,
        "ingredients": [{"name": "pale_ale_malt", "amount_kg": 5.5, "unit": "kg"}],
        "notes": "",
        "created_at": "2025-04-01T09:00:00",
        "brew_count": 1,
        "last_brewed": None,
        "rating": None,
    }


# ── Fermentation log fixtures ────────────────────────────────────────────────


@pytest.fixture
def now():
    return datetime.now()


@pytest.fixture
def two_days_ago(now):
    return now - timedelta(days=2)


@pytest.fixture
def three_days_ago(now):
    return now - timedelta(days=3)


@pytest.fixture
def log_day1(two_days_ago, standard_temp_range) -> FermentationLog:
    return FermentationLog(
        recipe_name="Centennial Blonde",
        temperature=20.0,
        timestamp=two_days_ago,
        day=1,
        temp_range=standard_temp_range,
    )


@pytest.fixture
def log_day2_yesterday(two_days_ago, standard_temp_range) -> FermentationLog:
    return FermentationLog(
        recipe_name="Centennial Blonde",
        temperature=20.5,
        timestamp=two_days_ago + timedelta(hours=24),
        day=2,
        temp_range=standard_temp_range,
    )


@pytest.fixture
def log_day3_today(two_days_ago, standard_temp_range) -> FermentationLog:
    return FermentationLog(
        recipe_name="Centennial Blonde",
        temperature=20.8,
        timestamp=two_days_ago + timedelta(hours=48),
        day=3,
        temp_range=standard_temp_range,
    )


@pytest.fixture
def logs_3_day(log_day1, log_day2_yesterday, log_day3_today) -> list[FermentationLog]:
    return [log_day1, log_day2_yesterday, log_day3_today]


@pytest.fixture
def stale_log(now, standard_temp_range) -> FermentationLog:
    return FermentationLog(
        recipe_name="Old Batch",
        temperature=18.0,
        timestamp=now - timedelta(hours=60),
        day=4,
        temp_range=standard_temp_range,
    )


@pytest.fixture
def cold_log(standard_temp_range) -> FermentationLog:
    return FermentationLog(
        recipe_name="Cold Batch",
        temperature=5.0,
        timestamp=datetime.now(),
        day=1,
        temp_range=standard_temp_range,
    )


@pytest.fixture
def hot_log(standard_temp_range) -> FermentationLog:
    return FermentationLog(
        recipe_name="Hot Batch",
        temperature=27.0,
        timestamp=datetime.now(),
        day=1,
        temp_range=standard_temp_range,
    )
