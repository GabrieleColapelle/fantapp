from pathlib import Path

import pytest

from app.services.providers.probable_lineups_provider import LineupsFetchError, _parse_lineups_html

FIXTURE_HTML = (Path(__file__).parent / "fixtures" / "probable_lineups_sample.html").read_text()


def test_parse_lineups_extracts_starter_with_weighted_average():
    data = _parse_lineups_html(FIXTURE_HTML)
    bijlow = next(r for r in data["starters"] if r["surname_key"] == "bijlow")
    assert bijlow["team"] == "Genoa"
    assert bijlow["role"] == "P"
    assert bijlow["is_starter"] is True
    assert bijlow["probability"] == 91.0


def test_parse_lineups_marks_bench_table_rows_as_not_starter():
    data = _parse_lineups_html(FIXTURE_HTML)
    osmajic = next(r for r in data["starters"] if r["surname_key"] == "osmajic")
    assert osmajic["is_starter"] is False
    assert osmajic["probability"] == 47.0


def test_parse_lineups_missing_source_percentage_is_none():
    # The Sky column ("muta") uses "–" for this fixture — not part of the
    # media/starters output directly, but sanity-check the dash doesn't
    # break parsing of the row it's in.
    data = _parse_lineups_html(FIXTURE_HTML)
    assert any(r["surname_key"] == "vitinha" for r in data["starters"])


def test_parse_lineups_extracts_unavailable_players_with_reason():
    data = _parse_lineups_html(FIXTURE_HTML)
    reasons = {r["surname_key"]: r["reason"] for r in data["unavailable"]}
    assert reasons["nuredini"] == "infortunato"
    assert reasons["traore"] == "infortunato"


def test_parse_lineups_raises_when_no_teams_found():
    with pytest.raises(LineupsFetchError):
        _parse_lineups_html("<html><body></body></html>")
