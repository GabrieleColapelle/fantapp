"""Provider that fetches probable starting lineups from Fantacalcio-Online,
which already cross-references and weight-averages multiple editorial
sources (Fantacalcio.it, Gazzetta, SOS Fanta, Sky) into one "starter
probability" per player for the upcoming matchday — exactly the
cross-source averaging that would otherwise have to be built by hand. No
login needed. Isolated the same way as the other providers: if this
breaks, the rest of the app (manual player status, CSV import) still
works.
"""
import httpx
from bs4 import BeautifulSoup

LINEUPS_URL = "https://www.fantacalcio-online.com/it/serie-a/2026-2027/probabili-formazioni/ultima-giornata"
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; fantapp/1.0)"}
REQUEST_TIMEOUT = 10

VALID_ROLES = {"P", "D", "C", "A"}

UNAVAILABLE_REASON_MAP = {
    "infortunato": "infortunato",
    "squalificato": "squalificato",
    "diffidato": "diffidato",
}


class LineupsFetchError(Exception):
    """Raised when the probable-lineups page can't be fetched or parsed.
    The caller should surface a clear error rather than crash — manual
    player status entry (Modulo 2) still works on its own."""


def _parse_percentage(text: str) -> float | None:
    text = text.strip().replace("%", "")
    if not text or text == "–":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _name_parts(name_el) -> str:
    """`.prb-nome` holds the surname as direct text plus a nested <small>
    with a disambiguating initial, e.g. "BALDANZI" + "T" -> "Baldanzi T"."""
    small = name_el.find("small")
    surname = name_el.get_text(strip=True)
    if small:
        initial = small.get_text(strip=True)
        surname = surname[: -len(initial)] if surname.endswith(initial) else surname
    return surname.strip()


def _parse_lineups_html(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    team_blocks = soup.select(".prb-squadra")
    if not team_blocks:
        raise LineupsFetchError(
            "Nessuna squadra trovata nella pagina: la struttura del sito potrebbe essere cambiata"
        )

    starters: list[dict] = []
    unavailable: list[dict] = []

    for block in team_blocks:
        team_el = block.select_one(".prb-squadra__nome")
        if not team_el:
            continue
        team = team_el.get_text(strip=True)

        for table in block.select("table.prb-tabella"):
            caption = table.select_one("caption")
            is_starter = bool(caption and "titolari" in caption.get_text().lower())

            for row in table.select("tbody tr"):
                role_el = row.select_one(".role")
                name_el = row.select_one(".prb-nome")
                media_el = row.select_one("td.prb-cella--media span")
                if not role_el or not name_el:
                    continue

                role = role_el.get_text(strip=True).upper()
                if role not in VALID_ROLES:
                    continue

                starters.append(
                    {
                        "team": team,
                        "role": role,
                        "surname_key": _name_parts(name_el).lower(),
                        "is_starter": is_starter,
                        "probability": _parse_percentage(media_el.get_text()) if media_el else None,
                    }
                )

        for row in block.select(".prb-fuori__riga"):
            name_el = row.select_one(".prb-nome")
            reason_el = row.select_one(".fco-etichetta")
            if not name_el or not reason_el:
                continue
            role_el = row.select_one(".role")
            unavailable.append(
                {
                    "team": team,
                    "role": role_el.get_text(strip=True).upper() if role_el else None,
                    "surname_key": _name_parts(name_el).lower(),
                    "reason": UNAVAILABLE_REASON_MAP.get(reason_el.get_text(strip=True).lower()),
                }
            )

    return {"starters": starters, "unavailable": unavailable}


def fetch_probable_lineups() -> dict:
    try:
        response = httpx.get(LINEUPS_URL, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise LineupsFetchError(f"Impossibile raggiungere Fantacalcio-Online: {exc}") from exc

    return _parse_lineups_html(response.text)
