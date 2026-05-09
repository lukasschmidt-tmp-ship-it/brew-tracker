"""Tests for brew_tracker.data.repository."""

import json
from datetime import datetime, timedelta

import pytest

from brew_tracker.data.repository import RecipeRepository, _normalize_ingredient_key
from brew_tracker.models.recipe import FermentationStatus


@pytest.fixture
def repo(tmp_path):
    return RecipeRepository(
        recipes_path=tmp_path / "recipes.json",
        logs_path=tmp_path / "fermentation_log.json",
        prices_path=tmp_path / "ingredients.json",
    )


class TestNormalizeIngredientKey:
    @pytest.mark.parametrize(
        "input_,expected",
        [
            ("Citra", "citra"),
            ("Hallertau Mittelfruh", "hallertau_mittelfruh"),
            ("  SAFALE US05  ", "safale_us05"),
        ],
    )
    def test_normalizes_correctly(self, input_, expected):
        assert _normalize_ingredient_key(input_) == expected


class TestRecipeRepository:
    # ── recipe CRUD ──────────────────────────────────────────────────────────

    def testall_recipes_returns_empty_when_no_file(self, repo):
        assert repo.all_recipes() == []

    def testsave_and_all_recipes_roundtrip(self, repo, pale_ale_recipe):
        saved = repo.save(pale_ale_recipe)
        assert saved.id == 1

        recipes = repo.all_recipes()
        assert len(recipes) == 1
        assert recipes[0].name == "Centennial Blonde"

    def testsave_assigns_next_id(self, repo, pale_ale_recipe, ipa_recipe):
        repo.save(pale_ale_recipe)
        saved_ipa = repo.save(ipa_recipe)
        assert saved_ipa.id == 2

    def testsave_raises_when_duplicate_name(self, repo, pale_ale_recipe):
        repo.save(pale_ale_recipe)
        pale_ale_recipe.id = None  # reset so upsert path triggers
        with pytest.raises(ValueError, match="already exists"):
            repo.save(pale_ale_recipe)

    def testby_name_returns_recipe(self, repo, pale_ale_recipe):
        repo.save(pale_ale_recipe)
        found = repo.by_name("centennial blonde")
        assert found is not None
        assert found.style == "Blonde Ale"

    def testby_name_case_insensitive(self, repo, pale_ale_recipe):
        repo.save(pale_ale_recipe)
        assert repo.by_name("CENTENNIAL BLONDE") is not None

    def testby_name_returns_none_when_not_found(self, repo):
        assert repo.by_name("does not exist") is None

    def testupsert_creates_new_recipe(self, repo, ipa_recipe):
        recipe, created = repo.upsert(ipa_recipe)
        assert created is True
        assert recipe.id == 1

    def testupsert_updates_existing_recipe(self, repo, ipa_recipe):
        repo.save(ipa_recipe)
        ipa_recipe.batch_size_liters = 30.0
        _, created = repo.upsert(ipa_recipe)
        assert created is False
        assert repo.by_name("Headspace IPA").batch_size_liters == 30.0

    def testdelete_removes_recipe(self, repo, pale_ale_recipe):
        repo.save(pale_ale_recipe)
        assert repo.delete("Centennial Blonde") is True
        assert repo.by_name("Centennial Blonde") is None

    def testdelete_returns_false_when_not_found(self, repo):
        assert repo.delete("nonexistent") is False

    def testfilter_by_style(self, repo, pale_ale_recipe, ipa_recipe):
        repo.save(pale_ale_recipe)
        repo.save(ipa_recipe)
        results = repo.filter_by_style("IPA")
        assert len(results) == 1
        assert results[0].name == "Headspace IPA"

    def testsearch_finds_in_name(self, repo, pale_ale_recipe, ipa_recipe):
        repo.save(pale_ale_recipe)
        repo.save(ipa_recipe)
        results = repo.search("headspace")
        assert len(results) == 1

    def testsearch_finds_in_notes(self, repo, ipa_recipe):
        repo.save(ipa_recipe)
        results = repo.search("dry-hopped")
        assert len(results) == 1

    def testsearch_finds_in_ingredients(self, repo, ipa_recipe):
        repo.save(ipa_recipe)
        results = repo.search("citra")
        assert len(results) == 1

    def testsearch_is_case_insensitive(self, repo, ipa_recipe):
        repo.save(ipa_recipe)
        results = repo.search("HEADSPACE")
        assert len(results) == 1

    # ── fermentation logs ───────────────────────────────────────────────────

    def testlog_temperature_creates_day1(self, repo, pale_ale_recipe):
        repo.save(pale_ale_recipe)
        log = repo.log_temperature("Centennial Blonde", 20.0)
        assert log.day == 1
        assert log.recipe_name == "Centennial Blonde"

    def testlog_temperature_increments_day(self, repo, pale_ale_recipe):
        repo.save(pale_ale_recipe)
        repo.log_temperature("Centennial Blonde", 20.0)
        repo.log_temperature("Centennial Blonde", 20.5)
        logs = repo.fermentation_logs("Centennial Blonde")
        assert logs[0].day == 1
        assert logs[1].day == 2

    def testfermentation_logs_returns_chronological(self, repo, pale_ale_recipe):
        repo.save(pale_ale_recipe)
        repo.log_temperature("Centennial Blonde", 18.0)
        repo.log_temperature("Centennial Blonde", 20.0)
        repo.log_temperature("Centennial Blonde", 21.0)
        logs = repo.fermentation_logs("Centennial Blonde")
        assert [log.day for log in logs] == [1, 2, 3]
        assert [log.temperature for log in logs] == [18.0, 20.0, 21.0]

    def testfermentation_logs_returns_empty_when_none(self, repo):
        assert repo.fermentation_logs("nonexistent") == []

    def testfermentation_status_no_data(self, repo):
        assert repo.fermentation_status("ghost batch") == FermentationStatus.NO_DATA

    def testfermentation_status_stale(self, repo, pale_ale_recipe, tmp_path):
        repo.save(pale_ale_recipe)
        stale_timestamp = (datetime.now() - timedelta(hours=60)).isoformat()
        log_entry = {
            "recipe_name": "Centennial Blonde",
            "temperature": 18.0,
            "timestamp": stale_timestamp,
            "day": 4,
            "notes": "",
        }
        logs_file = tmp_path / "fermentation_log.json"
        json.dump([log_entry], open(logs_file, "w"))
        assert repo.fermentation_status("Centennial Blonde") == FermentationStatus.STALE

    def testfermentation_status_stable(self, repo, pale_ale_recipe):
        repo.save(pale_ale_recipe)
        for temp in [20.0, 20.2, 20.4, 20.3, 20.5]:
            repo.log_temperature("Centennial Blonde", temp)
        assert (
            repo.fermentation_status("Centennial Blonde") == FermentationStatus.STABLE
        )

    def testfermentation_status_active(self, repo, pale_ale_recipe):
        repo.save(pale_ale_recipe)
        repo.log_temperature("Centennial Blonde", 18.0)
        repo.log_temperature("Centennial Blonde", 21.5)
        repo.log_temperature("Centennial Blonde", 20.0)
        # temp range > 0.5 in recent window → active
        assert (
            repo.fermentation_status("Centennial Blonde") == FermentationStatus.ACTIVE
        )

    # ── prices ───────────────────────────────────────────────────────────────

    def testprices_returns_defaults(self, repo):
        prices = repo.prices()
        assert prices["pilsner_malt"] == 2.50
        assert prices["citra"] == 45.00

    def testset_price_and_prices(self, repo):
        repo.set_price("citra", 42.00)
        prices = repo.prices()
        assert prices["citra"] == 42.00

    def testset_price_normalizes_key(self, repo):
        repo.set_price("Citra Hops", 40.00)
        prices = repo.prices()
        assert prices["citra_hops"] == 40.00
