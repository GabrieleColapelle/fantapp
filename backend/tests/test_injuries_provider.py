from datetime import date
from pathlib import Path

import pytest

from app.services.providers.injuries_provider import (
    InjuriesFetchError,
    _parse_injuries_html,
    _parse_recovery_matchdays_html,
    _parse_return_date,
    estimate_date_from_matchday,
)

FANTACALCIO_HTML = (Path(__file__).parent / "fixtures" / "injuries_fantacalcio_sample.html").read_text()
SOSFANTA_HTML = (Path(__file__).parent / "fixtures" / "injuries_sosfanta_sample.html").read_text()


def test_parse_injuries_extracts_name_team_and_description():
    rows = _parse_injuries_html(FANTACALCIO_HTML)
    hien = next(r for r in rows if r["name"] == "Hien")
    assert hien["team"] == "Atalanta"
    assert "operato" in hien["description"]


def test_parse_injuries_covers_all_players():
    rows = _parse_injuries_html(FANTACALCIO_HTML)
    names = {r["name"] for r in rows}
    assert names == {"Sulemana K.", "Hien", "Orsolini", "Trepy"}


def test_parse_injuries_leaves_unparseable_description_without_a_date():
    rows = _parse_injuries_html(FANTACALCIO_HTML)
    trepy = next(r for r in rows if r["name"] == "Trepy")
    assert trepy["expected_return_date"] is None


def test_parse_injuries_raises_on_empty_page():
    with pytest.raises(InjuriesFetchError):
        _parse_injuries_html("<html><body></body></html>")


def test_parse_recovery_matchdays_extracts_name_to_matchday():
    result = _parse_recovery_matchdays_html(SOSFANTA_HTML)
    assert result == {"Hien": 6, "Sulemana K.": 6, "Orsolini": 6, "Felici": 29}


@pytest.mark.parametrize(
    "description,expected",
    [
        ("recuperabile da inizio ottobre", date(2026, 10, 5)),
        ("pronto a tornare in campo dall'inizio di ottobre", date(2026, 10, 5)),
        ("recuperabile dalla seconda metà di settembre", date(2026, 9, 20)),
        ("Recuperabile dalla fine di settembre", date(2026, 9, 25)),
        ("ipotizziamo un rientro da marzo", date(2027, 3, 5)),
        ("operato a fine giugno, non ancora chiaro il rientro", None),
        ("tempi di recupero non ancora definiti", None),
    ],
)
def test_parse_return_date(description, expected):
    assert _parse_return_date(description, today=date(2026, 9, 10)) == expected


def test_estimate_date_from_matchday_uses_weekly_cadence():
    # Season starts 2026-08-22 (giornata 1); giornata 6 is 5 weeks later.
    result = estimate_date_from_matchday(6, today=date(2026, 9, 10))
    assert result == date(2026, 9, 26)


def test_estimate_date_from_matchday_never_returns_a_past_date():
    result = estimate_date_from_matchday(1, today=date(2026, 9, 10))
    assert result >= date(2026, 9, 10)
