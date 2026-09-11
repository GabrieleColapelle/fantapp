"""Provider that fetches Fantacalcio.it's season-preview "probabili
formazioni" article: one infographic image plus structured text (coach,
modulo, probable XI, ballottaggi, rigoristi, calci piazzati) per team.

Unlike the other providers here, this isn't an evergreen URL — it's a
single seasonal article Fantacalcio.it publishes once before the season
starts and updates as transfers finalize, so the URL needs updating by
hand each season (there's no formula to derive it from a season string).
"""
import httpx
from bs4 import BeautifulSoup

ARTICLE_URL = (
    "https://www.fantacalcio.it/news/calcio-italia/06_08_2026/"
    "asta-fantacalcio-le-probabili-formazioni-della-serie-a-enilive-2026-27-495558"
)
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; fantapp/1.0)"}
REQUEST_TIMEOUT = 15

FIELD_LABELS = {
    "Allenatore": "coach",
    "Modulo": "formation_module",
    "Probabile formazione": "starting_eleven",
    "Ballottaggi": "ballottaggi",
    "Rigoristi": "penalty_takers",
    "Calci da fermo": "free_kick_takers",
}


class TeamFormationsFetchError(Exception):
    """Raised when the article can't be fetched or parsed. The caller
    should surface a clear error rather than let this crash the request —
    there's no manual fallback for this one, so a failure here should
    just mean the formations tab stays empty, not that the app breaks."""


def _parse_team_formations_html(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    asides = soup.select("aside.text-type-aside")
    if not asides:
        raise TeamFormationsFetchError(
            "Nessuna squadra trovata nell'articolo: la struttura della pagina potrebbe essere cambiata"
        )

    teams: list[dict] = []
    for aside in asides:
        heading = aside.find("h2")
        if not heading:
            continue
        team = heading.get_text(strip=True).title()

        data: dict = {field: "" for field in FIELD_LABELS.values()}
        for p in aside.find_all("p"):
            strong = p.find("strong")
            if not strong:
                continue
            label = strong.get_text(strip=True)
            field = FIELD_LABELS.get(label)
            if not field:
                continue
            value = p.get_text(strip=True)[len(label):].lstrip(":").strip()
            data[field] = value

        image_url = None
        section = aside.find_parent("section")
        sibling = section.find_next_sibling("section") if section else None
        while sibling:
            if sibling.select_one("aside.text-type-aside"):
                break
            img = sibling.select_one(".article-image img")
            if img:
                image_url = img.get("src")
                break
            sibling = sibling.find_next_sibling("section")

        teams.append({"team": team, "image_url": image_url, **data})

    return teams


def fetch_team_formations() -> list[dict]:
    try:
        response = httpx.get(ARTICLE_URL, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise TeamFormationsFetchError(f"Impossibile raggiungere Fantacalcio.it: {exc}") from exc

    return _parse_team_formations_html(response.text)
