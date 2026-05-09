"""Tests for brew_tracker.services.costing."""

import pytest

from brew_tracker.models.recipe import Recipe, Ingredient
from brew_tracker.models.types import ABVConfig
from brew_tracker.services.pricing import PricingService
from brew_tracker.services.costing import (
    calculate_recipe_cost,
    format_cost_report,
    RecipeCost,
    CostBreakdown,
)


@pytest.fixture
def pricing():
    return PricingService(
        {
            "pilsner_malt": 2.50,
            "wheat_malt": 2.80,
            "citra": 45.00,
            "safale_us05": 4.50,
        },
        aliases={"hallertau": "citra"},
    )


@pytest.fixture
def blonde_recipe() -> Recipe:
    return Recipe(
        name="Centennial Blonde",
        style="Blonde Ale",
        batch_size_liters=20.0,
        original_gravity=1.048,
        final_gravity=1.010,
        ingredients=[
            Ingredient("pilsner_malt", 4.5),
            Ingredient("citra", 0.025),
            Ingredient("safale_us05", 1.0),
        ],
        _abv_config=ABVConfig(),
    )


@pytest.fixture
def recipe_with_unknown_ingredient() -> Recipe:
    return Recipe(
        name="Mystery Grain",
        style="Farmhouse",
        batch_size_liters=20.0,
        original_gravity=1.045,
        final_gravity=1.008,
        ingredients=[
            Ingredient("pilsner_malt", 4.5),
            Ingredient("spelt_malt", 0.5),  # not in price table
        ],
        _abv_config=ABVConfig(),
    )


class TestCalculateRecipeCost:
    def test_calculates_ingredient_costs(self, pricing, blonde_recipe):
        cost = calculate_recipe_cost(blonde_recipe, pricing)
        assert cost.recipe_name == "Centennial Blonde"
        assert cost.batch_size_liters == 20.0

    def test_ingredients_cost(self, pricing, blonde_recipe):
        cost = calculate_recipe_cost(blonde_recipe, pricing)
        # pilsner: 4.5 * 2.50 = 11.25
        # citra:   0.025 * 45.00 = 1.125
        # yeast:   1.0 * 4.50 = 4.50
        assert cost.ingredients_cost == pytest.approx(16.88, rel=1e-2)

    def test_water_cost(self, pricing, blonde_recipe):
        cost = calculate_recipe_cost(blonde_recipe, pricing)
        # 20.0 * 0.005 = 0.10
        assert cost.water_cost == 0.10

    def test_energy_cost(self, pricing, blonde_recipe):
        cost = calculate_recipe_cost(blonde_recipe, pricing)
        assert cost.energy_cost == 2.50

    def test_total_cost(self, pricing, blonde_recipe):
        cost = calculate_recipe_cost(blonde_recipe, pricing)
        # 16.875 + 0.10 + 2.50 = 19.475 → 19.48
        assert cost.total_cost == pytest.approx(19.48, rel=1e-2)

    def test_cost_per_liter(self, pricing, blonde_recipe):
        cost = calculate_recipe_cost(blonde_recipe, pricing)
        assert cost.cost_per_liter == pytest.approx(0.97, rel=0.1)

    def test_breakdown_has_all_ingredients(self, pricing, blonde_recipe):
        cost = calculate_recipe_cost(blonde_recipe, pricing)
        assert len(cost.breakdown) == 3
        names = [item.name for item in cost.breakdown]
        assert "pilsner_malt" in names
        assert "citra" in names
        assert "safale_us05" in names

    def test_breakdown_items_have_price_info(self, pricing, blonde_recipe):
        cost = calculate_recipe_cost(blonde_recipe, pricing)
        pilsner_item = next(i for i in cost.breakdown if i.name == "pilsner_malt")
        assert pilsner_item.price_per_kg == 2.50
        assert pilsner_item.price_unknown is False
        assert pilsner_item.cost == pytest.approx(11.25, rel=1e-2)

    def test_unknown_ingredient_flagged(self, pricing, recipe_with_unknown_ingredient):
        cost = calculate_recipe_cost(recipe_with_unknown_ingredient, pricing)
        assert cost.has_unknown_prices is True
        assert "spelt_malt" in cost.unknown_ingredients
        # pilsner_malt is known
        known = [i for i in cost.breakdown if not i.price_unknown]
        assert len(known) == 1
        assert known[0].name == "pilsner_malt"

    def test_unknown_ingredient_has_zero_cost(
        self, pricing, recipe_with_unknown_ingredient
    ):
        cost = calculate_recipe_cost(recipe_with_unknown_ingredient, pricing)
        spelt = next(i for i in cost.breakdown if i.name == "spelt_malt")
        assert spelt.cost == 0.0
        assert spelt.price_unknown is True

    def test_alias_hit_shows_correct_canonical_key(self, pricing, blonde_recipe):
        # "citra" lookup resolves to canonical "citra" — no alias needed
        cost = calculate_recipe_cost(blonde_recipe, pricing)
        citra_item = next(i for i in cost.breakdown if i.name == "citra")
        assert citra_item.canonical_key == "citra"
        assert citra_item.price_per_kg == 45.00

    def test_empty_ingredients(self, pricing):
        recipe = Recipe(
            name="Empty",
            style="Ghost",
            batch_size_liters=20.0,
            original_gravity=1.045,
            final_gravity=1.008,
            ingredients=[],
            _abv_config=ABVConfig(),
        )
        cost = calculate_recipe_cost(recipe, pricing)
        assert cost.ingredients_cost == 0.0
        assert cost.total_cost == pytest.approx(2.60, rel=1e-2)  # water + energy

    def test_custom_water_and_energy_costs(self, pricing, blonde_recipe):
        cost = calculate_recipe_cost(
            blonde_recipe,
            pricing,
            water_cost_per_liter=0.01,
            energy_cost=5.0,
        )
        assert cost.water_cost == 0.20  # 20 * 0.01
        assert cost.energy_cost == 5.0

    def test_returns_recipe_cost_dataclass(self, pricing, blonde_recipe):
        result = calculate_recipe_cost(blonde_recipe, pricing)
        assert isinstance(result, RecipeCost)
        assert isinstance(result.breakdown[0], CostBreakdown)


class TestFormatCostReport:
    def test_renders_recipe_name(self, pricing, blonde_recipe):
        cost = calculate_recipe_cost(blonde_recipe, pricing)
        output = format_cost_report(cost)
        assert "Centennial Blonde" in output

    def test_renders_ingredient_lines(self, pricing, blonde_recipe):
        cost = calculate_recipe_cost(blonde_recipe, pricing)
        output = format_cost_report(cost)
        assert "pilsner_malt" in output
        assert "4.500 kg" in output

    def test_renders_water_and_energy(self, pricing, blonde_recipe):
        cost = calculate_recipe_cost(blonde_recipe, pricing)
        output = format_cost_report(cost)
        assert "Water" in output
        assert "Energy" in output

    def test_renders_total(self, pricing, blonde_recipe):
        cost = calculate_recipe_cost(blonde_recipe, pricing)
        output = format_cost_report(cost)
        assert "TOTAL" in output
        assert "€" in output

    def test_renders_per_liter(self, pricing, blonde_recipe):
        cost = calculate_recipe_cost(blonde_recipe, pricing)
        output = format_cost_report(cost)
        assert "/L" in output

    def test_warns_about_unknown_ingredients(
        self, pricing, recipe_with_unknown_ingredient
    ):
        cost = calculate_recipe_cost(recipe_with_unknown_ingredient, pricing)
        output = format_cost_report(cost)
        assert "⚠️" in output
        assert "spelt_malt" in output

    def test_no_warning_when_all_prices_known(self, pricing, blonde_recipe):
        cost = calculate_recipe_cost(blonde_recipe, pricing)
        output = format_cost_report(cost)
        assert "⚠️" not in output
