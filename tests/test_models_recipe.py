"""Tests for brew_tracker.models.recipe."""

from datetime import datetime

import pytest

from brew_tracker.models.recipe import (
    Ingredient,
    Recipe,
    FermentationLog,
    FermentationStatus,
)
from brew_tracker.models.types import ABVConfig


class TestIngredient:
    def test_to_dict(self):
        ing = Ingredient("pilsner_malt", 4.5, "kg")
        d = ing.to_dict()
        assert d == {"name": "pilsner_malt", "amount_kg": 4.5, "unit": "kg"}

    def test_from_dict(self):
        d = {"name": "citra", "amount_kg": 0.06, "unit": "kg"}
        ing = Ingredient.from_dict(d)
        assert ing.name == "citra"
        assert ing.amount_kg == 0.06

    def test_from_dict_falls_back_to_amount_field(self):
        d = {"name": "safale_us05", "amount": 2}
        ing = Ingredient.from_dict(d)
        assert ing.amount_kg == 2.0

    def test_amount_grams_converts_from_kg(self):
        ing = Ingredient("pale_ale_malt", 5.5)
        assert ing.amount_grams == 5500.0

    def test_amount_grams_passes_through_when_unit_is_not_kg(self):
        ing = Ingredient("safale_us05", 2, "packets")
        assert ing.amount_grams == 2


class TestRecipe:
    def test_abv_property(self, pale_ale_recipe):
        # OG 1.048, FG 1.010 → (1.048 - 1.010) * 131.25 ≈ 4.99
        assert pale_ale_recipe.abv == pytest.approx(5.0, rel=0.1)

    def test_to_dict(self, pale_ale_recipe):
        d = pale_ale_recipe.to_dict()
        assert d["name"] == "Centennial Blonde"
        assert d["style"] == "Blonde Ale"
        assert d["abv"] == pale_ale_recipe.abv
        assert len(d["ingredients"]) == 3

    def test_to_dict_roundtrip(self, pale_ale_recipe):
        d = pale_ale_recipe.to_dict()
        recreated = Recipe.from_dict(d)
        assert recreated.name == pale_ale_recipe.name
        assert recreated.batch_size_liters == pale_ale_recipe.batch_size_liters
        assert recreated.original_gravity == pale_ale_recipe.original_gravity

    def test_from_dict(self, pale_ale_dict):
        recipe = Recipe.from_dict(pale_ale_dict)
        assert recipe.name == "Centennial Blonde"
        assert recipe.batch_size_liters == 20.0
        assert recipe.original_gravity == 1.048
        assert len(recipe.ingredients) == 3

    def test_from_dict_missing_optional_fields(self):
        minimal = {
            "name": "Minimal Recipe",
            "style": "Pilsner",
            "batch_size_liters": 20,
            "original_gravity": 1.045,
            "final_gravity": 1.008,
        }
        recipe = Recipe.from_dict(minimal)
        assert recipe.notes == ""
        assert recipe.brew_count == 0
        assert recipe.rating is None

    def test_abv_uses_config(self, ipa_recipe):
        cfg = ABVConfig(multiplier=131.0, decimal_places=2)
        ipa_recipe._abv_config = cfg
        # (1.065 - 1.012) * 131 = 6.943 → 6.94
        assert ipa_recipe.abv == pytest.approx(6.94, rel=0.01)


class TestFermentationLog:
    def test_to_dict(self, log_day1):
        d = log_day1.to_dict()
        assert d["recipe_name"] == "Centennial Blonde"
        assert d["temperature"] == 20.0
        assert d["day"] == 1

    def test_from_dict(self, standard_temp_range):
        d = {
            "recipe_name": "Test IPA",
            "temperature": 19.5,
            "timestamp": "2025-05-01T14:00:00",
            "day": 2,
            "notes": "Krausen visible",
        }
        log = FermentationLog.from_dict(d, standard_temp_range)
        assert log.temperature == 19.5
        assert log.day == 2
        assert log.notes == "Krausen visible"

    def testwarnings_returns_empty_list_in_range(self, standard_temp_range):
        log = FermentationLog(
            recipe_name="Test",
            temperature=20.0,
            timestamp=datetime.now(),
            temp_range=standard_temp_range,
        )
        assert log.warnings == []

    def testwarnings_returns_hot_warning(self, hot_log):
        assert len(hot_log.warnings) == 1
        assert "exceeds safe maximum" in hot_log.warnings[0]

    def testwarnings_returns_cold_warning(self, cold_log):
        assert len(cold_log.warnings) == 1
        assert "below safe minimum" in cold_log.warnings[0]


class TestFermentationStatus:
    def test_status_values_are_strings(self):
        assert FermentationStatus.ACTIVE == "active"
        assert FermentationStatus.STABLE == "stable"
        assert FermentationStatus.STALE == "stale"
        assert FermentationStatus.NO_DATA == "no_data"
