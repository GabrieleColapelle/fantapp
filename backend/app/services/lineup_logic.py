"""Pure functions for the lineup assistant: player scoring and formation
recommendation. Free of DB/session concerns so they're easy to unit test.
"""
from dataclasses import dataclass, field

DEFAULT_VOTE = 6.0
RECENT_FORM_WINDOW = 4
SEASON_WEIGHT = 0.4
RECENT_WEIGHT = 0.6
HOME_BONUS = 0.3
AWAY_MALUS = -0.3
HEAD_TO_HEAD_WEIGHT = 0.2
PRESENCE_RISK_THRESHOLD = 0.5
PRESENCE_RISK_PENALTY = 1.0
DUBBIO_PENALTY = 0.5
BALLOTTAGGIO_GAP = 0.5

EXCLUDING_STATUSES = {"infortunato", "squalificato"}

FORMATIONS = {
    "3-4-3": {"P": 1, "D": 3, "C": 4, "A": 3},
    "3-5-2": {"P": 1, "D": 3, "C": 5, "A": 2},
    "4-3-3": {"P": 1, "D": 4, "C": 3, "A": 3},
    "4-4-2": {"P": 1, "D": 4, "C": 4, "A": 2},
    "4-5-1": {"P": 1, "D": 4, "C": 5, "A": 1},
    "5-3-2": {"P": 1, "D": 5, "C": 3, "A": 2},
    "5-4-1": {"P": 1, "D": 5, "C": 4, "A": 1},
}


@dataclass
class PlayerScore:
    score: float | None
    excluded_reason: str | None = None
    flags: list[str] = field(default_factory=list)


def compute_player_score(
    stats: list[dict],
    opponent: str | None,
    home: bool | None,
    status: str,
) -> PlayerScore:
    """`stats` is this player's match history, each a dict with keys
    matchday, played, vote, opponent, home, sorted ascending by matchday."""
    if status in EXCLUDING_STATUSES:
        return PlayerScore(score=None, excluded_reason=status)

    played_entries = [s for s in stats if s["played"] and s["vote"] is not None]
    season_avg = sum(s["vote"] for s in played_entries) / len(played_entries) if played_entries else DEFAULT_VOTE

    recent = stats[-RECENT_FORM_WINDOW:]
    recent_played = [s for s in recent if s["played"] and s["vote"] is not None]
    recent_avg = sum(s["vote"] for s in recent_played) / len(recent_played) if recent_played else season_avg

    score = SEASON_WEIGHT * season_avg + RECENT_WEIGHT * recent_avg
    flags: list[str] = []

    if home is True:
        score += HOME_BONUS
    elif home is False:
        score += AWAY_MALUS

    if opponent:
        h2h = [s for s in stats if s["played"] and s["vote"] is not None and s["opponent"] == opponent]
        if h2h:
            h2h_avg = sum(s["vote"] for s in h2h) / len(h2h)
            score = (1 - HEAD_TO_HEAD_WEIGHT) * score + HEAD_TO_HEAD_WEIGHT * h2h_avg

    if recent:
        played_ratio = len([s for s in recent if s["played"]]) / len(recent)
        if played_ratio < PRESENCE_RISK_THRESHOLD:
            score -= PRESENCE_RISK_PENALTY
            flags.append("rischio_panchina")

    if status == "dubbio":
        score -= DUBBIO_PENALTY
        flags.append("in_dubbio")
    elif status == "diffidato":
        flags.append("rischio_squalifica")

    return PlayerScore(score=score, flags=flags)


def recommend_lineup(players: list[dict], formation: str) -> dict:
    """`players` items need: player_id, name, role, score (None if excluded),
    excluded_reason, flags. Returns starters/bench per role plus ballottaggi
    (close calls between the last starter and first bench player)."""
    slots = FORMATIONS[formation]

    excluded = [p for p in players if p["score"] is None]
    available = [p for p in players if p["score"] is not None]

    starters: list[dict] = []
    bench: list[dict] = []
    alternatives: list[dict] = []

    for role, count in slots.items():
        role_players = sorted((p for p in available if p["role"] == role), key=lambda p: p["score"], reverse=True)
        starters.extend(role_players[:count])
        role_bench = role_players[count:]
        bench.extend(role_bench)

        if len(role_players) > count and role_players[count - 1]["score"] - role_players[count]["score"] < BALLOTTAGGIO_GAP:
            alternatives.append(
                {
                    "role": role,
                    "starter": role_players[count - 1]["name"],
                    "alternative": role_players[count]["name"],
                }
            )

    bench.sort(key=lambda p: p["score"], reverse=True)

    return {
        "starters": starters,
        "bench": bench,
        "alternatives": alternatives,
        "excluded": excluded,
    }
