"""Provider that fetches the set-piece taker hierarchy per Serie A team
(penalties and free kicks) from Fantacalcio.it's public "Rigoristi" page —
same site as the listone, no login needed. A designated first-choice
penalty or free-kick taker is a strong fantacalcio value signal independent
of role/price. Isolated the same way as the other providers: if this
breaks, the rest of the app keeps working without it.
"""
import httpx
from bs4 import BeautifulSoup

SET_PIECE_TAKERS_URL = "https://www.fantacalcio.it/rigoristi-serie-a"
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; fantapp/1.0)"}
REQUEST_TIMEOUT = 10


class PenaltyTakersFetchError(Exception):
    """Raised when the set-piece-takers page can't be fetched or parsed.
    The caller should surface a clear error rather than crash — the rest
    of the app works fine without this enrichment."""


def _find_column(card, header_keyword: str):
    for col in card.select(".row.row-responsive > .col"):
        header = col.find("header")
        if header and header_keyword in header.get_text(strip=True).lower():
            return col
    return None


def _extract_ranked_names(column, team: str) -> list[dict]:
    rows = []
    for rank, li in enumerate(column.select("ol.pill-list li"), start=1):
        name_el = li.select_one(".player-name")
        if not name_el:
            continue
        name = name_el.get_text(strip=True)
        if name:
            rows.append({"team": team, "surname_key": name.lower(), "rank": rank})
    return rows


def _parse_set_piece_takers_html(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    team_cards = soup.select(".team-card")
    if not team_cards:
        raise PenaltyTakersFetchError(
            "Nessuna squadra trovata nella pagina: la struttura del sito potrebbe essere cambiata"
        )

    penalties: list[dict] = []
    free_kicks: list[dict] = []

    for card in team_cards:
        team_el = card.select_one(".team-name")
        if not team_el:
            continue
        team = team_el.get_text(strip=True)

        penalty_col = _find_column(card, "rigori")
        if penalty_col:
            penalties.extend(_extract_ranked_names(penalty_col, team))

        free_kick_col = _find_column(card, "calci piazzati")
        if free_kick_col:
            free_kicks.extend(_extract_ranked_names(free_kick_col, team))

    return {"penalties": penalties, "free_kicks": free_kicks}


def fetch_set_piece_takers() -> dict:
    try:
        response = httpx.get(SET_PIECE_TAKERS_URL, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise PenaltyTakersFetchError(f"Impossibile raggiungere Fantacalcio.it: {exc}") from exc

    return _parse_set_piece_takers_html(response.text)
