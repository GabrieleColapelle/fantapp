"""Provider that fetches live Serie A standings (goals for/against per
team) from Wikipedia. Fantacalcio.it's own classifica is loaded via
client-side JS and isn't in the page source, so this fills that specific
gap — Wikipedia keeps a plain server-rendered league table that's updated
promptly after each giornata.

Used to weight fixtures: a weak-scoring opponent is good news for a
defender/goalkeeper, a leaky one is good news for a midfielder/attacker.
Early in the season these rates are based on very few games and should be
shown to the user as provisional — see `played` on each row.
"""
from datetime import date

import httpx
from bs4 import BeautifulSoup

STANDINGS_URL_TEMPLATE = "https://en.wikipedia.org/wiki/{season}_Serie_A"
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; fantapp/1.0)"}
REQUEST_TIMEOUT = 10

# Wikipedia spells a few clubs differently than Fantacalcio.it.
TEAM_NAME_MAP = {
    "Inter Milan": "Inter",
    "AC Milan": "Milan",
    "Hellas Verona": "Verona",
}


def _current_season() -> str:
    """Serie A season string as used in the Wikipedia article title
    (e.g. "2026–27", with an en dash). The season runs July through June,
    so before July we're still in the season that started the previous
    calendar year."""
    today = date.today()
    start_year = today.year if today.month >= 7 else today.year - 1
    return f"{start_year}–{str(start_year + 1)[2:]}"


class TeamStrengthFetchError(Exception):
    """Raised when the standings can't be fetched or parsed. The caller
    should surface a clear error rather than let this crash the request —
    there's no manual fallback for this one, so a failure here should just
    mean the opponent-strength factor is skipped, not that scoring breaks."""


def _parse_standings_html(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    goals_for_header = soup.select_one('abbr[title="Goals for"]')
    table = goals_for_header.find_parent("table") if goals_for_header else None
    if not table:
        raise TeamStrengthFetchError(
            "Tabella classifica non trovata: la struttura della pagina Wikipedia potrebbe essere cambiata"
        )

    rows: list[dict] = []
    for tr in table.select("tbody tr"):
        team_el = tr.select_one('th[scope="row"] a')
        cells = tr.find_all("td")
        # Row layout: position, played, won, drawn, lost, goals-for,
        # goals-against, goal-diff, points[, qualification note].
        if not team_el or len(cells) < 9:
            continue

        team = team_el.get_text(strip=True)
        team = TEAM_NAME_MAP.get(team, team)

        try:
            played = int(cells[1].get_text(strip=True))
            goals_for = int(cells[5].get_text(strip=True))
            goals_against = int(cells[6].get_text(strip=True))
        except ValueError:
            continue
        if played <= 0:
            continue

        rows.append(
            {
                "team": team,
                "played": played,
                "goals_for_per_game": goals_for / played,
                "goals_against_per_game": goals_against / played,
            }
        )

    if not rows:
        raise TeamStrengthFetchError(
            "Nessuna squadra trovata nella tabella classifica: la struttura della pagina potrebbe essere cambiata"
        )

    return rows


def fetch_team_strength() -> list[dict]:
    url = STANDINGS_URL_TEMPLATE.format(season=_current_season())
    try:
        response = httpx.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise TeamStrengthFetchError(f"Impossibile raggiungere Wikipedia: {exc}") from exc

    return _parse_standings_html(response.text)
