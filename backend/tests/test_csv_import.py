from app.services.csv_import import parse_players_csv

FANTACALCIO_STYLE = """Id;R;RM;Nome;Squadra;Qt.A;Qt.I
1;P;Por;Meret;Napoli;12;10
2;D;Dc;Buongiorno;Napoli;18;15
"""

GAZZETTA_STYLE = """Ruolo,Nome,Squadra,Quotazione
A,Osimhen,Napoli,35
C,Barella,Inter,22
"""


def test_parse_fantacalcio_style_semicolon_csv():
    players, errors = parse_players_csv(FANTACALCIO_STYLE)
    assert errors == []
    assert len(players) == 2
    assert players[0] == {"name": "Meret", "role": "P", "team": "Napoli", "quotation": 12.0, "tier": ""}


def test_parse_gazzetta_style_comma_csv():
    players, errors = parse_players_csv(GAZZETTA_STYLE)
    assert errors == []
    assert len(players) == 2
    assert players[1]["name"] == "Barella"
    assert players[1]["quotation"] == 22.0


def test_parse_skips_rows_with_invalid_role():
    csv_content = "Nome,Ruolo,Squadra,Quotazione\nMario Rossi,X,Roma,10\n"
    players, errors = parse_players_csv(csv_content)
    assert players == []
    assert len(errors) == 1


def test_parse_missing_required_columns():
    csv_content = "Foo,Bar\n1,2\n"
    players, errors = parse_players_csv(csv_content)
    assert players == []
    assert len(errors) == 1
