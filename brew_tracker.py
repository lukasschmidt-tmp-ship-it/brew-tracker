#!/usr/bin/env python3
# My brewing tracker - started Jan 2025
# TODO: clean this up someday lol

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import statistics

DATA_FILE = "recipes.json"
TEMP_LOG_FILE = "fermentation_log.json"
INGREDIENTS_FILE = "ingredients.json"

# ingredient prices per kg/L (updated manually, should probably use an API)
DEFAULT_PRICES = {
    "pilsner_malt": 2.50,
    "wheat_malt": 2.80,
    "munich_malt": 3.10,
    "caramunich": 4.20,
    "pale_ale_malt": 2.90,
    "hallertau_mittelfruh": 28.00,  # per kg
    "tettnang": 30.00,
    "cascade": 25.00,
    "citra": 45.00,
    "saaz": 26.00,
    "safale_us05": 4.50,  # per packet
    "safale_wb06": 5.00,
    "saflager_w34_70": 5.50,
    "wyeast_1007": 8.50,
}

def load_data(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return []

def save_data(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def add_recipe(name, style, batch_size, og, fg, ingredients, notes=""):
    recipes = load_data(DATA_FILE)
    # check if recipe already exists
    for r in recipes:
        if r['name'].lower() == name.lower():
            print(f"Recipe '{name}' already exists! Use update_recipe instead.")
            return False
    recipe = {
        'id': len(recipes) + 1,
        'name': name,
        'style': style,
        'batch_size_liters': batch_size,
        'original_gravity': og,
        'final_gravity': fg,
        'abv': round((og - fg) * 131.25, 1),
        'ingredients': ingredients,
        'notes': notes,
        'created_at': datetime.now().isoformat(),
        'brew_count': 0,
        'last_brewed': None,
        'rating': None,
    }
    recipes.append(recipe)
    save_data(DATA_FILE, recipes)
    print(f"Added recipe: {name} ({style}) - {recipe['abv']}% ABV")
    return True

def update_recipe(name, **kwargs):
    recipes = load_data(DATA_FILE)
    found = False
    for r in recipes:
        if r['name'].lower() == name.lower():
            for key, value in kwargs.items():
                if key in r:
                    r[key] = value
            if 'original_gravity' in kwargs or 'final_gravity' in kwargs:
                r['abv'] = round((r['original_gravity'] - r['final_gravity']) * 131.25, 1)
            found = True
            break
    if found:
        save_data(DATA_FILE, recipes)
        print(f"Updated recipe: {name}")
    else:
        print(f"Recipe '{name}' not found!")
    return found

def delete_recipe(name):
    recipes = load_data(DATA_FILE)
    original_len = len(recipes)
    recipes = [r for r in recipes if r['name'].lower() != name.lower()]
    if len(recipes) < original_len:
        save_data(DATA_FILE, recipes)
        print(f"Deleted recipe: {name}")
        return True
    print(f"Recipe '{name}' not found!")
    return False

def list_recipes(style_filter=None):
    recipes = load_data(DATA_FILE)
    if style_filter:
        recipes = [r for r in recipes if style_filter.lower() in r['style'].lower()]
    if not recipes:
        print("No recipes found.")
        return []
    print(f"\n{'='*60}")
    print(f"{'Name':<25} {'Style':<20} {'ABV':<6} {'Brewed':<8}")
    print(f"{'='*60}")
    for r in recipes:
        print(f"{r['name']:<25} {r['style']:<20} {r['abv']:<6}% {r['brew_count']:<8}")
    print(f"{'='*60}")
    print(f"Total: {len(recipes)} recipes")
    return recipes

def get_recipe(name):
    recipes = load_data(DATA_FILE)
    for r in recipes:
        if r['name'].lower() == name.lower():
            return r
    return None

# fermentation tracking stuff
def log_temperature(recipe_name, temperature, notes=""):
    logs = load_data(TEMP_LOG_FILE)
    entry = {
        'recipe_name': recipe_name,
        'temperature': temperature,
        'timestamp': datetime.now().isoformat(),
        'notes': notes,
        'day': None,  # will be calculated
    }
    # calculate fermentation day
    recipe_logs = [l for l in logs if l['recipe_name'].lower() == recipe_name.lower()]
    if recipe_logs:
        first = datetime.fromisoformat(recipe_logs[0]['timestamp'])
        entry['day'] = (datetime.now() - first).days + 1
    else:
        entry['day'] = 1
    logs.append(entry)
    save_data(TEMP_LOG_FILE, logs)
    print(f"Logged {temperature}°C for {recipe_name} (Day {entry['day']})")
    # check if temp is out of range - hardcoded ranges, should be per-style
    if temperature > 24:
        print("⚠️  WARNING: Temperature above 24°C! Risk of off-flavors.")
    elif temperature < 8:
        print("⚠️  WARNING: Temperature below 8°C! Fermentation may stall.")
    return entry

def get_fermentation_history(recipe_name):
    logs = load_data(TEMP_LOG_FILE)
    recipe_logs = [l for l in logs if l['recipe_name'].lower() == recipe_name.lower()]
    if not recipe_logs:
        print(f"No fermentation data for '{recipe_name}'")
        return []
    print(f"\nFermentation history for: {recipe_name}")
    print(f"{'Day':<6} {'Temp':<8} {'Time':<20} {'Notes'}")
    print("-" * 60)
    for log in recipe_logs:
        print(f"{log['day']:<6} {log['temperature']:<8}°C {log['timestamp'][:16]:<20} {log.get('notes', '')}")
    # stats
    temps = [l['temperature'] for l in recipe_logs]
    print(f"\nStats: min={min(temps)}°C, max={max(temps)}°C, avg={statistics.mean(temps):.1f}°C")
    if len(temps) > 1:
        print(f"       stdev={statistics.stdev(temps):.2f}°C")
    return recipe_logs

def check_fermentation_status(recipe_name):
    logs = load_data(TEMP_LOG_FILE)
    recipe_logs = [l for l in logs if l['recipe_name'].lower() == recipe_name.lower()]
    if not recipe_logs:
        return "no_data"
    last_log = recipe_logs[-1]
    last_time = datetime.fromisoformat(last_log['timestamp'])
    hours_since = (datetime.now() - last_time).total_seconds() / 3600
    if hours_since > 48:
        return "stale"
    recent_temps = [l['temperature'] for l in recipe_logs[-5:]]
    if len(recent_temps) >= 3:
        temp_range = max(recent_temps) - min(recent_temps)
        if temp_range < 0.5:
            return "stable"
    return "active"

# ingredient cost stuff
def calculate_recipe_cost(recipe_name):
    recipe = get_recipe(recipe_name)
    if not recipe:
        print(f"Recipe '{recipe_name}' not found!")
        return None
    # try to load custom prices first
    prices = DEFAULT_PRICES.copy()
    if os.path.exists(INGREDIENTS_FILE):
        custom = load_data(INGREDIENTS_FILE)
        if isinstance(custom, dict):
            prices.update(custom)
    total_cost = 0
    cost_breakdown = []
    for ingredient in recipe.get('ingredients', []):
        name = ingredient.get('name', '').lower().replace(' ', '_')
        amount = ingredient.get('amount_kg', ingredient.get('amount', 0))
        unit_price = prices.get(name, 0)
        if unit_price == 0:
            # try fuzzy match - just check if the ingredient name contains any known key
            for key, price in prices.items():
                if key in name or name in key:
                    unit_price = price
                    break
        cost = amount * unit_price
        total_cost += cost
        cost_breakdown.append({
            'name': ingredient.get('name', name),
            'amount': amount,
            'unit_price': unit_price,
            'cost': round(cost, 2)
        })
    # add fixed costs (estimated)
    water_cost = recipe['batch_size_liters'] * 0.005  # €0.005 per liter
    energy_cost = 2.50  # rough estimate for brewing + fermentation
    total_cost += water_cost + energy_cost
    result = {
        'recipe_name': recipe_name,
        'ingredients_cost': round(sum(c['cost'] for c in cost_breakdown), 2),
        'water_cost': round(water_cost, 2),
        'energy_cost': energy_cost,
        'total_cost': round(total_cost, 2),
        'cost_per_liter': round(total_cost / recipe['batch_size_liters'], 2),
        'breakdown': cost_breakdown,
    }
    return result

def print_cost_report(recipe_name):
    cost = calculate_recipe_cost(recipe_name)
    if not cost:
        return
    print(f"\n{'='*50}")
    print(f"Cost Report: {recipe_name}")
    print(f"{'='*50}")
    print(f"\nIngredients:")
    for item in cost['breakdown']:
        if item['cost'] > 0:
            print(f"  {item['name']:<25} {item['amount']:.3f} x €{item['unit_price']:.2f} = €{item['cost']:.2f}")
        else:
            print(f"  {item['name']:<25} {item['amount']:.3f} (price unknown)")
    print(f"\n  {'Water':<25} €{cost['water_cost']:.2f}")
    print(f"  {'Energy (est.)':<25} €{cost['energy_cost']:.2f}")
    print(f"\n  {'TOTAL':<25} €{cost['total_cost']:.2f}")
    print(f"  {'Per liter':<25} €{cost['cost_per_liter']:.2f}/L")
    print(f"{'='*50}")

def update_ingredient_price(ingredient_name, price_per_kg):
    prices = {}
    if os.path.exists(INGREDIENTS_FILE):
        prices = load_data(INGREDIENTS_FILE)
        if not isinstance(prices, dict):
            prices = {}
    key = ingredient_name.lower().replace(' ', '_')
    prices[key] = price_per_kg
    save_data(INGREDIENTS_FILE, prices)
    print(f"Updated price: {ingredient_name} = €{price_per_kg:.2f}/kg")

# reporting
def monthly_report():
    recipes = load_data(DATA_FILE)
    logs = load_data(TEMP_LOG_FILE)
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0)
    # brews this month
    month_brews = []
    for r in recipes:
        if r.get('last_brewed'):
            brewed = datetime.fromisoformat(r['last_brewed'])
            if brewed >= month_start:
                month_brews.append(r)
    # temp logs this month
    month_logs = []
    for l in logs:
        logged = datetime.fromisoformat(l['timestamp'])
        if logged >= month_start:
            month_logs.append(l)
    print(f"\n{'='*50}")
    print(f"Monthly Report - {now.strftime('%B %Y')}")
    print(f"{'='*50}")
    print(f"\nBrews this month: {len(month_brews)}")
    for b in month_brews:
        print(f"  - {b['name']} ({b['style']})")
    print(f"\nTemperature readings: {len(month_logs)}")
    active_ferments = set(l['recipe_name'] for l in month_logs)
    print(f"Active fermentations: {len(active_ferments)}")
    for name in active_ferments:
        status = check_fermentation_status(name)
        print(f"  - {name}: {status}")
    # total spending estimate
    total_spent = 0
    for b in month_brews:
        cost = calculate_recipe_cost(b['name'])
        if cost:
            total_spent += cost['total_cost']
    print(f"\nEstimated spending: €{total_spent:.2f}")
    print(f"{'='*50}")

def style_summary():
    recipes = load_data(DATA_FILE)
    if not recipes:
        print("No recipes to summarize.")
        return
    styles = {}
    for r in recipes:
        style = r['style']
        if style not in styles:
            styles[style] = []
        styles[style].append(r)
    print(f"\n{'='*50}")
    print("Recipes by Style")
    print(f"{'='*50}")
    for style, recs in sorted(styles.items()):
        avg_abv = statistics.mean([r['abv'] for r in recs])
        total_brews = sum(r['brew_count'] for r in recs)
        print(f"\n{style} ({len(recs)} recipes, {total_brews} total brews, avg {avg_abv:.1f}% ABV)")
        for r in recs:
            stars = f" {'⭐' * r['rating']}" if r.get('rating') else ""
            print(f"  - {r['name']} ({r['abv']}%){stars}")

def search_recipes(query):
    recipes = load_data(DATA_FILE)
    results = []
    query_lower = query.lower()
    for r in recipes:
        if (query_lower in r['name'].lower() or 
            query_lower in r['style'].lower() or
            query_lower in r.get('notes', '').lower() or
            any(query_lower in i.get('name', '').lower() for i in r.get('ingredients', []))):
            results.append(r)
    return results

# CLI stuff - should probably use argparse but whatever
def main():
    if len(sys.argv) < 2:
        print("Usage: brew_tracker.py <command> [args]")
        print("\nCommands:")
        print("  add <name> <style> <batch_size> <og> <fg>  - Add a recipe")
        print("  list [style]                                - List recipes")
        print("  show <name>                                 - Show recipe details")
        print("  delete <name>                               - Delete a recipe")
        print("  log <recipe> <temp>                         - Log fermentation temp")
        print("  history <recipe>                            - Show fermentation history")
        print("  cost <recipe>                               - Show cost breakdown")
        print("  report                                      - Monthly report")
        print("  styles                                      - Style summary")
        print("  search <query>                              - Search recipes")
        print("  price <ingredient> <price>                  - Update ingredient price")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "add":
        if len(sys.argv) < 7:
            print("Usage: add <name> <style> <batch_size> <og> <fg>")
            sys.exit(1)
        # this is hacky but ingredients come from stdin as json
        ingredients = []
        if not sys.stdin.isatty():
            try:
                ingredients = json.load(sys.stdin)
            except:
                pass
        add_recipe(sys.argv[2], sys.argv[3], float(sys.argv[4]), 
                   float(sys.argv[5]), float(sys.argv[6]), ingredients)
    elif command == "list":
        style = sys.argv[2] if len(sys.argv) > 2 else None
        list_recipes(style)
    elif command == "show":
        if len(sys.argv) < 3:
            print("Usage: show <recipe_name>")
            sys.exit(1)
        recipe = get_recipe(sys.argv[2])
        if recipe:
            print(json.dumps(recipe, indent=2))
        else:
            print(f"Recipe '{sys.argv[2]}' not found.")
    elif command == "delete":
        if len(sys.argv) < 3:
            print("Usage: delete <recipe_name>")
            sys.exit(1)
        delete_recipe(sys.argv[2])
    elif command == "log":
        if len(sys.argv) < 4:
            print("Usage: log <recipe_name> <temperature>")
            sys.exit(1)
        notes = sys.argv[4] if len(sys.argv) > 4 else ""
        log_temperature(sys.argv[2], float(sys.argv[3]), notes)
    elif command == "history":
        if len(sys.argv) < 3:
            print("Usage: history <recipe_name>")
            sys.exit(1)
        get_fermentation_history(sys.argv[2])
    elif command == "cost":
        if len(sys.argv) < 3:
            print("Usage: cost <recipe_name>")
            sys.exit(1)
        print_cost_report(sys.argv[2])
    elif command == "report":
        monthly_report()
    elif command == "styles":
        style_summary()
    elif command == "search":
        if len(sys.argv) < 3:
            print("Usage: search <query>")
            sys.exit(1)
        results = search_recipes(sys.argv[2])
        if results:
            print(f"Found {len(results)} results:")
            for r in results:
                print(f"  - {r['name']} ({r['style']}, {r['abv']}% ABV)")
        else:
            print("No matches found.")
    elif command == "price":
        if len(sys.argv) < 4:
            print("Usage: price <ingredient> <price_per_kg>")
            sys.exit(1)
        update_ingredient_price(sys.argv[2], float(sys.argv[3]))
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
