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
    breakdown: list[str] = field(default_factory=list)


def compute_player_score(
    stats: list[dict],
    opponent: str | None,
    home: bool | None,
    status: str,
) -> PlayerScore:
    """`stats` is this player's match history, each a dict with keys
    matchday, played, vote, opponent, home, sorted ascending by matchday.
    `breakdown` collects one human-readable line per factor that actually
    moved the score, in the order applied — used to explain a
    recommendation in the UI, not just produce the number."""
    if status in EXCLUDING_STATUSES:
        return PlayerScore(score=None, excluded_reason=status)

    breakdown: list[str] = []

    played_entries = [s for s in stats if s["played"] and s["vote"] is not None]
    if played_entries:
        season_avg = sum(s["vote"] for s in played_entries) / len(played_entries)
        breakdown.append(f"Media voto stagionale: {season_avg:.2f} su {len(played_entries)} presenze")
    else:
        season_avg = DEFAULT_VOTE
        breakdown.append(f"Nessuno storico voti disponibile: uso il voto base {DEFAULT_VOTE:.2f}")

    recent = stats[-RECENT_FORM_WINDOW:]
    recent_played = [s for s in recent if s["played"] and s["vote"] is not None]
    if recent_played:
        recent_avg = sum(s["vote"] for s in recent_played) / len(recent_played)
        breakdown.append(f"Forma nelle ultime {len(recent_played)} giornate giocate: {recent_avg:.2f}")
    else:
        recent_avg = season_avg

    score = SEASON_WEIGHT * season_avg + RECENT_WEIGHT * recent_avg
    breakdown.append(
        f"Punteggio base ({SEASON_WEIGHT:.0%} media stagionale + {RECENT_WEIGHT:.0%} forma recente): {score:.2f}"
    )
    flags: list[str] = []

    if home is True:
        score += HOME_BONUS
        breakdown.append(f"Gioca in casa: +{HOME_BONUS:.2f}")
    elif home is False:
        score += AWAY_MALUS
        breakdown.append(f"Gioca in trasferta: {AWAY_MALUS:.2f}")

    if opponent:
        h2h = [s for s in stats if s["played"] and s["vote"] is not None and s["opponent"] == opponent]
        if h2h:
            h2h_avg = sum(s["vote"] for s in h2h) / len(h2h)
            score = (1 - HEAD_TO_HEAD_WEIGHT) * score + HEAD_TO_HEAD_WEIGHT * h2h_avg
            breakdown.append(
                f"Scontri diretti vs {opponent}: media {h2h_avg:.2f} su {len(h2h)} precedenti "
                f"(pesa {HEAD_TO_HEAD_WEIGHT:.0%} sul punteggio finale)"
            )

    if recent:
        played_count = len([s for s in recent if s["played"]])
        played_ratio = played_count / len(recent)
        if played_ratio < PRESENCE_RISK_THRESHOLD:
            score -= PRESENCE_RISK_PENALTY
            flags.append("rischio_panchina")
            breakdown.append(
                f"Ha giocato solo {played_count}/{len(recent)} delle ultime giornate: "
                f"rischio panchina (-{PRESENCE_RISK_PENALTY:.2f})"
            )

    if status == "dubbio":
        score -= DUBBIO_PENALTY
        flags.append("in_dubbio")
        breakdown.append(f"Stato \"in dubbio\": penalità -{DUBBIO_PENALTY:.2f}")
    elif status == "diffidato":
        flags.append("rischio_squalifica")
        breakdown.append("Diffidato: rischio squalifica alla prossima ammonizione (nessuna penalità al punteggio)")

    return PlayerScore(score=score, flags=flags, breakdown=breakdown)


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
