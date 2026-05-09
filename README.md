# brew-tracker

Homebrewing recipe manager with fermentation tracking, cost analysis, and reporting.

## Install

```bash
pip install -e .
```

For development (tests, linting):

```bash
pip install -e ".[dev]"
```

## Usage

### Recipe management

```bash
# Add a recipe (ingredients via stdin as JSON)
brew-tracker add "Centennial Blonde" "Blonde Ale" 20 1.048 1.010 \
  --ingredients '[{"name": "pilsner_malt", "amount_kg": 4.5}]'

# List all recipes
brew-tracker list

# List recipes filtered by style
brew-tracker list --style IPA

# Show a recipe
brew-tracker show "Centennial Blonde"

# Delete a recipe
brew-tracker delete "Centennial Blonde"
```

### Fermentation tracking

```bash
# Log a fermentation temperature reading
brew-tracker log "Centennial Blonde" 20.0

# Log with a note
brew-tracker log "Centennial Blonde" 21.5 "Krausen visible"

# View fermentation history and stats
brew-tracker history "Centennial Blonde"
```

### Cost analysis

```bash
# Cost breakdown for a recipe
brew-tracker cost "Centennial Blonde"

# Update an ingredient price
brew-tracker price "citra" 42.00
```

### Reporting

```bash
# Monthly activity report
brew-tracker report

# Recipes grouped by style with ABV stats
brew-tracker styles

# Search recipes by name, style, notes, or ingredient
brew-tracker search "citra"
```

## Run tests

```bash
python -m pytest tests/
```

With coverage:

```bash
pip install pytest-cov
python -m pytest tests/ --cov=brew_tracker --cov-report=term-missing
```