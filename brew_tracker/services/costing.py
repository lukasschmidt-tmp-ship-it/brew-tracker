"""Recipe cost calculation service."""

from __future__ import annotations

from dataclasses import dataclass

from brew_tracker.services.pricing import PricingService
from brew_tracker.config import WATER_COST_PER_LITER, ENERGY_COST_PER_BATCH


@dataclass(frozen=True)
class CostBreakdown:
    """Itemised cost result for a single ingredient line."""

    name: str
    amount_kg: float
    price_per_kg: float | None
    canonical_key: str | None
    cost: float
    price_unknown: bool


@dataclass(frozen=True)
class RecipeCost:
    """Full cost report for a recipe."""

    recipe_name: str
    batch_size_liters: float
    ingredients_cost: float
    water_cost: float
    energy_cost: float
    total_cost: float
    cost_per_liter: float
    breakdown: list[CostBreakdown]
    unknown_ingredients: list[str]  # names with no price found

    @property
    def has_unknown_prices(self) -> bool:
        return bool(self.unknown_ingredients)


def calculate_recipe_cost(
    recipe,  # type: ignore[no-redef]  # "Recipe" is imported below to avoid circular dep
    pricing: PricingService,
    water_cost_per_liter: float = WATER_COST_PER_LITER,
    energy_cost: float = ENERGY_COST_PER_BATCH,
) -> RecipeCost:
    """
    Compute full cost breakdown for a recipe.

    Args:
        recipe: Recipe object with ingredients list.
        pricing: PricingService with the active price table.
        water_cost_per_liter: Cost per liter of water (default from config).
        energy_cost: Fixed energy cost per batch (default from config).

    Returns:
        RecipeCost with itemised breakdown and totals.

    Raises:
        ValueError: if recipe has no ingredients.
    """
    ingredients = [
        {"name": i.name, "amount_kg": i.amount_kg, "unit": i.unit}
        for i in recipe.ingredients
    ]

    enriched = pricing.lookup_all(ingredients)

    breakdown: list[CostBreakdown] = []
    unknown_ingredients: list[str] = []
    ingredients_cost = 0.0

    for ing in enriched:
        unknown = ing["price_unknown"]
        if unknown:
            unknown_ingredients.append(ing["name"])
        breakdown.append(
            CostBreakdown(
                name=ing["name"],
                amount_kg=float(ing["amount_kg"]),
                price_per_kg=ing["price_per_kg"],
                canonical_key=ing["canonical_key"],
                cost=ing["cost"],
                price_unknown=unknown,
            )
        )
        ingredients_cost += ing["cost"]

    water_cost = round(recipe.batch_size_liters * water_cost_per_liter, 2)
    total_cost = round(ingredients_cost + water_cost + energy_cost, 2)
    cost_per_liter = round(total_cost / recipe.batch_size_liters, 2)

    return RecipeCost(
        recipe_name=recipe.name,
        batch_size_liters=recipe.batch_size_liters,
        ingredients_cost=round(ingredients_cost, 2),
        water_cost=water_cost,
        energy_cost=energy_cost,
        total_cost=total_cost,
        cost_per_liter=cost_per_liter,
        breakdown=breakdown,
        unknown_ingredients=unknown_ingredients,
    )


def format_cost_report(cost: RecipeCost) -> str:
    """Render a RecipeCost into a human-readable string."""

    lines = [
        f"{'=' * 50}",
        f"Cost Report: {cost.recipe_name}",
        f"{'=' * 50}",
        "",
        "Ingredients:",
    ]

    for item in cost.breakdown:
        if item.price_unknown:
            price_str = "(price unknown)"
        else:
            price_str = f"€{item.price_per_kg:.2f}/kg"
        cost_str = f"€{item.cost:.2f}" if item.cost > 0 else "(no cost)"
        lines.append(
            f"  {item.name:<25} {item.amount_kg:.3f} kg × {price_str} = {cost_str}"
        )

    lines.extend(
        [
            "",
            f"  {'Water':<25} €{cost.water_cost:.2f}",
            f"  {'Energy (est.)':<25} €{cost.energy_cost:.2f}",
            "",
            f"  {'TOTAL':<25} €{cost.total_cost:.2f}",
            f"  {'Per liter':<25} €{cost.cost_per_liter:.2f}/L",
            f"{'=' * 50}",
        ]
    )

    if cost.unknown_ingredients:
        lines.append("")
        lines.append(f"⚠️  No price found for: {', '.join(cost.unknown_ingredients)}")

    return "\n".join(lines)
