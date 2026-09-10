"""Provider that fetches current injuries for Serie A players, cross
referencing two sources:

- Fantacalcio.it's "infortunati" page: a free-text description per player
  ("lesione del collaterale mediale... recuperabile da inizio ottobre"),
  grouped by team — the primary source, used for the description and a
  best-effort parsed return date.
- SOS Fanta's "indisponibili" page: the same information condensed into
  "in dubbio per la Nª giornata" per player — a cleaner, giornata-based
  signal, used as a cross-check / fallback when Fantacalcio.it's prose
  doesn't parse into a date.

Both descriptions are inherently estimates (real recovery timelines slip
constantly) — kept as free text plus a best-effort parsed date/matchday
rather than pretending to a precision the sources themselves don't have.
"""
import re
from datetime import date, timedelta

import httpx
from bs4 import BeautifulSoup

INJURIES_URL = "https://www.fantacalcio.it/infortunati-serie-a"
RECOVERY_MATCHDAYS_URL = (
    "https://www.sosfanta.com/indisponibili-e-squalificati/"
    "tabella-indisponibili-seriea-fantacalcio-asta-infortunati-tempi-recupero-squalificati-diffidati/"
)
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; fantapp/1.0)"}
REQUEST_TIMEOUT = 15

MONTHS = {
    "gennaio": 1,
    "febbraio": 2,
    "marzo": 3,
    "aprile": 4,
    "maggio": 5,
    "giugno": 6,
    "luglio": 7,
    "agosto": 8,
    "settembre": 9,
    "ottobre": 10,
    "novembre": 11,
    "dicembre": 12,
}

QUALIFIER_DAY = {
    "inizio": 5,
    "prima meta": 10,
    "meta": 15,
    "seconda meta": 20,
    "fine": 25,
}

# "dal/dall'/dalla" + optional qualifier ("seconda metà"/"metà"/"inizio"/"fine") + month name.
# The word boundary after "da"/"dall'"/"dalla" is optional: "dall'inizio" has
# no space before "inizio", while "da inizio" and "dalla fine" do.
_RETURN_DATE_RE = re.compile(
    r"\bda(?:l+[ae'’]?)?\s*(?:la\s+)?"
    r"(seconda\s+met[àa]|prima\s+met[àa]|met[àa]|inizio|fine)?\s*(?:di\s+)?"
    r"(" + "|".join(MONTHS) + r")",
    re.IGNORECASE,
)

# "in dubbio per (la) Nª/Na giornata" — the number just before the "a"/"ª" suffix.
_RECOVERY_MATCHDAY_RE = re.compile(r"([A-ZÀ-Ý][A-Za-zÀ-ÿ'.\- ]{1,40}?) - [^.]*?in dubbio per (?:la )?(\d+)[ªa]\b")


class InjuriesFetchError(Exception):
    """Raised when injuries can't be fetched or parsed. The caller should
    surface a clear error rather than let this crash the request — there's
    no manual fallback for this one, so a failure here should just mean
    the injury flag/estimate is skipped, not that the app breaks."""


def _normalize(text: str) -> str:
    return text.replace("à", "a").replace("è", "e").replace("ì", "i").replace("ò", "o").replace("ù", "u").lower()


def _parse_return_date(description: str, today: date) -> date | None:
    match = _RETURN_DATE_RE.search(description)
    if not match:
        return None

    qualifier_raw, month_name = match.groups()
    qualifier = _normalize(qualifier_raw).strip() if qualifier_raw else None
    day = QUALIFIER_DAY.get(qualifier, 5)
    month = MONTHS[month_name.lower()]
    year = today.year if month >= today.month else today.year + 1

    try:
        return date(year, month, day)
    except ValueError:
        return None


def _parse_injuries_html(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    team_cards = soup.select(".team-card")
    if not team_cards:
        raise InjuriesFetchError(
            "Nessuna squadra trovata nella pagina infortunati: la struttura del sito potrebbe essere cambiata"
        )

    today = date.today()
    rows: list[dict] = []
    for card in team_cards:
        team_el = card.select_one(".team-name")
        if not team_el:
            continue
        team = team_el.get_text(strip=True)

        for item in card.select(".item-name"):
            name = item.get_text(strip=True)
            desc_el = item.find_next_sibling(class_="item-description")
            description = desc_el.get_text(strip=True) if desc_el else ""
            if not name:
                continue

            rows.append(
                {
                    "name": name,
                    "team": team,
                    "description": description,
                    "expected_return_date": _parse_return_date(description, today),
                }
            )

    return rows


def fetch_injuries() -> list[dict]:
    try:
        response = httpx.get(INJURIES_URL, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise InjuriesFetchError(f"Impossibile raggiungere Fantacalcio.it: {exc}") from exc

    return _parse_injuries_html(response.text)


def _parse_recovery_matchdays_html(html: str) -> dict[str, int]:
    match = re.search(r'"articleBody"\s*:\s*"(.*?)",\s*\n', html, re.S)
    if not match:
        raise InjuriesFetchError(
            "Testo indisponibili non trovato: la struttura della pagina SOS Fanta potrebbe essere cambiata"
        )

    blob = match.group(1).encode().decode("unicode_escape").encode("latin1").decode("utf-8", errors="replace")
    return {name.strip(): int(matchday) for name, matchday in _RECOVERY_MATCHDAY_RE.findall(blob)}


SEASON_START = date(2026, 8, 22)
DAYS_PER_MATCHDAY = 7


def estimate_date_from_matchday(matchday: int, today: date) -> date:
    """Turns a "in dubbio per la Nª giornata" signal into an approximate
    calendar date, assuming Serie A's normal weekly cadence from the
    season's start — a rough estimate (international breaks and
    rescheduled matches shift real dates around), used only as a fallback
    when Fantacalcio.it's own prose doesn't parse into a date."""
    matchday_date = SEASON_START + timedelta(days=(matchday - 1) * DAYS_PER_MATCHDAY)
    return max(matchday_date, today)


def fetch_recovery_matchdays() -> dict[str, int]:
    """Player name -> giornata they're expected to be available from
    again, per SOS Fanta. Used as a cross-check/fallback next to
    Fantacalcio.it's parsed date, not the primary signal — name-only
    (no team), so callers should match within the set of already-known
    injured players rather than trusting a name match in isolation."""
    try:
        response = httpx.get(RECOVERY_MATCHDAYS_URL, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise InjuriesFetchError(f"Impossibile raggiungere SOS Fanta: {exc}") from exc

    return _parse_recovery_matchdays_html(response.text)
