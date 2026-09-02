from app.services.player_matching import match_avg_prices


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
