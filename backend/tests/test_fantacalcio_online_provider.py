from pathlib import Path

import pytest

from app.services.providers.fantacalcio_online_provider import (
    AveragePriceFetchError,
    _parse_average_prices_html,
    select_price_column,
)

FIXTURE_HTML = (Path(__file__).parent / "fixtures" / "avg_prices_sample.html").read_text()


def test_parse_average_prices_extracts_known_fields():
    players = _parse_average_prices_html(FIXTURE_HTML)
    malen = next(p for p in players if p["surname_key"] == "malen")
    assert malen["team"] == "Roma"
    assert malen["role"] == "A"
    assert malen["avg_8_350"] == 120.18
    assert malen["avg_10_500"] == 142.74


def test_parse_average_prices_handles_multiword_surname_as_one_token():
    players = _parse_average_prices_html(FIXTURE_HTML)
    lautaro = next(p for p in players if p["surname_key"] == "martinez")
    assert lautaro["team"] == "Inter"


def test_parse_average_prices_new_player_has_no_prices():
    players = _parse_average_prices_html(FIXTURE_HTML)
    woltemade = next(p for p in players if p["surname_key"] == "woltemade")
    assert woltemade["avg_8_350"] is None
    assert woltemade["avg_10_500"] is None


def test_parse_average_prices_raises_when_no_rows_found():
    with pytest.raises(AveragePriceFetchError):
        _parse_average_prices_html("<html><body><table><tbody></tbody></table></body></html>")


def test_select_price_column_participants_threshold():
    assert select_price_column(participants=8, budget=350) == "avg_8_350"
    assert select_price_column(participants=9, budget=350) == "avg_10_350"


def test_select_price_column_budget_nearest():
    assert select_price_column(participants=8, budget=300) == "avg_8_350"
    assert select_price_column(participants=8, budget=500) == "avg_8_500"
    assert select_price_column(participants=8, budget=440) == "avg_8_500"
    assert select_price_column(participants=8, budget=420) == "avg_8_350"
