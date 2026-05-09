"""Fermentation tracking service."""

from __future__ import annotations

import statistics
from datetime import datetime
from typing import TYPE_CHECKING

from brew_tracker.models.types import (
    STALE_HOURS,
    STABILITY_WINDOW,
    STABILITY_THRESHOLD_CELSIUS,
)

if TYPE_CHECKING:
    from brew_tracker.models.recipe import FermentationLog, FermentationStatus


def compute_fermentation_day(
    first_log_timestamp: datetime, at: datetime | None = None
) -> int:
    """
    Compute which fermentation day a given timestamp falls on.

    Args:
        first_log_timestamp: When the first log entry was recorded.
        at: Timestamp to evaluate. Defaults to now.

    Returns:
        Day number (1-based).
    """
    if at is None:
        at = datetime.now()
    return (at - first_log_timestamp).days + 1


def check_status(logs: list[FermentationLog]) -> FermentationStatus:
    """
    Determine fermentation status from a list of logs.

    Status order: NO_DATA → STALE → STABLE → ACTIVE
    """
    from brew_tracker.models.recipe import FermentationStatus

    if not logs:
        return FermentationStatus.NO_DATA

    last = logs[-1]
    hours_since = (datetime.now() - last.timestamp).total_seconds() / 3600
    if hours_since > STALE_HOURS:
        return FermentationStatus.STALE

    recent = [log.temperature for log in logs[-STABILITY_WINDOW:]]
    if len(recent) >= 3 and (max(recent) - min(recent)) <= STABILITY_THRESHOLD_CELSIUS:
        return FermentationStatus.STABLE

    return FermentationStatus.ACTIVE


def temp_warnings(log: FermentationLog) -> list[str]:
    """Return any out-of-range warnings for a fermentation log."""
    return log.warnings


def fermentation_summary(logs: list[FermentationLog]) -> dict:
    """
    Compute min / max / mean / stdev for a list of fermentation logs.

    Returns:
        Dict with keys: min, max, mean, stdev, count.
    """
    if not logs:
        return {"min": None, "max": None, "mean": None, "stdev": None, "count": 0}

    temps = [log.temperature for log in logs]
    result: dict = {
        "min": min(temps),
        "max": max(temps),
        "mean": round(statistics.mean(temps), 1),
        "count": len(temps),
    }
    if len(temps) > 1:
        result["stdev"] = round(statistics.stdev(temps), 2)
    return result
