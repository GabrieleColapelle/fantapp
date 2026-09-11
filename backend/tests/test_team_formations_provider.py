from pathlib import Path

import pytest

from app.services.providers.team_formations_provider import (
    TeamFormationsFetchError,
    _parse_team_formations_html,
)

FIXTURE_HTML = (Path(__file__).parent / "fixtures" / "team_formations_sample.html").read_text()


def test_parse_team_formations_covers_all_teams():
    teams = _parse_team_formations_html(FIXTURE_HTML)
    assert [t["team"] for t in teams] == ["Atalanta", "Bologna"]


def test_parse_team_formations_extracts_all_fields():
    teams = _parse_team_formations_html(FIXTURE_HTML)
    atalanta = teams[0]
    assert atalanta["coach"] == "Maurizio Sarri (nuovo)"
    assert atalanta["formation_module"] == "4-3-3"
    assert "Carnesecchi" in atalanta["starting_eleven"]
    assert "Kristensen/Hien" in atalanta["ballottaggi"]
    assert atalanta["penalty_takers"] == "Scamacca, Krstovic, Samardzic"
    assert atalanta["free_kick_takers"] == "De Ketelaere, Samardzic, Gaetano"


def test_parse_team_formations_extracts_the_lineup_image_between_sections():
    teams = _parse_team_formations_html(FIXTURE_HTML)
    assert teams[0]["image_url"] == "https://content.fantacalcio.it/web/img/medium/f336cb78-1c14-431b-bb39-d91e29f099c3.jpg"
    assert teams[1]["image_url"] == "https://content.fantacalcio.it/web/img/medium/a30a716a-0402-432b-b52c-de1d2ca5f4e0.jpg"


def test_parse_team_formations_raises_on_empty_page():
    with pytest.raises(TeamFormationsFetchError):
        _parse_team_formations_html("<html><body></body></html>")
