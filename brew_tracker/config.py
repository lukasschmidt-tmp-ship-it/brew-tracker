"""Configuration for brew_tracker."""

from pathlib import Path

DATA_FILE = Path("recipes.json")
TEMP_LOG_FILE = Path("fermentation_log.json")
INGREDIENTS_FILE = Path("ingredients.json")

# Default ingredient prices (€/kg or €/unit as noted)
DEFAULT_PRICES: dict[str, float] = {
    "pilsner_malt": 2.50,
    "wheat_malt": 2.80,
    "munich_malt": 3.10,
    "caramunich": 4.20,
    "pale_ale_malt": 2.90,
    "vienna_malt": 3.30,
    "hallertau_mittelfruh": 28.00,
    "tettnang": 30.00,
    "cascade": 25.00,
    "citra": 45.00,
    "saaz": 26.00,
    "safale_us05": 4.50,  # per packet
    "safale_wb06": 5.00,
    "saflager_w34_70": 5.50,
    "wyeast_1007": 8.50,
}

# Fixed per-batch overhead costs (€)
WATER_COST_PER_LITER = 0.005
ENERGY_COST_PER_BATCH = 2.50
