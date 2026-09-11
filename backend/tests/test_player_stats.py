from app.services.player_stats import recent_form_fantavoto


def stat(matchday, played=True, vote=6.0):
    return {"matchday": matchday, "played": played, "vote": vote if played else None}


def test_recent_form_averages_last_window_matchdays():
    stats = [stat(1, vote=5), stat(2, vote=6), stat(3, vote=7), stat(4, vote=8), stat(5, vote=9)]
    # window=4 -> giornate 2,3,4,5
    assert recent_form_fantavoto(stats, window=4) == (6 + 7 + 8 + 9) / 4


def test_recent_form_ignores_unplayed_giornate():
    stats = [stat(1, vote=6), stat(2, played=False), stat(3, vote=8)]
    assert recent_form_fantavoto(stats, window=4) == (6 + 8) / 2


def test_recent_form_fewer_than_window_giornate_available():
    stats = [stat(1, vote=7)]
    assert recent_form_fantavoto(stats, window=4) == 7.0


def test_recent_form_no_played_giornate_returns_none():
    stats = [stat(1, played=False), stat(2, played=False)]
    assert recent_form_fantavoto(stats, window=4) is None


def test_recent_form_empty_history_returns_none():
    assert recent_form_fantavoto([], window=4) is None


def test_recent_form_uses_most_recent_matchdays_not_insertion_order():
    stats = [stat(5, vote=9), stat(1, vote=1), stat(3, vote=3), stat(2, vote=2), stat(4, vote=4)]
    assert recent_form_fantavoto(stats, window=4) == (2 + 3 + 4 + 9) / 4
