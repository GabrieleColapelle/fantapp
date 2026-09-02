from app.services.stats_import import parse_fixtures_csv, parse_match_stats_csv

PLAYER_IDS = {"meret": 1, "osimhen": 2}

MATCH_STATS_CSV = """Giornata,Nome,Voto,Avversario,Casa
1,Meret,6.5,Verona,S
1,Osimhen,7,Verona,S
2,Meret,,Torino,N
"""

FIXTURES_CSV = """Giornata;Squadra;Avversario;Casa
3;Napoli;Milan;S
3;Milan;Napoli;N
"""


def test_parse_match_stats_maps_player_names_to_ids():
    rows, errors = parse_match_stats_csv(MATCH_STATS_CSV, PLAYER_IDS)
    assert errors == []
    assert len(rows) == 3
    assert rows[0] == {
        "player_id": 1,
        "matchday": 1,
        "played": True,
        "vote": 6.5,
        "opponent": "Verona",
        "home": True,
    }


def test_parse_match_stats_empty_vote_means_not_played():
    rows, errors = parse_match_stats_csv(MATCH_STATS_CSV, PLAYER_IDS)
    not_played = next(r for r in rows if r["matchday"] == 2)
    assert not_played["played"] is False
    assert not_played["vote"] is None
    assert not_played["home"] is False


def test_parse_match_stats_unknown_player_is_skipped_with_error():
    csv_content = "Giornata,Nome,Voto\n1,Someone Else,6\n"
    rows, errors = parse_match_stats_csv(csv_content, PLAYER_IDS)
    assert rows == []
    assert len(errors) == 1


def test_parse_fixtures_semicolon_csv():
    rows, errors = parse_fixtures_csv(FIXTURES_CSV)
    assert errors == []
    assert rows == [
        {"matchday": 3, "team": "Napoli", "opponent": "Milan", "home": True},
        {"matchday": 3, "team": "Milan", "opponent": "Napoli", "home": False},
    ]


def test_parse_fixtures_missing_columns():
    rows, errors = parse_fixtures_csv("Foo,Bar\n1,2\n")
    assert rows == []
    assert len(errors) == 1
