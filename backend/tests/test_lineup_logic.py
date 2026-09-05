from app.services.lineup_logic import (
    DEFAULT_VOTE,
    compute_player_score,
    describe_opponent_attack,
    rank_teams_by_attack,
    recommend_lineup,
)


def stat(matchday, played=True, vote=6.0, opponent="", home=True):
    return {"matchday": matchday, "played": played, "vote": vote if played else None, "opponent": opponent, "home": home}


def test_compute_score_no_data_uses_default_vote():
    result = compute_player_score([], opponent=None, home=None, status="", role="D")
    assert result.score == DEFAULT_VOTE
    assert result.excluded_reason is None


def test_compute_score_weights_recent_form_more():
    # 5 matchdays: a poor start (vote 5) followed by a strong recent run
    # (vote 8) should score higher than a flat, evenly-mixed history with
    # the same overall average, because recent form is weighted more.
    improving = [stat(1, vote=5), stat(2, vote=5), stat(3, vote=8), stat(4, vote=8), stat(5, vote=8)]
    declining = [stat(1, vote=8), stat(2, vote=8), stat(3, vote=8), stat(4, vote=5), stat(5, vote=5)]
    improving_score = compute_player_score(improving, opponent=None, home=None, status="", role="D").score
    declining_score = compute_player_score(declining, opponent=None, home=None, status="", role="D").score
    assert improving_score > declining_score


def test_compute_score_home_bonus_and_away_malus():
    stats = [stat(1, vote=6)]
    home_score = compute_player_score(stats, opponent=None, home=True, status="", role="D").score
    away_score = compute_player_score(stats, opponent=None, home=False, status="", role="D").score
    neutral_score = compute_player_score(stats, opponent=None, home=None, status="", role="D").score
    assert home_score > neutral_score > away_score


def test_compute_score_head_to_head_nudges_score():
    stats = [stat(1, vote=4, opponent="Roma"), stat(2, vote=4, opponent="Roma"), stat(3, vote=8, opponent="Lazio")]
    vs_roma = compute_player_score(stats, opponent="Roma", home=None, status="", role="D").score
    vs_unknown = compute_player_score(stats, opponent="Milan", home=None, status="", role="D").score
    assert vs_roma < vs_unknown  # history vs Roma is worse, should pull the score down


def test_compute_score_excludes_injured_and_suspended():
    for status in ("infortunato", "squalificato"):
        result = compute_player_score([], opponent=None, home=None, status=status, role="D")
        assert result.score is None
        assert result.excluded_reason == status


def test_compute_score_flags_bench_risk_when_rarely_played():
    stats = [stat(1, played=False), stat(2, played=False), stat(3, played=True, vote=6), stat(4, played=False)]
    result = compute_player_score(stats, opponent=None, home=None, status="", role="D")
    assert "rischio_panchina" in result.flags


def test_compute_score_dubbio_penalizes_and_flags():
    stats = [stat(1, vote=7)]
    normal = compute_player_score(stats, opponent=None, home=None, status="", role="D")
    dubbio = compute_player_score(stats, opponent=None, home=None, status="dubbio", role="D")
    assert dubbio.score < normal.score
    assert "in_dubbio" in dubbio.flags


def test_compute_score_diffidato_flags_without_penalty():
    stats = [stat(1, vote=7)]
    normal = compute_player_score(stats, opponent=None, home=None, status="", role="D")
    diffidato = compute_player_score(stats, opponent=None, home=None, status="diffidato", role="D")
    assert diffidato.score == normal.score
    assert "rischio_squalifica" in diffidato.flags


def test_compute_score_breakdown_explains_each_applied_factor():
    stats = [stat(1, vote=4, opponent="Roma"), stat(2, vote=8, opponent="Lazio")]
    result = compute_player_score(stats, opponent="Roma", home=True, status="dubbio", role="D")
    joined = " | ".join(result.breakdown)
    assert "Media voto stagionale" in joined
    assert "Forma nelle ultime" in joined
    assert "Gioca in casa" in joined
    assert "Scontri diretti vs Roma" in joined
    assert "in dubbio" in joined


def test_compute_score_breakdown_notes_missing_history():
    result = compute_player_score([], opponent=None, home=None, status="", role="D")
    assert any("Nessuno storico voti disponibile" in line for line in result.breakdown)


def test_compute_score_breakdown_empty_for_excluded_players():
    result = compute_player_score([], opponent=None, home=None, status="infortunato", role="D")
    assert result.breakdown == []


def strength(played, goals_for_per_game, goals_against_per_game):
    return {"played": played, "goals_for_per_game": goals_for_per_game, "goals_against_per_game": goals_against_per_game}


def test_opponent_strength_rewards_defender_against_weak_attack():
    stats = [stat(1, vote=6)]
    weak_attack = strength(played=5, goals_for_per_game=0.5, goals_against_per_game=1.5)
    strong_attack = strength(played=5, goals_for_per_game=2.5, goals_against_per_game=1.5)
    vs_weak = compute_player_score(stats, opponent="X", home=None, status="", role="D", opponent_strength=weak_attack)
    vs_strong = compute_player_score(
        stats, opponent="X", home=None, status="", role="D", opponent_strength=strong_attack
    )
    no_data = compute_player_score(stats, opponent="X", home=None, status="", role="D")
    assert vs_weak.score > no_data.score > vs_strong.score


def test_opponent_strength_rewards_attacker_against_leaky_defense():
    stats = [stat(1, vote=6)]
    leaky_defense = strength(played=5, goals_for_per_game=1.5, goals_against_per_game=2.5)
    solid_defense = strength(played=5, goals_for_per_game=1.5, goals_against_per_game=0.5)
    vs_leaky = compute_player_score(stats, opponent="X", home=None, status="", role="A", opponent_strength=leaky_defense)
    vs_solid = compute_player_score(
        stats, opponent="X", home=None, status="", role="A", opponent_strength=solid_defense
    )
    assert vs_leaky.score > vs_solid.score


def test_opponent_strength_uses_attack_rate_for_goalkeepers_too():
    stats = [stat(1, vote=6)]
    weak_attack = strength(played=5, goals_for_per_game=0.5, goals_against_per_game=1.5)
    result = compute_player_score(stats, opponent="X", home=None, status="", role="P", opponent_strength=weak_attack)
    baseline = compute_player_score(stats, opponent="X", home=None, status="", role="P")
    assert result.score > baseline.score


def test_opponent_strength_flags_small_sample_as_provisional():
    stats = [stat(1, vote=6)]
    result = compute_player_score(
        stats, opponent="X", home=None, status="", role="D", opponent_strength=strength(2, 0.5, 1.5)
    )
    assert any("provvisorio" in line for line in result.breakdown)


def test_opponent_strength_no_provisional_note_with_enough_games():
    stats = [stat(1, vote=6)]
    result = compute_player_score(
        stats, opponent="X", home=None, status="", role="D", opponent_strength=strength(10, 0.5, 1.5)
    )
    assert not any("provvisorio" in line for line in result.breakdown)


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


def test_rank_teams_by_attack_weakest_first():
    rates = {"Venezia": 0.5, "Napoli": 2.5, "Udinese": 1.5}
    ranks = rank_teams_by_attack(rates)
    assert ranks == {"Venezia": 1, "Udinese": 2, "Napoli": 3}


def test_describe_opponent_attack_flags_weak_attack():
    text = describe_opponent_attack("Venezia", rate=0.5, played=5, rank=1, total=20)
    assert "Venezia" in text
    assert "più deboli" in text


def test_describe_opponent_attack_flags_dangerous_attack():
    text = describe_opponent_attack("Napoli", rate=2.5, played=5, rank=19, total=20)
    assert "più pericolosi" in text


def test_describe_opponent_attack_flags_average_attack():
    text = describe_opponent_attack("Udinese", rate=1.3, played=5, rank=10, total=20)
    assert "nella media" in text


def test_describe_opponent_attack_notes_small_sample():
    text = describe_opponent_attack("Venezia", rate=0.5, played=2, rank=1, total=20)
    assert "provvisorio" in text


def test_describe_opponent_attack_no_note_with_enough_games():
    text = describe_opponent_attack("Venezia", rate=0.5, played=5, rank=1, total=20)
    assert "provvisorio" not in text
