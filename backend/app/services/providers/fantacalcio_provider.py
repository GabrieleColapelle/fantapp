"""Provider that fetches the official Fantacalcio.it player quotation list
("listone") from the public quotations page — no login needed. Kept isolated
behind a simple `fetch_listone()` function so it can be swapped for another
source, or dropped, without touching the rest of the app: if this ever
breaks (site redesign, network issues), the CSV/manual import in
players.py still works as a fallback.
"""
import httpx
from bs4 import BeautifulSoup

LISTONE_URL = "https://www.fantacalcio.it/quotazioni-fantacalcio"
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; fantapp/1.0)"}
REQUEST_TIMEOUT = 10

TEAM_ABBREVIATIONS = {
    "ATA": "Atalanta",
    "BOL": "Bologna",
    "CAG": "Cagliari",
    "COM": "Como",
    "CRE": "Cremonese",
    "EMP": "Empoli",
    "FIO": "Fiorentina",
    "FRO": "Frosinone",
    "GEN": "Genoa",
    "INT": "Inter",
    "JUV": "Juventus",
    "LAZ": "Lazio",
    "LEC": "Lecce",
    "MIL": "Milan",
    "MON": "Monza",
    "NAP": "Napoli",
    "PAR": "Parma",
    "PIS": "Pisa",
    "ROM": "Roma",
    "SAL": "Salernitana",
    "SAS": "Sassuolo",
    "SPE": "Spezia",
    "TOR": "Torino",
    "UDI": "Udinese",
    "VEN": "Venezia",
    "VER": "Verona",
}

VALID_ROLES = {"P", "D", "C", "A"}

# Mantra sub-roles that mean "plays in an advanced/attacking position",
# regardless of the coarser Classic role: a player listed as Classic "C"
# (centrocampista) whose Mantra tags include any of these is a known
# "bug del listone" in fantacalcio slang — cheaper to buy as a midfielder
# but with an attacker's scoring upside (trequartista/ala/attaccante).
# https://calciodangolo.com/fantacalcio-bug-listone-2026-2027-wesley-pulisic-occasioni/
ADVANCED_MANTRA_TAGS = {"t", "w", "a", "pc"}


class ListoneFetchError(Exception):
    """Raised when the listone can't be fetched or parsed. The caller
    should surface a clear error and suggest the CSV/manual import as a
    fallback, rather than let this crash the request."""


def _parse_listone_html(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("tr.player-row")
    if not rows:
        raise ListoneFetchError(
            "Nessun giocatore trovato nella pagina: la struttura del sito potrebbe essere cambiata"
        )

    players: list[dict] = []
    for row in rows:
        role = (row.get("data-filter-role-classic") or "").upper()
        # The name link only (".player-name a span"), not the whole
        # ".player-name" cell: that cell also holds a sibling "*" marker
        # (title "Non gioca più in Serie A") for players no longer active,
        # which would otherwise get glued onto the name (e.g. "Leao*").
        name_el = row.select_one(".player-name a span") or row.select_one(".player-name")
        team_el = row.select_one(".player-team")
        price_el = row.select_one(".player-classic-current-price")
        mantra_role = row.get("data-filter-role-mantra") or ""

        if role not in VALID_ROLES or not name_el or not team_el:
            continue

        name = name_el.get_text(strip=True)
        team_abbr = team_el.get_text(strip=True)
        if not name or not team_abbr:
            continue

        price_text = price_el.get_text(strip=True) if price_el else ""
        try:
            quotation = float(price_text.replace(",", "."))
        except ValueError:
            quotation = 0.0

        mantra_tags = set(mantra_role.split("|"))
        is_bug = role == "C" and bool(mantra_tags & ADVANCED_MANTRA_TAGS)

        players.append(
            {
                "name": name,
                "role": role,
                "team": TEAM_ABBREVIATIONS.get(team_abbr, team_abbr),
                "quotation": quotation,
                "mantra_role": mantra_role,
                "is_midfielder_bug": is_bug,
            }
        )

    return players


def fetch_listone() -> list[dict]:
    try:
        response = httpx.get(LISTONE_URL, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ListoneFetchError(f"Impossibile raggiungere Fantacalcio.it: {exc}") from exc

    return _parse_listone_html(response.text)
