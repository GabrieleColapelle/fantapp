from pathlib import Path

import pytest

from app.services.providers.penalty_takers_provider import PenaltyTakersFetchError, _parse_set_piece_takers_html

FIXTURE_HTML = (Path(__file__).parent / "fixtures" / "penalty_takers_sample.html").read_text()


def test_parse_set_piece_takers_extracts_penalties_in_rank_order():
    data = _parse_set_piece_takers_html(FIXTURE_HTML)
    atalanta = [t for t in data["penalties"] if t["team"] == "Atalanta"]
    assert [t["surname_key"] for t in atalanta] == ["scamacca", "krstovic", "samardzic"]
    assert [t["rank"] for t in atalanta] == [1, 2, 3]


def test_parse_set_piece_takers_extracts_free_kicks_separately():
    data = _parse_set_piece_takers_html(FIXTURE_HTML)
    atalanta_fk = [t for t in data["free_kicks"] if t["team"] == "Atalanta"]
    assert [t["surname_key"] for t in atalanta_fk] == ["de ketelaere", "samardzic"]
    # Samardzic is both a backup penalty taker (rank 3) and a free-kick
    # taker (rank 2) — the two lists are independent.
    assert not any(t["surname_key"] == "de ketelaere" for t in data["penalties"])


def test_parse_set_piece_takers_single_taker_team():
    data = _parse_set_piece_takers_html(FIXTURE_HTML)
    bologna = [t for t in data["penalties"] if t["team"] == "Bologna"]
    assert bologna == [{"team": "Bologna", "surname_key": "orsolini", "rank": 1}]


def test_parse_set_piece_takers_raises_when_no_teams_found():
    with pytest.raises(PenaltyTakersFetchError):
        _parse_set_piece_takers_html("<html><body></body></html>")
