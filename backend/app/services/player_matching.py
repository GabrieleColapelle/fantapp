"""Matches players already in a league against rows from an external source
(e.g. Fantacalcio-Online's average prices) that doesn't share a common ID.
Kept as a pure function, separate from the DB/router, so the matching rules
(and their edge cases) are easy to unit test.
"""
import unicodedata
from dataclasses import dataclass


@dataclass
class MatchResult:
    matched: dict[int, float]  # player_id -> price
    unmatched: int


def _fold(text: str) -> str:
    """Lowercases and strips accents (e.g. "Dodò" -> "dodo") so the two
    sources matching a name differently on diacritics (common for
    Portuguese/French names) still line up."""
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def match_avg_prices(players: list[dict], rows: list[dict], column: str) -> MatchResult:
    """`players`: existing league players as dicts with id/name/team/role.
    `rows`: parsed rows from fetch_average_prices(), each with
    surname_key/team/role plus the price columns. `column` is which price
    column to use (see select_price_column).

    Matches on (name token, team) first: the two sources don't always agree
    on a player's role (e.g. Dimarco is "D" on the official listone but "C"
    on Fantacalcio-Online), so requiring an exact role match would drop
    real matches. Role is only used as a tiebreaker when a name+team is
    genuinely ambiguous (e.g. two "Martinez" at Inter: one keeper, one
    striker). `surname_key` can itself be multi-word (e.g. "kolo muani",
    "de bruyne") — every word is tried against every word of the stored
    name, so a match succeeds as long as the two sources share at least one
    name token for that team, even if they order/split a compound surname
    differently.
    """
    players_by_name_team: dict[tuple[str, str], list[dict]] = {}
    for p in players:
        for token in _fold(p["name"]).split():
            players_by_name_team.setdefault((token, _fold(p["team"])), []).append(p)

    matched: dict[int, float] = {}
    unmatched = 0

    for row in rows:
        price = row.get(column)
        if price is None:
            continue

        team = _fold(row["team"])
        candidates = []
        seen_ids = set()
        for token in _fold(row["surname_key"]).split():
            for c in players_by_name_team.get((token, team), []):
                if c["id"] not in seen_ids:
                    seen_ids.add(c["id"])
                    candidates.append(c)

        player = None
        if len(candidates) == 1:
            player = candidates[0]
        elif len(candidates) > 1:
            same_role = [c for c in candidates if c["role"] == row["role"]]
            if len(same_role) == 1:
                player = same_role[0]

        if player:
            matched[player["id"]] = price
        else:
            unmatched += 1

    return MatchResult(matched=matched, unmatched=unmatched)
