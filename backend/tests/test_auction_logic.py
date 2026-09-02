from app.services.auction_logic import classify_deal, classify_fascia, role_gaps, suggest_players_by_fascia


def test_classify_deal_good_deal():
    deal = classify_deal(price_paid=8, quotation=15)
    assert deal.label == "Buon affare"


def test_classify_deal_overpriced():
    deal = classify_deal(price_paid=20, quotation=10)
    assert deal.label == "Prezzo gonfiato"


def test_classify_deal_average():
    deal = classify_deal(price_paid=10, quotation=10)
    assert deal.label == "Nella media"


def test_classify_deal_missing_quotation():
    deal = classify_deal(price_paid=10, quotation=0)
    assert deal.label == "N/D"


def test_role_gaps_counts_remaining_slots():
    gaps = role_gaps({"P": 3, "D": 8}, {"P": 1})
    by_role = {g["role"]: g for g in gaps}
    assert by_role["P"]["remaining"] == 2
    assert by_role["D"]["remaining"] == 8


def test_role_gaps_never_negative():
    gaps = role_gaps({"P": 3}, {"P": 5})
    assert gaps[0]["remaining"] == 0


def test_classify_fascia_thresholds():
    assert classify_fascia(35) == "Top"
    assert classify_fascia(30) == "Top"
    assert classify_fascia(29) == "Semitop"
    assert classify_fascia(15) == "Semitop"
    assert classify_fascia(14) == "Buoni"
    assert classify_fascia(6) == "Buoni"
    assert classify_fascia(5) == "Scommesse"
    assert classify_fascia(1) == "Scommesse"


def test_classify_fascia_below_range_is_none():
    assert classify_fascia(0) is None


def test_suggest_players_by_fascia_filters_by_role_and_budget():
    players = [
        {"player_id": 1, "name": "A", "team": "X", "role": "A", "quotation": 30},
        {"player_id": 2, "name": "B", "team": "Y", "role": "A", "quotation": 10},
        {"player_id": 3, "name": "C", "team": "Z", "role": "D", "quotation": 5},
    ]
    result = suggest_players_by_fascia(players, role="A", remaining_budget=15)
    all_players = [p for group in result.values() for p in group]
    assert [p["player_id"] for p in all_players] == [2]


def test_suggest_players_by_fascia_groups_and_sorts_within_group():
    players = [
        {"player_id": 1, "name": "A", "team": "X", "role": "A", "quotation": 35},
        {"player_id": 2, "name": "B", "team": "Y", "role": "A", "quotation": 32},
        {"player_id": 3, "name": "C", "team": "Y", "role": "A", "quotation": 20},
        {"player_id": 4, "name": "D", "team": "Y", "role": "A", "quotation": 3},
    ]
    result = suggest_players_by_fascia(players, role="A", remaining_budget=100)
    assert [p["player_id"] for p in result["Top"]] == [1, 2]
    assert [p["player_id"] for p in result["Semitop"]] == [3]
    assert [p["player_id"] for p in result["Scommesse"]] == [4]
    assert result["Buoni"] == []


def test_suggest_players_by_fascia_respects_per_fascia_limit():
    players = [
        {"player_id": i, "name": str(i), "team": "X", "role": "A", "quotation": 3}
        for i in range(10)
    ]
    result = suggest_players_by_fascia(players, role="A", remaining_budget=100, counts={"Scommesse": 2})
    assert len(result["Scommesse"]) == 2
