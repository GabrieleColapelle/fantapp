from pathlib import Path

import pytest

from app.services.providers.match_votes_provider import MatchVotesFetchError, _parse_grade, _parse_votes_html

FIXTURE_HTML = (Path(__file__).parent / "fixtures" / "match_votes_sample.html").read_text()


def test_parse_votes_reads_fantavoto_and_home_team():
    rows = _parse_votes_html(FIXTURE_HTML, matchday=1)
    carnesecchi = next(r for r in rows if r["name"] == "Carnesecchi")
    assert carnesecchi["team"] == "Atalanta"
    assert carnesecchi["opponent"] == "Sassuolo"
    assert carnesecchi["home"] is True
    assert carnesecchi["vote"] == 6.5
    assert carnesecchi["matchday"] == 1


def test_parse_votes_reads_away_team_correctly():
    rows = _parse_votes_html(FIXTURE_HTML, matchday=1)
    idzes = next(r for r in rows if r["name"] == "Idzes")
    assert idzes["team"] == "Sassuolo"
    assert idzes["opponent"] == "Atalanta"
    assert idzes["home"] is False
    assert idzes["vote"] == 4.5


def test_parse_votes_does_not_cap_a_big_game_fantavoto_above_ten():
    rows = _parse_votes_html(FIXTURE_HTML, matchday=1)
    krstovic = next(r for r in rows if r["name"] == "Krstovic")
    assert krstovic["vote"] == 17.5


def test_parse_votes_fixes_missing_decimal_point():
    # Some substitute rows render the default sufficiency vote without the
    # comma ("55" instead of "5,5") — anything above the 10-point max is
    # assumed to be missing its decimal point.
    rows = _parse_votes_html(FIXTURE_HTML, matchday=1)
    scamacca = next(r for r in rows if r["name"] == "Scamacca")
    assert scamacca["vote"] == 5.5


def test_parse_votes_uses_first_pill_not_the_other_sources():
    rows = _parse_votes_html(FIXTURE_HTML, matchday=1)
    ederson = next(r for r in rows if r["name"] == "Ederson D.S.")
    assert ederson["vote"] == 8.5


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("6,5", 6.5),
        ("6", 6.0),
        ("55", 5.5),
        # Fantavoto has no upper bound (goals/assists stack on top of the
        # base vote) — a big game must not be mistaken for the "55" quirk.
        ("17,5", 17.5),
        ("18", 18.0),
        ("11,5", 11.5),
        ("", None),
        (None, None),
        ("n/d", None),
    ],
)
def test_parse_grade(raw, expected):
    assert _parse_grade(raw) == expected


def test_parse_votes_raises_when_no_matches_found():
    with pytest.raises(MatchVotesFetchError):
        _parse_votes_html("<html><body></body></html>", matchday=1)
