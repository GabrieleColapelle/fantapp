from pathlib import Path

import pytest

from app.services.providers.fantacalcio_provider import ListoneFetchError, _parse_listone_html

FIXTURE_HTML = (Path(__file__).parent / "fixtures" / "listone_sample.html").read_text()


def test_parse_listone_extracts_known_fields():
    players = _parse_listone_html(FIXTURE_HTML)
    names = {p["name"] for p in players}
    assert "Malen" in names
    assert "Martinez L." in names
    assert "Meret" in names


def test_parse_listone_maps_team_abbreviation_to_full_name():
    players = _parse_listone_html(FIXTURE_HTML)
    meret = next(p for p in players if p["name"] == "Meret")
    assert meret["team"] == "Napoli"
    assert meret["role"] == "P"
    assert meret["quotation"] == 12.0


def test_parse_listone_skips_rows_with_unrecognized_role():
    players = _parse_listone_html(FIXTURE_HTML)
    assert not any(p["name"] == "Ruolo Sconosciuto" for p in players)


def test_parse_listone_raises_when_no_rows_found():
    with pytest.raises(ListoneFetchError):
        _parse_listone_html("<html><body><table><tbody></tbody></table></body></html>")
