from pathlib import Path

import pytest

from app.services.providers.fixtures_provider import FixturesFetchError, _parse_fixtures_html

FIXTURE_HTML = (Path(__file__).parent / "fixtures" / "calendario_sample.html").read_text()


def test_parse_fixtures_filters_by_requested_matchday():
    # The page embeds giornata 3 (already played) alongside giornata 5:
    # only rows for the requested matchday should come back.
    rows = _parse_fixtures_html(FIXTURE_HTML, matchday=5)
    assert all(r["matchday"] == 5 for r in rows)
    teams = {r["team"] for r in rows}
    assert "Genoa" not in teams  # that match is giornata 3


def test_parse_fixtures_produces_one_row_per_team_with_correct_home_away():
    rows = _parse_fixtures_html(FIXTURE_HTML, matchday=5)
    by_team = {r["team"]: r for r in rows}
    assert by_team["Lazio"] == {"matchday": 5, "team": "Lazio", "opponent": "Cagliari", "home": True}
    assert by_team["Cagliari"] == {"matchday": 5, "team": "Cagliari", "opponent": "Lazio", "home": False}


def test_parse_fixtures_covers_all_matches_for_the_matchday():
    rows = _parse_fixtures_html(FIXTURE_HTML, matchday=5)
    assert len(rows) == 4  # 2 matches * 2 teams


def test_parse_fixtures_raises_when_matchday_not_found():
    with pytest.raises(FixturesFetchError):
        _parse_fixtures_html(FIXTURE_HTML, matchday=99)


def test_parse_fixtures_raises_on_empty_page():
    with pytest.raises(FixturesFetchError):
        _parse_fixtures_html("<html><body></body></html>", matchday=1)
