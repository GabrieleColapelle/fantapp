"""Tolerant CSV import for match-day votes and the fixture list, reusing the
same header-normalization approach as csv_import.py."""
import csv
import io

from app.services.csv_utils import find_column, normalize_header, sniff_dialect

MATCHDAY_HEADERS = ["giornata", "matchday", "gg"]
PLAYER_NAME_HEADERS = ["nome", "calciatore", "giocatore", "name"]
VOTE_HEADERS = ["voto", "vote", "fantavoto"]
OPPONENT_HEADERS = ["avversario", "opponent"]
HOME_HEADERS = ["casa", "home", "casatrasferta"]
TEAM_HEADERS = ["squadra", "team", "club"]

HOME_FALSE_VALUES = {"n", "no", "0", "trasferta", "a", "away", "false"}


def _parse_home(raw: str | None) -> bool:
    value = (raw or "").strip().lower()
    if value in HOME_FALSE_VALUES:
        return False
    return True


def parse_match_stats_csv(content: str, player_ids_by_name: dict[str, int]) -> tuple[list[dict], list[str]]:
    delimiter = sniff_dialect(content[:2000])
    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)

    if not reader.fieldnames:
        return [], ["Il file CSV non contiene un'intestazione riconoscibile"]

    normalized_headers = {normalize_header(h): h for h in reader.fieldnames if h}
    matchday_col = find_column(normalized_headers, MATCHDAY_HEADERS)
    name_col = find_column(normalized_headers, PLAYER_NAME_HEADERS)
    vote_col = find_column(normalized_headers, VOTE_HEADERS)
    opponent_col = find_column(normalized_headers, OPPONENT_HEADERS)
    home_col = find_column(normalized_headers, HOME_HEADERS)

    if not matchday_col or not name_col:
        return [], [
            "Colonne 'Giornata' e/o 'Nome' non trovate. Colonne riconosciute: "
            + ", ".join(reader.fieldnames)
        ]

    rows: list[dict] = []
    errors: list[str] = []

    for i, row in enumerate(reader, start=2):
        name = (row.get(name_col) or "").strip()
        matchday_raw = (row.get(matchday_col) or "").strip()
        if not name or not matchday_raw:
            errors.append(f"Riga {i}: nome o giornata mancante, riga saltata")
            continue

        player_id = player_ids_by_name.get(name.lower())
        if player_id is None:
            errors.append(f"Riga {i}: giocatore '{name}' non trovato in lega, riga saltata")
            continue

        try:
            matchday = int(matchday_raw)
        except ValueError:
            errors.append(f"Riga {i}: giornata '{matchday_raw}' non valida, riga saltata")
            continue

        vote_raw = (row.get(vote_col) or "").strip().replace(",", ".") if vote_col else ""
        played = bool(vote_raw)
        vote = None
        if played:
            try:
                vote = float(vote_raw)
            except ValueError:
                played = False

        rows.append(
            {
                "player_id": player_id,
                "matchday": matchday,
                "played": played,
                "vote": vote,
                "opponent": (row.get(opponent_col) or "").strip() if opponent_col else "",
                "home": _parse_home(row.get(home_col) if home_col else None),
            }
        )

    return rows, errors


def parse_fixtures_csv(content: str) -> tuple[list[dict], list[str]]:
    delimiter = sniff_dialect(content[:2000])
    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)

    if not reader.fieldnames:
        return [], ["Il file CSV non contiene un'intestazione riconoscibile"]

    normalized_headers = {normalize_header(h): h for h in reader.fieldnames if h}
    matchday_col = find_column(normalized_headers, MATCHDAY_HEADERS)
    team_col = find_column(normalized_headers, TEAM_HEADERS)
    opponent_col = find_column(normalized_headers, OPPONENT_HEADERS)
    home_col = find_column(normalized_headers, HOME_HEADERS)

    if not matchday_col or not team_col or not opponent_col:
        return [], [
            "Colonne 'Giornata', 'Squadra' e/o 'Avversario' non trovate. Colonne riconosciute: "
            + ", ".join(reader.fieldnames)
        ]

    rows: list[dict] = []
    errors: list[str] = []

    for i, row in enumerate(reader, start=2):
        team = (row.get(team_col) or "").strip()
        opponent = (row.get(opponent_col) or "").strip()
        matchday_raw = (row.get(matchday_col) or "").strip()
        if not team or not opponent or not matchday_raw:
            errors.append(f"Riga {i}: giornata, squadra o avversario mancante, riga saltata")
            continue

        try:
            matchday = int(matchday_raw)
        except ValueError:
            errors.append(f"Riga {i}: giornata '{matchday_raw}' non valida, riga saltata")
            continue

        rows.append(
            {
                "matchday": matchday,
                "team": team,
                "opponent": opponent,
                "home": _parse_home(row.get(home_col) if home_col else None),
            }
        )

    return rows, errors
