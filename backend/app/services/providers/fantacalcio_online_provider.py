"""Provider that fetches real average auction prices from Fantacalcio-Online
("quanto è stato pagato davvero"), a public page that aggregates actual
purchases across leagues on that site — independent of, and complementary
to, the official listone quotation from fantacalcio_provider.py. No login
needed. Isolated the same way: if this breaks, the rest of the app (listone
import, manual entry) still works.
"""
import httpx
from bs4 import BeautifulSoup

PRICES_URL = "https://www.fantacalcio-online.com/it/asta-fantacalcio-stima-prezzi"
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; fantapp/1.0)"}
REQUEST_TIMEOUT = 10

VALID_ROLES = {"P", "D", "C", "A"}

# Column order in the table, after role/team/name.
PRICE_COLUMNS = ["avg_8_350", "avg_10_350", "avg_8_500", "avg_10_500"]


class AveragePriceFetchError(Exception):
    """Raised when the average-price table can't be fetched or parsed. The
    caller should surface a clear error rather than let this crash the
    request — the official listone quotation still works on its own."""


def select_price_column(participants: int, budget: int) -> str:
    """Picks the closest of the 4 site buckets (8 or 10 teams x 350 or 500
    credits) to this league's own configuration."""
    size = "8" if participants <= 8 else "10"
    tier = "350" if abs(budget - 350) <= abs(budget - 500) else "500"
    return f"avg_{size}_{tier}"


def _parse_price(text: str) -> float | None:
    text = text.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _parse_average_prices_html(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("table tbody tr")
    if not rows:
        raise AveragePriceFetchError(
            "Nessun giocatore trovato nella pagina: la struttura del sito potrebbe essere cambiata"
        )

    players: list[dict] = []
    for row in rows:
        role_el = row.select_one(".player-pos .role")
        team_el = row.select_one(".team-name")
        surname_el = row.select_one(".player-name .text-bold")
        cells = row.select("td.vote-col-no")

        role = (role_el.get_text(strip=True) if role_el else "").upper()
        if role not in VALID_ROLES or not team_el or not surname_el or len(cells) < 7:
            continue

        surname = surname_el.get_text(strip=True)
        team = team_el.get_text(strip=True)
        if not surname or not team:
            continue

        # cells order: Kap., 8sq/350, 10sq/350, 8sq/500, 10sq/500, M.V., Pres.
        prices = {col: _parse_price(cells[i].get_text()) for i, col in enumerate(PRICE_COLUMNS, start=1)}

        players.append(
            {
                "surname_key": surname.lower(),
                "team": team,
                "role": role,
                **prices,
            }
        )

    return players


def fetch_average_prices() -> list[dict]:
    try:
        response = httpx.get(PRICES_URL, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise AveragePriceFetchError(f"Impossibile raggiungere Fantacalcio-Online: {exc}") from exc

    return _parse_average_prices_html(response.text)
