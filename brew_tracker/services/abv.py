"""ABV calculation service."""

from brew_tracker.models.types import ABVConfig


def calculate_abv(
    original_gravity: float,
    final_gravity: float,
    config: ABVConfig = ABVConfig(),
) -> float:
    """
    Calculate alcohol by volume from OG and FG.

    Args:
        original_gravity: Specific gravity pre-fermentation (e.g. 1.050)
        final_gravity: Specific gravity post-fermentation (e.g. 1.010)
        config: ABVConfig with multiplier and decimal places.

    Returns:
        ABV as a percentage, e.g. 5.2
    """
    return round(
        (original_gravity - final_gravity) * config.multiplier, config.decimal_places
    )
