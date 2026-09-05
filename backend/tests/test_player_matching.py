from app.services.player_matching import match_avg_prices, match_match_votes, match_probable_lineups, match_set_piece_takers


def player(id, name, team, role):
    return {"id": id, "name": name, "team": team, "role": role}


def row(surname_key, team, role, price):
    return {"surname_key": surname_key, "team": team, "role": role, "avg_8_500": price}


def test_matches_on_surname_and_team_even_when_role_disagrees():
    # Dimarco is "D" on the official listone but "C" on the other source —
    # should still match since surname+team is unambiguous.
    players = [player(1, "Dimarco", "Inter", "D")]
    rows = [row("dimarco", "Inter", "C", 45.0)]
    result = match_avg_prices(players, rows, "avg_8_500")
    assert result.matched == {1: 45.0}
    assert result.unmatched == 0


def test_uses_role_as_tiebreaker_when_surname_and_team_are_ambiguous():
    players = [
        player(1, "Martinez Jo.", "Inter", "P"),
        player(2, "Martinez L.", "Inter", "A"),
    ]
    rows = [row("martinez", "Inter", "A", 156.76)]
    result = match_avg_prices(players, rows, "avg_8_500")
    assert result.matched == {2: 156.76}


def test_ambiguous_match_with_no_role_tiebreaker_is_left_unmatched():
    players = [
        player(1, "Martinez Jo.", "Inter", "P"),
        player(2, "Martinez L.", "Inter", "A"),
    ]
    rows = [row("martinez", "Inter", "C", 10.0)]  # neither candidate is role C
    result = match_avg_prices(players, rows, "avg_8_500")
    assert result.matched == {}
    assert result.unmatched == 1


def test_multiword_stored_name_matches_via_any_token():
    players = [player(1, "Lautaro Martinez", "Inter", "A")]
    rows = [row("martinez", "Inter", "A", 156.76)]
    result = match_avg_prices(players, rows, "avg_8_500")
    assert result.matched == {1: 156.76}


def test_accented_name_matches_unaccented_counterpart():
    # Our source keeps the accent ("Dodò"), the other source doesn't ("dodo").
    players = [player(1, "Dodò", "Fiorentina", "D")]
    rows = [row("dodo", "Fiorentina", "C", 12.2)]
    result = match_avg_prices(players, rows, "avg_8_500")
    assert result.matched == {1: 12.2}


def test_compound_surname_matches_via_shared_token():
    # Both sides split "Kolo Muani" into two words, sharing at least one.
    players = [player(1, "Kolo Muani", "Juventus", "A")]
    rows = [row("kolo muani", "Juventus", "A", 90.0)]
    result = match_avg_prices(players, rows, "avg_8_500")
    assert result.matched == {1: 90.0}


def test_row_without_price_for_the_selected_column_is_skipped():
    players = [player(1, "Malen", "Roma", "A")]
    rows = [{"surname_key": "malen", "team": "Roma", "role": "A", "avg_8_500": None}]
    result = match_avg_prices(players, rows, "avg_8_500")
    assert result.matched == {}
    assert result.unmatched == 0


def test_no_candidate_at_all_is_unmatched():
    players = [player(1, "Malen", "Roma", "A")]
    rows = [row("someoneelse", "Roma", "A", 10.0)]
    result = match_avg_prices(players, rows, "avg_8_500")
    assert result.matched == {}
    assert result.unmatched == 1


def lineup_starter(surname_key, team, role, is_starter, probability):
    return {"surname_key": surname_key, "team": team, "role": role, "is_starter": is_starter, "probability": probability}


def unavailable(surname_key, team, role, reason):
    return {"surname_key": surname_key, "team": team, "role": role, "reason": reason}


def test_match_probable_lineups_sets_starter_probability():
    players = [player(1, "Malen", "Roma", "A")]
    lineups = {"starters": [lineup_starter("malen", "Roma", "A", True, 91.0)], "unavailable": []}
    result = match_probable_lineups(players, lineups)
    assert result.starter_probability == {1: 91.0}
    assert result.status == {}


def test_match_probable_lineups_ignores_bench_rows():
    players = [player(1, "Osmajic", "Genoa", "A")]
    lineups = {"starters": [lineup_starter("osmajic", "Genoa", "A", False, 47.0)], "unavailable": []}
    result = match_probable_lineups(players, lineups)
    assert result.starter_probability == {}


def test_match_probable_lineups_sets_status_for_recognized_reason():
    players = [player(1, "Nuredini", "Genoa", "C")]
    lineups = {"starters": [], "unavailable": [unavailable("nuredini", "Genoa", "C", "infortunato")]}
    result = match_probable_lineups(players, lineups)
    assert result.status == {1: "infortunato"}


def test_match_probable_lineups_skips_unrecognized_reason():
    players = [player(1, "Nuredini", "Genoa", "C")]
    lineups = {"starters": [], "unavailable": [unavailable("nuredini", "Genoa", "C", None)]}
    result = match_probable_lineups(players, lineups)
    assert result.status == {}


def test_match_probable_lineups_counts_unmatched_starters():
    players = [player(1, "Malen", "Roma", "A")]
    lineups = {"starters": [lineup_starter("someoneelse", "Roma", "A", True, 90.0)], "unavailable": []}
    result = match_probable_lineups(players, lineups)
    assert result.unmatched == 1


def penalty_row(surname_key, team, rank):
    return {"surname_key": surname_key, "team": team, "rank": rank}


def test_match_set_piece_takers_sets_penalty_rank():
    players = [player(1, "Scamacca", "Atalanta", "A")]
    data = {"penalties": [penalty_row("scamacca", "Atalanta", 1)], "free_kicks": []}
    result = match_set_piece_takers(players, data)
    assert result.penalty_rank == {1: 1}
    assert result.free_kick_rank == {}


def test_match_set_piece_takers_orders_multiple_takers():
    players = [player(1, "Scamacca", "Atalanta", "A"), player(2, "Krstovic", "Atalanta", "A")]
    data = {
        "penalties": [penalty_row("scamacca", "Atalanta", 1), penalty_row("krstovic", "Atalanta", 2)],
        "free_kicks": [],
    }
    result = match_set_piece_takers(players, data)
    assert result.penalty_rank == {1: 1, 2: 2}


def test_match_set_piece_takers_sets_free_kick_rank_independently():
    players = [player(1, "Calhanoglu", "Inter", "C"), player(2, "Dimarco", "Inter", "D")]
    data = {
        "penalties": [penalty_row("calhanoglu", "Inter", 1)],
        "free_kicks": [penalty_row("calhanoglu", "Inter", 1), penalty_row("dimarco", "Inter", 2)],
    }
    result = match_set_piece_takers(players, data)
    assert result.penalty_rank == {1: 1}
    assert result.free_kick_rank == {1: 1, 2: 2}


def test_match_set_piece_takers_counts_unmatched_across_both_lists():
    players = [player(1, "Malen", "Roma", "A")]
    data = {"penalties": [penalty_row("someoneelse", "Roma", 1)], "free_kicks": [penalty_row("another", "Roma", 1)]}
    result = match_set_piece_takers(players, data)
    assert result.penalty_rank == {}
    assert result.unmatched == 2


def vote_row(name, team, opponent, home, vote):
    return {"name": name, "team": team, "opponent": opponent, "home": home, "vote": vote}


def test_match_match_votes_sets_vote_opponent_and_home():
    players = [player(1, "Carnesecchi", "Atalanta", "P")]
    rows = [vote_row("Carnesecchi", "Atalanta", "Sassuolo", True, 6.5)]
    result = match_match_votes(players, rows)
    assert result.matched == {1: {"vote": 6.5, "opponent": "Sassuolo", "home": True}}
    assert result.unmatched == 0


def test_match_match_votes_matches_full_name_to_abbreviated_stored_name():
    players = [player(1, "Martinez L.", "Inter", "A")]
    rows = [vote_row("Lautaro Martinez", "Inter", "Monza", True, 7.0)]
    result = match_match_votes(players, rows)
    assert result.matched == {1: {"vote": 7.0, "opponent": "Monza", "home": True}}


def test_match_match_votes_counts_unmatched():
    players = [player(1, "Malen", "Roma", "A")]
    rows = [vote_row("Someone Else", "Roma", "Fiorentina", True, 6.0)]
    result = match_match_votes(players, rows)
    assert result.matched == {}
    assert result.unmatched == 1
