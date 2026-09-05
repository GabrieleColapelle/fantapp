from pathlib import Path

import pytest

from app.services.providers.team_strength_provider import TeamStrengthFetchError, _parse_standings_html

FIXTURE_HTML = (Path(__file__).parent / "fixtures" / "wiki_standings_sample.html").read_text()


def test_parse_standings_maps_wikipedia_team_names_to_fantacalcio_names():
    rows = _parse_standings_html(FIXTURE_HTML)
    teams = {r["team"] for r in rows}
    assert "Inter" in teams
    assert "Milan" in teams
    assert "Inter Milan" not in teams
    assert "AC Milan" not in teams


def test_parse_standings_computes_per_game_rates():
    rows = _parse_standings_html(FIXTURE_HTML)
    como = next(r for r in rows if r["team"] == "Como")
    assert como["played"] == 3
    assert como["goals_for_per_game"] == pytest.approx(7 / 3)
    assert como["goals_against_per_game"] == pytest.approx(1.0)


def test_parse_standings_reads_a_leaky_defense_correctly():
    rows = _parse_standings_html(FIXTURE_HTML)
    cagliari = next(r for r in rows if r["team"] == "Cagliari")
    assert cagliari["goals_against_per_game"] == pytest.approx(2.0)


def test_parse_standings_row_with_rowspan_qualification_cell_still_parses():
    # Como's row carries an extra rowspan="4" cell that subsequent rows in
    # the same zone don't repeat — shouldn't throw off the fixed column
    # positions for goals-for/goals-against.
    rows = _parse_standings_html(FIXTURE_HTML)
    assert len(rows) == 5


def test_parse_standings_raises_when_table_not_found():
    with pytest.raises(TeamStrengthFetchError):
        _parse_standings_html("<html><body><table></table></body></html>")
