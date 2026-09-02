from app.services.auction_logic import classify_deal, role_gaps, suggest_players


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


def test_suggest_players_filters_by_role_and_budget():
    players = [
        {"player_id": 1, "name": "A", "team": "X", "role": "A", "quotation": 30},
        {"player_id": 2, "name": "B", "team": "Y", "role": "A", "quotation": 10},
        {"player_id": 3, "name": "C", "team": "Z", "role": "D", "quotation": 5},
    ]
    result = suggest_players(players, role="A", remaining_budget=15)
    assert [p["player_id"] for p in result] == [2]


def test_suggest_players_sorted_best_first():
    players = [
        {"player_id": 1, "name": "A", "team": "X", "role": "A", "quotation": 10},
        {"player_id": 2, "name": "B", "team": "Y", "role": "A", "quotation": 20},
    ]
    result = suggest_players(players, role="A", remaining_budget=100)
    assert [p["player_id"] for p in result] == [2, 1]
