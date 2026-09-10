"""Provider that fetches a player's full-season statistics (average voto,
average fantavoto, appearances) from a past, completed Serie A season —
Fantacalcio.it's own "statistiche" page, one request for the whole league
(600+ players), reusing the same team-abbreviation map as the listone.

Used as an auction/lineup signal distinct from the current-season data
already tracked elsewhere: "how did this player actually perform last
year" is a different question from "what's the market paying for him now"
(quotation) or "how has he done in the first few giornate" (match-stats).
"""
import httpx
from bs4 import BeautifulSoup

from app.services.providers.fantacalcio_provider import TEAM_ABBREVIATIONS, VALID_ROLES

STATS_URL_TEMPLATE = "https://www.fantacalcio.it/statistiche-serie-a/{season}"
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; fantapp/1.0)"}
REQUEST_TIMEOUT = 15


class SeasonStatsFetchError(Exception):
    """Raised when a season's statistics can't be fetched or parsed. The
    caller should surface a clear error rather than let this crash the
    request — there's no manual fallback for this one, so a failure here
    should just mean the past-season signal is skipped, not that the rest
    of the app breaks."""


def _parse_number(raw: str | None) -> float | None:
    raw = (raw or "").strip().replace(",", ".")
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _parse_season_stats_html(html: str, season: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("tr.player-row")
    if not rows:
        raise SeasonStatsFetchError(
            f"Nessun giocatore trovato per la stagione {season}: la struttura del sito potrebbe essere cambiata"
        )

    players: list[dict] = []
    for row in rows:
        role = (row.get("data-filter-role-classic") or "").upper()
        name_el = row.select_one(".player-name a span") or row.select_one(".player-name")
        team_el = row.select_one('[data-col-key="sq"]')
        if role not in VALID_ROLES or not name_el or not team_el:
            continue

        name = name_el.get_text(strip=True)
        team_abbr = team_el.get_text(strip=True)
        if not name or not team_abbr:
            continue

        played = _parse_number(row.select_one('[data-col-key="pg"]').get_text(strip=True) if row.select_one('[data-col-key="pg"]') else None)
        avg_vote = _parse_number(row.select_one('[data-col-key="mv"]').get_text(strip=True) if row.select_one('[data-col-key="mv"]') else None)
        avg_fantavoto = _parse_number(row.select_one('[data-col-key="mfv"]').get_text(strip=True) if row.select_one('[data-col-key="mfv"]') else None)

        if played is None or played <= 0:
            continue

        players.append(
            {
                "name": name,
                "role": role,
                "team": TEAM_ABBREVIATIONS.get(team_abbr, team_abbr),
                "season": season,
                "matches_played": int(played),
                "avg_vote": avg_vote,
                "avg_fantavoto": avg_fantavoto,
            }
        )

    return players


def fetch_season_stats(season: str) -> list[dict]:
    """`season` in "YYYY-YY" form (e.g. "2025-26")."""
    url = STATS_URL_TEMPLATE.format(season=season)
    try:
        response = httpx.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise SeasonStatsFetchError(f"Impossibile raggiungere Fantacalcio.it: {exc}") from exc

    return _parse_season_stats_html(response.text, season)
