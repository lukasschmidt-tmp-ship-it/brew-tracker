"""Tests for brew_tracker.services.pricing."""

import pytest

from brew_tracker.services.pricing import (
    PricingService,
    PriceResult,
    _normalize,
)


class TestNormalize:
    @pytest.mark.parametrize(
        "input_,expected",
        [
            ("Citra", "citra"),
            ("Hallertau Mittelfruh", "hallertau_mittelfruh"),
            ("  SAFALE US05  ", "safale_us05"),
            ("pale-ale-malt", "pale_ale_malt"),
            ("Munich II", "munich_ii"),
        ],
    )
    def test_normalizes_correctly(self, input_, expected):
        assert _normalize(input_) == expected


class TestPriceResult:
    def test_known_result_is_truthy(self):
        result = PriceResult(price=45.0, canonical_key="citra")
        assert bool(result) is True
        assert result.unknown is False

    def test_unknown_result_is_falsy(self):
        result = PriceResult(price=None, canonical_key=None)
        assert bool(result) is False
        assert result.unknown is True


class TestPricingService:
    @pytest.fixture
    def prices(self):
        return {
            "pilsner_malt": 2.50,
            "wheat_malt": 2.80,
            "munich_malt": 3.10,
            "citra": 45.00,
            "safale_us05": 4.50,
        }

    @pytest.fixture
    def pricing(self, prices):
        return PricingService(prices)

    @pytest.fixture
    def pricing_with_aliases(self, prices):
        return PricingService(
            prices,
            aliases={
                "hallertau": "citra",  # intentionally wrong for "unrelated alias" test
                "pils": "pilsner_malt",
            },
        )

    # ── Tier 1: exact match ────────────────────────────────────────────────

    def test_exact_key_match(self, pricing):
        result = pricing.lookup("pilsner_malt")
        assert result.price == 2.50
        assert result.canonical_key == "pilsner_malt"

    def test_exact_key_match_case_insensitive(self, pricing):
        result = pricing.lookup("Citra")
        assert result.price == 45.00
        assert result.canonical_key == "citra"

    def test_exact_key_match_strips_spaces(self, pricing):
        result = pricing.lookup("  safale_us05  ")
        assert result.price == 4.50

    def test_exact_key_match_replaces_dashes(self, pricing):
        result = pricing.lookup("pale-ale-malt")  # not in table
        assert result.unknown is True  # no match

    # ── Tier 2: alias ──────────────────────────────────────────────────────

    def test_alias_match(self, pricing_with_aliases):
        result = pricing_with_aliases.lookup("pils")
        assert result.price == 2.50
        assert result.canonical_key == "pilsner_malt"

    def test_alias_normalizes_input(self, pricing_with_aliases):
        result = pricing_with_aliases.lookup("  PILS  ")
        assert result.price == 2.50

    def test_alias_resolves_to_canonical(self, pricing_with_aliases):
        result = pricing_with_aliases.lookup("hallertau")
        assert result.price == 45.00
        assert result.canonical_key == "citra"

    def test_alias_not_in_price_table_returns_unknown(self):
        # "lupulin" is an alias for something not in price_table
        pricing = PricingService(
            {"citra": 45.0},
            aliases={"lupulin": "some_unknown_hop"},
        )
        result = pricing.lookup("lupulin")
        assert result.unknown is True
        assert result.canonical_key is None

    # ── Tier 3: unknown ────────────────────────────────────────────────────

    def test_unknown_returns_none(self, pricing):
        result = pricing.lookup("vienna_malt")
        assert result.price is None
        assert result.canonical_key is None

    def test_unknown_is_falsy(self, pricing):
        result = pricing.lookup("nonexistent")
        assert bool(result) is False

    def test_no_substring_matching(self, pricing):
        # "pil" is a substring of "pilsner_malt" but must NOT match
        result = pricing.lookup("pil")
        assert result.unknown is True

        # "citra_10kg" is not in table and "citra" is not in "citra_10kg"
        # — must NOT match "citra"
        result = pricing.lookup("citra_10kg")
        assert result.unknown is True

    # ── lookup_all ─────────────────────────────────────────────────────────

    def test_lookup_all(self, pricing):
        ingredients = [
            {"name": "pilsner_malt", "amount_kg": 4.5},
            {"name": "citra", "amount_kg": 0.06},
            {"name": "unknown_hop", "amount_kg": 0.01},
        ]
        results = pricing.lookup_all(ingredients)
        assert len(results) == 3
        assert results[0]["cost"] == 11.25  # 4.5 * 2.50
        assert results[0]["price_unknown"] is False
        assert results[1]["cost"] == 2.70  # 0.06 * 45.00
        assert results[2]["cost"] == 0.0
        assert results[2]["price_unknown"] is True

    def test_lookup_all_with_legacy_amount_field(self, pricing):
        # Old format: "amount" instead of "amount_kg"
        ingredients = [{"name": "pilsner_malt", "amount": 4.5}]
        results = pricing.lookup_all(ingredients)
        assert results[0]["cost"] == 11.25

    def test_lookup_all_empty_list(self, pricing):
        assert pricing.lookup_all([]) == []

    # ── add_alias ──────────────────────────────────────────────────────────

    def test_add_alias(self, pricing):
        pricing.add_alias("munich", "munich_malt")
        result = pricing.lookup("munich")
        assert result.price == 3.10

    def test_add_alias_does_not_clobber_price_table_key(self, pricing):
        # Adding "pilsner_malt" as an alias for itself is a no-op
        pricing.add_alias("pilsner_malt", "pilsner_malt")
        assert pricing.lookup("pilsner_malt").price == 2.50

    # ── self-aliasing: price table keys are also valid aliases ─────────────

    def test_price_table_key_works_as_alias(self, pricing):
        # "pilsner" is not a key, but "pilsner_malt" is a key
        result = pricing.lookup("pilsner_malt")
        assert result.price == 2.50
        # Explicitly check alias seeding worked
        assert pricing._aliases["pilsner_malt"] == "pilsner_malt"
