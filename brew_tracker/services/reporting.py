"""Reporting service — monthly stats, style summaries, and search."""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import datetime

from brew_tracker.models.recipe import Recipe


@dataclass(frozen=True)
class MonthlyBrew:
    name: str
    style: str


@dataclass(frozen=True)
class StyleStats:
    style: str
    recipe_count: int
    total_brews: int
    avg_abv: float
    recipes: tuple[str, ...]


@dataclass(frozen=True)
class MonthlyReport:
    month: str
    brew_count: int
    brews: tuple[MonthlyBrew, ...]
    temp_reading_count: int
    active_fermentations: int
    estimated_cost: float


@dataclass(frozen=True)
class StyleReport:
    summaries: tuple[StyleStats, ...]
    total_recipes: int


def build_monthly_report(
    recipes: list[Recipe],
    fermentation_logs: list[dict],
    now: datetime | None = None,
    calculate_cost_fn=None,  # injectable: fn(recipe_name) -> RecipeCost | None
) -> MonthlyReport:
    """
    Build monthly report from raw recipe list and fermentation log dicts.

    Args:
        recipes: List of Recipe objects.
        fermentation_logs: List of fermentation log dicts (from JSON).
        now: Defaults to datetime.now().
        calculate_cost_fn: Optional function that takes a recipe name and
            returns a RecipeCost. If not provided, estimated_cost will be 0.
    """
    if now is None:
        now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    month_brews: list[MonthlyBrew] = []
    for r in recipes:
        if r.last_brewed and r.last_brewed >= month_start:
            month_brews.append(MonthlyBrew(name=r.name, style=r.style))

    month_logs = [
        log
        for log in fermentation_logs
        if datetime.fromisoformat(log["timestamp"]) >= month_start
    ]
    active_ferments: set[str] = set(log["recipe_name"] for log in month_logs)

    estimated_cost = 0.0
    if calculate_cost_fn is not None:
        for brew in month_brews:
            cost = calculate_cost_fn(brew.name)
            if cost is not None:
                estimated_cost += cost.total_cost

    return MonthlyReport(
        month=now.strftime("%B %Y"),
        brew_count=len(month_brews),
        brews=tuple(month_brews),
        temp_reading_count=len(month_logs),
        active_fermentations=len(active_ferments),
        estimated_cost=round(estimated_cost, 2),
    )


def build_style_report(recipes: list[Recipe]) -> StyleReport:
    """
    Group recipes by style with ABV stats and brew counts.
    """
    by_style: dict[str, list[Recipe]] = {}
    for r in recipes:
        by_style.setdefault(r.style, []).append(r)

    summaries: list[StyleStats] = []
    for style, recs in sorted(by_style.items()):
        avg_abv = round(statistics.mean(r.abv for r in recs), 1)
        total_brews = sum(r.brew_count for r in recs)
        summaries.append(
            StyleStats(
                style=style,
                recipe_count=len(recs),
                total_brews=total_brews,
                avg_abv=avg_abv,
                recipes=tuple(r.name for r in recs),
            )
        )

    return StyleReport(summaries=tuple(summaries), total_recipes=len(recipes))


def format_monthly_report(report: MonthlyReport) -> str:
    lines = [
        f"{'=' * 50}",
        f"Monthly Report — {report.month}",
        f"{'=' * 50}",
        "",
        f"Brews this month: {report.brew_count}",
    ]
    for b in report.brews:
        lines.append(f"  - {b.name} ({b.style})")

    lines.extend(
        [
            "",
            f"Temperature readings: {report.temp_reading_count}",
            f"Active fermentations: {report.active_fermentations}",
            "",
            f"Estimated spending: €{report.estimated_cost:.2f}",
            f"{'=' * 50}",
        ]
    )
    return "\n".join(lines)


def format_style_report(report: StyleReport) -> str:
    lines = [
        f"{'=' * 50}",
        "Recipes by Style",
        f"{'=' * 50}",
    ]
    for s in report.summaries:
        lines.append("")
        lines.append(
            f"{s.style} "
            f"({s.recipe_count} recipes, {s.total_brews} total brews, "
            f"avg {s.avg_abv}% ABV)"
        )
        for name in s.recipes:
            lines.append(f"  - {name}")
    return "\n".join(lines)
