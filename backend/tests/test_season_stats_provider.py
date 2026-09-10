from pathlib import Path

import pytest

from app.services.providers.season_stats_provider import SeasonStatsFetchError, _parse_season_stats_html

FIXTURE_HTML = (Path(__file__).parent / "fixtures" / "season_stats_sample.html").read_text()


def test_parse_season_stats_extracts_averages():
    rows = _parse_season_stats_html(FIXTURE_HTML, season="2025-26")
    calha = next(r for r in rows if r["name"] == "Calhanoglu")
    assert calha["team"] == "Inter"
    assert calha["role"] == "C"
    assert calha["matches_played"] == 22
    assert calha["avg_vote"] == 6.52
    assert calha["avg_fantavoto"] == 7.64
    assert calha["season"] == "2025-26"


def test_parse_season_stats_skips_players_with_zero_appearances():
    rows = _parse_season_stats_html(FIXTURE_HTML, season="2025-26")
    names = {r["name"] for r in rows}
    assert "Rientrante" not in names


def test_parse_season_stats_covers_all_qualifying_players():
    rows = _parse_season_stats_html(FIXTURE_HTML, season="2025-26")
    assert len(rows) == 2


def test_parse_season_stats_raises_on_empty_page():
    with pytest.raises(SeasonStatsFetchError):
        _parse_season_stats_html("<html><body></body></html>", season="2025-26")
