"""Domain models for brew_tracker."""

from dataclasses import dataclass, field
from datetime import datetime

from brew_tracker.models.types import ABVConfig, TempRange, DEFAULT_TEMP_RANGE


@dataclass
class Ingredient:
    """A single ingredient in a recipe."""

    name: str
    amount_kg: float
    unit: str = "kg"  # kg, g, packets, etc.

    @property
    def amount_grams(self) -> float:
        if self.unit == "kg":
            return self.amount_kg * 1000
        return self.amount_kg

    def to_dict(self) -> dict:
        return {"name": self.name, "amount_kg": self.amount_kg, "unit": self.unit}

    @staticmethod
    def from_dict(data: dict) -> "Ingredient":
        return Ingredient(
            name=data["name"],
            amount_kg=float(data.get("amount_kg", data.get("amount", 0))),
            unit=data.get("unit", "kg"),
        )


@dataclass
class Recipe:
    """A brewing recipe."""

    name: str
    style: str
    batch_size_liters: float
    original_gravity: float
    final_gravity: float
    ingredients: list[Ingredient] = field(default_factory=list)
    notes: str = ""
    id: int | None = None
    created_at: datetime = field(default_factory=datetime.now)
    brew_count: int = 0
    last_brewed: datetime | None = None
    rating: int | None = None
    # runtime fields — not persisted directly
    _abv_config: ABVConfig = field(default=ABVConfig(), repr=False)

    @property
    def abv(self) -> float:
        # Local import to avoid circular dependency with services package
        from brew_tracker.services.abv import calculate_abv

        return calculate_abv(
            self.original_gravity, self.final_gravity, self._abv_config
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "style": self.style,
            "batch_size_liters": self.batch_size_liters,
            "original_gravity": self.original_gravity,
            "final_gravity": self.final_gravity,
            "abv": self.abv,
            "ingredients": [i.to_dict() for i in self.ingredients],
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "brew_count": self.brew_count,
            "last_brewed": self.last_brewed.isoformat() if self.last_brewed else None,
            "rating": self.rating,
        }

    @staticmethod
    def from_dict(data: dict, abv_config: ABVConfig = ABVConfig()) -> "Recipe":
        ingredients = [Ingredient.from_dict(i) for i in data.get("ingredients", [])]
        return Recipe(
            id=data.get("id"),
            name=data["name"],
            style=data["style"],
            batch_size_liters=float(data["batch_size_liters"]),
            original_gravity=float(data["original_gravity"]),
            final_gravity=float(data["final_gravity"]),
            ingredients=ingredients,
            notes=data.get("notes", ""),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else datetime.now(),
            brew_count=data.get("brew_count", 0),
            last_brewed=datetime.fromisoformat(data["last_brewed"])
            if data.get("last_brewed")
            else None,
            rating=data.get("rating"),
            _abv_config=abv_config,
        )


@dataclass
class FermentationLog:
    """A single fermentation temperature reading."""

    recipe_name: str
    temperature: float
    timestamp: datetime
    day: int = 1
    notes: str = ""
    # runtime-only: not persisted
    temp_range: TempRange = field(default=DEFAULT_TEMP_RANGE, repr=False)

    def to_dict(self) -> dict:
        return {
            "recipe_name": self.recipe_name,
            "temperature": self.temperature,
            "timestamp": self.timestamp.isoformat(),
            "day": self.day,
            "notes": self.notes,
        }

    @staticmethod
    def from_dict(
        data: dict, temp_range: TempRange = DEFAULT_TEMP_RANGE
    ) -> "FermentationLog":
        return FermentationLog(
            recipe_name=data["recipe_name"],
            temperature=float(data["temperature"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            day=data.get("day", 1),
            notes=data.get("notes", ""),
            temp_range=temp_range,
        )

    @property
    def warnings(self) -> list[str]:
        return self.temp_range.warn_if_outside(self.temperature)


class FermentationStatus:
    """Enum-like for fermentation status."""

    NO_DATA = "no_data"
    STALE = "stale"
    ACTIVE = "active"
    STABLE = "stable"
