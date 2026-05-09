"""Shared types and constants for brew_tracker."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ABVConfig:
    """ABV calculation constants."""

    multiplier: float = 131.25
    decimal_places: int = 1


@dataclass(frozen=True)
class TempRange:
    """Safe fermentation temperature range."""

    min_celsius: float
    max_celsius: float

    def is_within(self, temp: float) -> bool:
        return self.min_celsius <= temp <= self.max_celsius

    def warn_if_outside(self, temp: float) -> list[str]:
        warnings = []
        if temp > self.max_celsius:
            warnings.append(
                f"Temperature ({temp}°C) exceeds safe maximum ({self.max_celsius}°C) — risk of off-flavors."
            )
        if temp < self.min_celsius:
            warnings.append(
                f"Temperature ({temp}°C) below safe minimum ({self.min_celsius}°C) — fermentation may stall."
            )
        return warnings


# Default thresholds. Replace with style-specific ranges at runtime.
DEFAULT_TEMP_RANGE = TempRange(min_celsius=8.0, max_celsius=24.0)

# How many recent temp readings to consider for stability check
STABILITY_WINDOW = 5
STABILITY_THRESHOLD_CELSIUS = 0.5  # range must be >= this to be "stable"
STALE_HOURS = 48
