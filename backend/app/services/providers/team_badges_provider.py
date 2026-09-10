"""Provider that fetches each Serie A team's crest image URL from
Fantacalcio.it. Reuses the "infortunati" page purely as a convenient
source that always lists all 20 teams (with or without injuries) in one
request — nothing here is actually about injuries.
"""
import httpx
from bs4 import BeautifulSoup

TEAM_BADGES_URL = "https://www.fantacalcio.it/infortunati-serie-a"
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; fantapp/1.0)"}
REQUEST_TIMEOUT = 15


class TeamBadgesFetchError(Exception):
    """Raised when team badges can't be fetched or parsed. The caller
    should surface a clear error rather than let this crash the request —
    there's no manual fallback for this one, so a failure here should
    just mean crests don't show, not that the app breaks."""


def _parse_team_badges_html(html: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    team_cards = soup.select(".team-card")
    if not team_cards:
        raise TeamBadgesFetchError(
            "Nessuna squadra trovata nella pagina: la struttura del sito potrebbe essere cambiata"
        )

    badges: dict[str, str] = {}
    for card in team_cards:
        name_el = card.select_one(".team-info .team-name")
        img_el = card.select_one(".team-info img.team-badge")
        if not name_el or not img_el:
            continue
        team = name_el.get_text(strip=True)
        src = img_el.get("src", "").strip()
        if team and src:
            badges[team] = src

    return badges


def fetch_team_badges() -> dict[str, str]:
    try:
        response = httpx.get(TEAM_BADGES_URL, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise TeamBadgesFetchError(f"Impossibile raggiungere Fantacalcio.it: {exc}") from exc

    return _parse_team_badges_html(response.text)
