"""Provider that fetches upcoming Serie A fixtures ("calendario") from
Fantacalcio.it for a given giornata — opponent and home/away for every
team, replacing the manual CSV import. Same isolation/fallback pattern as
the other providers: if this breaks, the CSV/manual fixture entry still
works.
"""
import httpx
from bs4 import BeautifulSoup

CALENDAR_URL_TEMPLATE = "https://www.fantacalcio.it/serie-a/calendario/{matchday}"
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; fantapp/1.0)"}
REQUEST_TIMEOUT = 10


class FixturesFetchError(Exception):
    """Raised when a giornata's fixtures can't be fetched or parsed. The
    caller should surface a clear error and suggest the CSV/manual entry
    as a fallback, rather than let this crash the request."""


def _parse_fixtures_html(html: str, matchday: int) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    # The calendar page embeds match cards for more than one giornata (the
    # current one plus whichever was requested) — each card carries its
    # own matchweek number, so we filter rather than assume page context.
    matches = soup.select('div[itemtype="http://schema.org/SportsEvent"]')

    rows: list[dict] = []
    for match in matches:
        week_el = match.select_one(".matchweek")
        if not week_el:
            continue
        try:
            week = int(week_el.get_text(strip=True))
        except ValueError:
            continue
        if week != matchday:
            continue

        home_el = match.select_one('label[itemprop="homeTeam"] meta[itemprop="name"]')
        away_el = match.select_one('label[itemprop="awayTeam"] meta[itemprop="name"]')
        if not home_el or not away_el:
            continue
        home_team = (home_el.get("content") or "").strip()
        away_team = (away_el.get("content") or "").strip()
        if not home_team or not away_team:
            continue

        rows.append({"matchday": matchday, "team": home_team, "opponent": away_team, "home": True})
        rows.append({"matchday": matchday, "team": away_team, "opponent": home_team, "home": False})

    if not rows:
        raise FixturesFetchError(
            f"Nessuna partita trovata per la giornata {matchday}: la struttura del sito potrebbe essere "
            "cambiata, oppure questa giornata non è ancora nel calendario"
        )

    return rows


def fetch_fixtures(matchday: int) -> list[dict]:
    url = CALENDAR_URL_TEMPLATE.format(matchday=matchday)
    try:
        response = httpx.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise FixturesFetchError(f"Impossibile raggiungere Fantacalcio.it: {exc}") from exc

    return _parse_fixtures_html(response.text, matchday)
