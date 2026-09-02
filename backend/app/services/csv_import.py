"""Tolerant CSV import for player quotation lists (Fantacalcio.it / Gazzetta
style exports use different headers and either ',' or ';' as separator)."""
import csv
import io

from app.services.csv_utils import find_column, normalize_header, sniff_dialect

ROLE_HEADERS = ["r", "ruolo", "rm"]
NAME_HEADERS = ["nome", "calciatore", "giocatore", "name"]
TEAM_HEADERS = ["squadra", "team", "club"]
QUOTATION_HEADERS = ["qta", "quotazione", "prezzo", "valore", "fvm"]
TIER_HEADERS = ["fascia", "tier", "livello"]

VALID_ROLES = {"P", "D", "C", "A"}


def parse_players_csv(content: str) -> tuple[list[dict], list[str]]:
    delimiter = sniff_dialect(content[:2000])
    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)

    if not reader.fieldnames:
        return [], ["Il file CSV non contiene un'intestazione riconoscibile"]

    normalized_headers = {normalize_header(h): h for h in reader.fieldnames if h}
    name_col = find_column(normalized_headers, NAME_HEADERS)
    role_col = find_column(normalized_headers, ROLE_HEADERS)
    team_col = find_column(normalized_headers, TEAM_HEADERS)
    quotation_col = find_column(normalized_headers, QUOTATION_HEADERS)
    tier_col = find_column(normalized_headers, TIER_HEADERS)

    if not name_col or not role_col:
        return [], [
            "Colonne 'Nome' e/o 'Ruolo' non trovate. Colonne riconosciute: "
            + ", ".join(reader.fieldnames)
        ]

    players: list[dict] = []
    errors: list[str] = []

    for i, row in enumerate(reader, start=2):
        name = (row.get(name_col) or "").strip()
        role = (row.get(role_col) or "").strip().upper()[:1]
        if not name or role not in VALID_ROLES:
            errors.append(f"Riga {i}: nome o ruolo mancante/non valido, riga saltata")
            continue

        quotation_raw = (row.get(quotation_col) or "0").strip().replace(",", ".") if quotation_col else "0"
        try:
            quotation = float(quotation_raw) if quotation_raw else 0.0
        except ValueError:
            quotation = 0.0

        players.append(
            {
                "name": name,
                "role": role,
                "team": (row.get(team_col) or "").strip() if team_col else "",
                "quotation": quotation,
                "tier": (row.get(tier_col) or "").strip() if tier_col else "",
            }
        )

    return players, errors
