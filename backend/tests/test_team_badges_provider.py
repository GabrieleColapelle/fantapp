from pathlib import Path

import pytest

from app.services.providers.team_badges_provider import TeamBadgesFetchError, _parse_team_badges_html

FIXTURE_HTML = (Path(__file__).parent / "fixtures" / "team_badges_sample.html").read_text()


def test_parse_team_badges_extracts_name_to_url():
    badges = _parse_team_badges_html(FIXTURE_HTML)
    assert badges == {
        "Atalanta": "https://content.fantacalcio.it/web/img/team/ico/atalanta2026_d.png",
        "Bologna": "https://content.fantacalcio.it/web/img/team/ico/bolognanew_d.png",
    }


def test_parse_team_badges_raises_on_empty_page():
    with pytest.raises(TeamBadgesFetchError):
        _parse_team_badges_html("<html><body></body></html>")
