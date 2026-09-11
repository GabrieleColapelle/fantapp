"""Small pure stat helpers derived purely from data already stored in this
app's own DB (PlayerMatchStat) — no external source needed, unlike the
providers in services/providers/.
"""


def recent_form_fantavoto(match_stats: list[dict], window: int = 4) -> float | None:
    """Average fantavoto across a player's most recent `window` played
    giornate this season — a short-term form signal, distinct from the
    full-season average (lineup_logic) and from last season's fantamedia
    (season_stats_provider). `match_stats` items need matchday/played/vote,
    same shape used elsewhere in the app. None if the player hasn't
    played (with a recorded vote) in any of the tracked giornate."""
    played = sorted(
        (s for s in match_stats if s["played"] and s["vote"] is not None),
        key=lambda s: s["matchday"],
    )
    recent = played[-window:]
    if not recent:
        return None
    return sum(s["vote"] for s in recent) / len(recent)
