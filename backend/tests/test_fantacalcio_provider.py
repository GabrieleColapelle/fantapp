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


def test_parse_listone_strips_out_of_game_marker_from_name():
    # Malen's row has a sibling "*" marker (title "Non gioca più in Serie
    # A") that must not get glued onto the name.
    players = _parse_listone_html(FIXTURE_HTML)
    malen = next(p for p in players if p["name"] == "Malen")
    assert "*" not in malen["name"]


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


def test_parse_listone_flags_midfielder_with_advanced_mantra_role_as_bug():
    # Baldanzi: Classic "C" but Mantra "c|t" (also trequartista-eligible).
    players = _parse_listone_html(FIXTURE_HTML)
    baldanzi = next(p for p in players if p["name"] == "Baldanzi")
    assert baldanzi["mantra_role"] == "c|t"
    assert baldanzi["is_midfielder_bug"] is True


def test_parse_listone_does_not_flag_plain_midfielder():
    # Frendrup: Classic "C", Mantra "m|c" — no advanced tag, not a bug.
    players = _parse_listone_html(FIXTURE_HTML)
    frendrup = next(p for p in players if p["name"] == "Frendrup")
    assert frendrup["is_midfielder_bug"] is False


def test_parse_listone_does_not_flag_non_midfielders():
    # Malen is Classic "A" (attacker) with an advanced Mantra tag too, but
    # the bug label only applies to players *listed* as midfielders.
    players = _parse_listone_html(FIXTURE_HTML)
    malen = next(p for p in players if p["name"] == "Malen")
    assert malen["is_midfielder_bug"] is False
