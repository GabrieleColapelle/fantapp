"""Matches players already in a league against rows from an external source
(e.g. Fantacalcio-Online's average prices or probable lineups) that doesn't
share a common ID. Kept as pure functions, separate from the DB/router, so
the matching rules (and their edge cases) are easy to unit test.
"""
import unicodedata
from dataclasses import dataclass


def _fold(text: str) -> str:
    """Lowercases and strips accents (e.g. "Dodò" -> "dodo") so the two
    sources matching a name differently on diacritics (common for
    Portuguese/French names) still line up."""
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


class PlayerNameIndex:
    """Indexes players by every (name token, team) pair so a source that
    only gives a surname (e.g. "Martinez" for "Lautaro Martinez") or splits
    a compound surname differently (e.g. "Kolo Muani") can still be found —
    a match succeeds as long as the two sources share at least one name
    token for that team.
    """

    def __init__(self, players: list[dict]):
        self._by_token: dict[tuple[str, str], list[dict]] = {}
        for p in players:
            for token in _fold(p["name"]).split():
                self._by_token.setdefault((token, _fold(p["team"])), []).append(p)

    def resolve(self, surname_key: str, team: str, role: str | None) -> dict | None:
        """Matches on (name token, team) first: the two sources don't
        always agree on a player's role (e.g. Dimarco is "D" on the
        official listone but "C" on Fantacalcio-Online), so requiring an
        exact role match would drop real matches. `role` is only used as a
        tiebreaker when a name+team is genuinely ambiguous (e.g. two
        "Martinez" at Inter: one keeper, one striker)."""
        team = _fold(team)
        candidates: list[dict] = []
        seen_ids = set()
        for token in _fold(surname_key).split():
            for c in self._by_token.get((token, team), []):
                if c["id"] not in seen_ids:
                    seen_ids.add(c["id"])
                    candidates.append(c)

        if len(candidates) == 1:
            return candidates[0]
        if len(candidates) > 1 and role:
            same_role = [c for c in candidates if c["role"] == role]
            if len(same_role) == 1:
                return same_role[0]
        return None


@dataclass
class MatchResult:
    matched: dict[int, float]  # player_id -> price
    unmatched: int


def match_avg_prices(players: list[dict], rows: list[dict], column: str) -> MatchResult:
    """`players`: existing league players as dicts with id/name/team/role.
    `rows`: parsed rows from fetch_average_prices(), each with
    surname_key/team/role plus the price columns. `column` is which price
    column to use (see select_price_column)."""
    index = PlayerNameIndex(players)
    matched: dict[int, float] = {}
    unmatched = 0

    for row in rows:
        price = row.get(column)
        if price is None:
            continue

        player = index.resolve(row["surname_key"], row["team"], row["role"])
        if player:
            matched[player["id"]] = price
        else:
            unmatched += 1

    return MatchResult(matched=matched, unmatched=unmatched)


@dataclass
class LineupMatchResult:
    starter_probability: dict[int, float | None]  # player_id -> probability (None if unknown)
    status: dict[int, str]  # player_id -> "infortunato"/"squalificato"/"diffidato"
    unmatched: int


def match_probable_lineups(players: list[dict], lineups: dict) -> LineupMatchResult:
    """`players`: existing league players as dicts with id/name/team/role.
    `lineups`: the dict returned by fetch_probable_lineups() (starters +
    unavailable). Only the *starters* table sets starter_probability
    (bench-table rows are skipped: a low "will come off the bench"
    percentage isn't the auction signal we want). Unavailable players get
    their `status` set only for reasons we recognize (see
    UNAVAILABLE_REASON_MAP in the provider) — an unrecognized reason is
    left alone rather than guessed.
    """
    index = PlayerNameIndex(players)
    starter_probability: dict[int, float | None] = {}
    status: dict[int, str] = {}
    unmatched = 0

    for row in lineups["starters"]:
        if not row["is_starter"]:
            continue
        player = index.resolve(row["surname_key"], row["team"], row["role"])
        if player:
            starter_probability[player["id"]] = row["probability"]
        else:
            unmatched += 1

    for row in lineups["unavailable"]:
        if not row["reason"]:
            continue
        player = index.resolve(row["surname_key"], row["team"], row["role"])
        if player:
            status[player["id"]] = row["reason"]

    return LineupMatchResult(starter_probability=starter_probability, status=status, unmatched=unmatched)


@dataclass
class SetPieceTakersMatchResult:
    penalty_rank: dict[int, int]  # player_id -> rank (1 = first choice)
    free_kick_rank: dict[int, int]
    unmatched: int


def _match_ranked_rows(index: "PlayerNameIndex", rows: list[dict]) -> tuple[dict[int, int], int]:
    rank_by_player: dict[int, int] = {}
    unmatched = 0
    for row in rows:
        player = index.resolve(row["surname_key"], row["team"], role=None)
        if player:
            rank_by_player[player["id"]] = row["rank"]
        else:
            unmatched += 1
    return rank_by_player, unmatched


def match_set_piece_takers(players: list[dict], data: dict) -> SetPieceTakersMatchResult:
    """`players`: existing league players as dicts with id/name/team (role
    not needed here — the source doesn't carry one, so matching relies on
    name+team alone; a genuinely ambiguous name+team is left unmatched
    rather than guessed, same as everywhere else). `data`: the dict
    returned by fetch_set_piece_takers() (penalties + free_kicks)."""
    index = PlayerNameIndex(players)
    penalty_rank, unmatched_penalties = _match_ranked_rows(index, data["penalties"])
    free_kick_rank, unmatched_free_kicks = _match_ranked_rows(index, data["free_kicks"])

    return SetPieceTakersMatchResult(
        penalty_rank=penalty_rank,
        free_kick_rank=free_kick_rank,
        unmatched=unmatched_penalties + unmatched_free_kicks,
    )
