"""Pricing lookup service — no silent substring matching."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PriceResult:
    """Result of a price lookup."""

    price: float | None
    canonical_key: str | None
    unknown: bool = field(init=False)

    def __post_init__(self):
        self.unknown = self.price is None

    def __bool__(self) -> bool:
        return self.price is not None


def _normalize(name: str) -> str:
    return name.lower().strip().replace(" ", "_").replace("-", "_")


class PricingService:
    """
    Three-tier price lookup. Each tier is explicit — no substring guessing.

    Tier 1: exact match against normalized key
    Tier 2: alias map (user-defined, auditable)
    Tier 3: unknown — returns None, never guesses
    """

    def __init__(
        self,
        price_table: dict[str, float],
        aliases: dict[str, str] | None = None,
    ):
        self._prices = price_table
        # Canonical key map: "what the user types" → "key in price_table"
        self._aliases: dict[str, str] = dict(aliases) if aliases else {}

        # Seed aliases: every price_table key is also a valid alias for itself,
        # so "pilsner_malt" and "pilsner" both hit the same entry.
        for key in self._prices:
            if key not in self._aliases:
                self._aliases[key] = key

    def lookup(self, ingredient_name: str) -> PriceResult:
        """
        Look up a single ingredient price.

        Returns PriceResult(price, canonical_key) or PriceResult(None, None).
        """
        key = _normalize(ingredient_name)

        # Tier 1: exact key
        if key in self._prices:
            return PriceResult(price=self._prices[key], canonical_key=key)

        # Tier 2: alias
        if key in self._aliases:
            canonical = self._aliases[key]
            if canonical in self._prices:
                return PriceResult(
                    price=self._prices[canonical], canonical_key=canonical
                )

        # Tier 3: not found
        return PriceResult(price=None, canonical_key=None)

    def lookup_all(self, ingredients: list[dict]) -> list[dict]:
        """
        Bulk price lookup for a list of ingredient dicts.

        Each dict must have 'name' (and optionally 'amount_kg' / 'amount').
        Returns enriched list with 'price_per_kg', 'cost', 'price_unknown' added.
        """
        results = []
        for ing in ingredients:
            amount_kg = float(ing.get("amount_kg", ing.get("amount", 0)))
            result = self.lookup(ing["name"])
            cost = amount_kg * result.price if result.price is not None else 0.0
            results.append(
                {
                    **ing,
                    "price_per_kg": result.price,
                    "canonical_key": result.canonical_key,
                    "cost": round(cost, 2),
                    "price_unknown": result.unknown,
                }
            )
        return results

    def add_alias(self, alias: str, canonical: str) -> None:
        """Register an alias at runtime (e.g. from a config file)."""
        self._aliases[_normalize(alias)] = _normalize(canonical)
