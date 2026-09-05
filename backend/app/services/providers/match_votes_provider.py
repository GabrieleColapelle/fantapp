"""Provider that fetches the official matchday votes ("voti fantacalcio")
from Fantacalcio.it for an already-played giornata: the fantavoto (voto +
bonus/malus already applied) for every player who took the pitch, plus the
opponent and home/away flag for that match, read straight off the same
page — no separate calendar lookup needed for a giornata already played.
Kept isolated so it can be swapped/dropped like the other providers: if
this breaks, matchday stats can still be imported by CSV.
"""
from datetime import date

import httpx
from bs4 import BeautifulSoup

VOTES_URL_TEMPLATE = "https://www.fantacalcio.it/voti-fantacalcio-serie-a/{season}/{matchday}"
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; fantapp/1.0)"}
REQUEST_TIMEOUT = 10


def _current_season() -> str:
    """Serie A season string as used in Fantacalcio.it URLs (e.g. "2026-27").
    The season runs July through June, so before July we're still in the
    season that started the previous calendar year."""
    today = date.today()
    start_year = today.year if today.month >= 7 else today.year - 1
    return f"{start_year}-{str(start_year + 1)[2:]}"


class MatchVotesFetchError(Exception):
    """Raised when a giornata's votes can't be fetched or parsed. The
    caller should surface a clear error and suggest the CSV import as a
    fallback, rather than let this crash the request."""


def _parse_grade(raw: str | None) -> float | None:
    """Grades are comma-decimal ("6,5"). One specific template quirk renders
    the default "no rating available" substitute vote without its comma
    ("55" instead of "5,5") — that's the only case rewritten here. Anything
    else is taken at face value: fantavoto (unlike voto) has no upper
    bound, so a big game genuinely reads "17,5" and must not be treated as
    malformed just for being over 10."""
    raw = (raw or "").strip()
    if not raw:
        return None
    if raw == "55":
        return 5.5
    try:
        return float(raw.replace(",", "."))
    except ValueError:
        return None


def _parse_votes_html(html: str, matchday: int) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    team_tables = soup.select("li.team-table")
    if not team_tables:
        raise MatchVotesFetchError(
            "Nessuna partita trovata per questa giornata: la struttura del sito potrebbe essere "
            "cambiata, oppure la giornata non è ancora stata giocata"
        )

    rows: list[dict] = []
    for table in team_tables:
        # Header reads e.g. "<span>Atalanta</span><span>2</span><span>-</span>
        # <span>1</span><span>Sassuolo</span>": first name is always the home
        # team (matches the site's own score-home/score-away convention),
        # and whichever side carries "current" is the team this table's
        # player rows belong to.
        header_spans = table.select(".match-score span")
        if len(header_spans) < 5:
            continue
        home_name = header_spans[0].get_text(strip=True)
        away_name = header_spans[-1].get_text(strip=True)
        is_home = "current" in (header_spans[0].get("class") or [])
        team = home_name if is_home else away_name
        opponent = away_name if is_home else home_name

        for player_row in table.select("tbody tr"):
            name_el = player_row.select_one(".player-name span")
            # Three vote "pills" per row (Redazione Fantacalcio, Voto
            # Statistico, Voto Italia) always appear in that order — the
            # first is the canonical fantacalcio.it fantavoto most leagues
            # score against.
            grade_el = player_row.select_one(".pill .player-fanta-grade")
            if not name_el or not grade_el:
                continue
            vote = _parse_grade(grade_el.get("data-value"))
            if vote is None:
                continue

            rows.append(
                {
                    "name": name_el.get_text(strip=True),
                    "team": team,
                    "opponent": opponent,
                    "home": is_home,
                    "matchday": matchday,
                    "vote": vote,
                }
            )

    return rows


def fetch_match_votes(matchday: int) -> list[dict]:
    url = VOTES_URL_TEMPLATE.format(season=_current_season(), matchday=matchday)
    try:
        response = httpx.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise MatchVotesFetchError(f"Impossibile raggiungere Fantacalcio.it: {exc}") from exc

    return _parse_votes_html(response.text, matchday)
