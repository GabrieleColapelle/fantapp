from app.services.lineup_logic import DEFAULT_VOTE, compute_player_score, recommend_lineup


def stat(matchday, played=True, vote=6.0, opponent="", home=True):
    return {"matchday": matchday, "played": played, "vote": vote if played else None, "opponent": opponent, "home": home}


def test_compute_score_no_data_uses_default_vote():
    result = compute_player_score([], opponent=None, home=None, status="")
    assert result.score == DEFAULT_VOTE
    assert result.excluded_reason is None


def test_compute_score_weights_recent_form_more():
    # 5 matchdays: a poor start (vote 5) followed by a strong recent run
    # (vote 8) should score higher than a flat, evenly-mixed history with
    # the same overall average, because recent form is weighted more.
    improving = [stat(1, vote=5), stat(2, vote=5), stat(3, vote=8), stat(4, vote=8), stat(5, vote=8)]
    declining = [stat(1, vote=8), stat(2, vote=8), stat(3, vote=8), stat(4, vote=5), stat(5, vote=5)]
    improving_score = compute_player_score(improving, opponent=None, home=None, status="").score
    declining_score = compute_player_score(declining, opponent=None, home=None, status="").score
    assert improving_score > declining_score


def test_compute_score_home_bonus_and_away_malus():
    stats = [stat(1, vote=6)]
    home_score = compute_player_score(stats, opponent=None, home=True, status="").score
    away_score = compute_player_score(stats, opponent=None, home=False, status="").score
    neutral_score = compute_player_score(stats, opponent=None, home=None, status="").score
    assert home_score > neutral_score > away_score


def test_compute_score_head_to_head_nudges_score():
    stats = [stat(1, vote=4, opponent="Roma"), stat(2, vote=4, opponent="Roma"), stat(3, vote=8, opponent="Lazio")]
    vs_roma = compute_player_score(stats, opponent="Roma", home=None, status="").score
    vs_unknown = compute_player_score(stats, opponent="Milan", home=None, status="").score
    assert vs_roma < vs_unknown  # history vs Roma is worse, should pull the score down


def test_compute_score_excludes_injured_and_suspended():
    for status in ("infortunato", "squalificato"):
        result = compute_player_score([], opponent=None, home=None, status=status)
        assert result.score is None
        assert result.excluded_reason == status


def test_compute_score_flags_bench_risk_when_rarely_played():
    stats = [stat(1, played=False), stat(2, played=False), stat(3, played=True, vote=6), stat(4, played=False)]
    result = compute_player_score(stats, opponent=None, home=None, status="")
    assert "rischio_panchina" in result.flags


def test_compute_score_dubbio_penalizes_and_flags():
    stats = [stat(1, vote=7)]
    normal = compute_player_score(stats, opponent=None, home=None, status="")
    dubbio = compute_player_score(stats, opponent=None, home=None, status="dubbio")
    assert dubbio.score < normal.score
    assert "in_dubbio" in dubbio.flags


def test_compute_score_diffidato_flags_without_penalty():
    stats = [stat(1, vote=7)]
    normal = compute_player_score(stats, opponent=None, home=None, status="")
    diffidato = compute_player_score(stats, opponent=None, home=None, status="diffidato")
    assert diffidato.score == normal.score
    assert "rischio_squalifica" in diffidato.flags


def test_compute_score_breakdown_explains_each_applied_factor():
    stats = [stat(1, vote=4, opponent="Roma"), stat(2, vote=8, opponent="Lazio")]
    result = compute_player_score(stats, opponent="Roma", home=True, status="dubbio")
    joined = " | ".join(result.breakdown)
    assert "Media voto stagionale" in joined
    assert "Forma nelle ultime" in joined
    assert "Gioca in casa" in joined
    assert "Scontri diretti vs Roma" in joined
    assert "in dubbio" in joined


def test_compute_score_breakdown_notes_missing_history():
    result = compute_player_score([], opponent=None, home=None, status="")
    assert any("Nessuno storico voti disponibile" in line for line in result.breakdown)


def test_compute_score_breakdown_empty_for_excluded_players():
    result = compute_player_score([], opponent=None, home=None, status="infortunato")
    assert result.breakdown == []


def player(player_id, name, role, score, excluded_reason=None, flags=None):
    return {
        "player_id": player_id,
        "name": name,
        "role": role,
        "team": "",
        "score": score,
        "excluded_reason": excluded_reason,
        "flags": flags or [],
        "opponent": None,
        "home": None,
    }


def test_recommend_lineup_fills_starters_by_role_and_score():
    players = [
        player(1, "GK1", "P", 6.5),
        player(2, "D1", "D", 7.0),
        player(3, "D2", "D", 6.8),
        player(4, "D3", "D", 6.0),
        player(5, "D4", "D", 5.5),
        player(6, "C1", "C", 7.5),
        player(7, "C2", "C", 6.0),
        player(8, "C3", "C", 5.0),
        player(9, "A1", "A", 8.0),
        player(10, "A2", "A", 7.0),
        player(11, "A3", "A", 6.0),
    ]
    result = recommend_lineup(players, "4-3-3")
    starter_names = {p["name"] for p in result["starters"]}
    assert starter_names == {"GK1", "D1", "D2", "D3", "D4", "C1", "C2", "C3", "A1", "A2", "A3"}
    assert result["bench"] == []
    assert result["excluded"] == []


def test_recommend_lineup_sends_excluded_players_to_excluded_list():
    players = [
        player(1, "GK1", "P", 6.0),
        player(2, "D1", "D", score=None, excluded_reason="infortunato"),
    ]
    result = recommend_lineup(players, "3-4-3")
    assert any(p["name"] == "D1" for p in result["excluded"])
    assert not any(p["name"] == "D1" for p in result["starters"])


def test_recommend_lineup_flags_close_ballottaggio():
    # "4-5-1" needs exactly 1 attacker: two close-scoring attackers should
    # trigger a ballottaggio between the starter and the bench alternative.
    players = [
        player(1, "GK1", "P", 6.0),
        player(2, "D1", "D", 6.0),
        player(3, "D2", "D", 6.0),
        player(4, "D3", "D", 6.0),
        player(5, "D4", "D", 6.0),
        player(6, "C1", "C", 6.0),
        player(7, "C2", "C", 6.0),
        player(8, "C3", "C", 6.0),
        player(9, "C4", "C", 6.0),
        player(10, "C5", "C", 6.0),
        player(11, "A1", "A", 7.0),
        player(12, "A2", "A", 6.9),
    ]
    result = recommend_lineup(players, "4-5-1")
    assert any(p["name"] == "A1" for p in result["starters"])
    assert any(p["name"] == "A2" for p in result["bench"])
    assert result["alternatives"] == [{"role": "A", "starter": "A1", "alternative": "A2"}]
