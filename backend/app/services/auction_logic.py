"""Pure functions for the auction assistant: deal-quality alerts, role coverage
and budget-aware suggestions. Kept free of DB/session concerns so they're easy
to unit test.
"""
from dataclasses import dataclass

GOOD_DEAL_THRESHOLD = 0.8
OVERPRICED_THRESHOLD = 1.2


@dataclass
class DealQuality:
    label: str
    detail: str


def classify_deal(price_paid: float, quotation: float) -> DealQuality:
    if quotation <= 0:
        return DealQuality(label="N/D", detail="Quotazione di listino non disponibile")

    ratio = price_paid / quotation
    if ratio <= GOOD_DEAL_THRESHOLD:
        return DealQuality(
            label="Buon affare",
            detail=f"Pagato {ratio:.0%} della quotazione ({quotation:g})",
        )
    if ratio >= OVERPRICED_THRESHOLD:
        return DealQuality(
            label="Prezzo gonfiato",
            detail=f"Pagato {ratio:.0%} della quotazione ({quotation:g})",
        )
    return DealQuality(
        label="Nella media",
        detail=f"Pagato {ratio:.0%} della quotazione ({quotation:g})",
    )


def role_gaps(roster_config: dict[str, int], filled_by_role: dict[str, int]) -> list[dict]:
    gaps = []
    for role, slots in roster_config.items():
        filled = filled_by_role.get(role, 0)
        gaps.append(
            {
                "role": role,
                "slots": slots,
                "filled": filled,
                "remaining": max(0, slots - filled),
            }
        )
    return gaps


# Standard community price tiers for the Classic auction (based on quotation
# alone, since that's what we have without historical fantamedia data):
# https://sportnews.betflag.it/asta-fantacalcio-2026-27-consigli-strategie-giocatori-da-comprare/
FASCE = [
    ("Top", 30, float("inf")),
    ("Semitop", 15, 29),
    ("Buoni", 6, 14),
    ("Scommesse", 1, 5),
]

DEFAULT_FASCIA_COUNTS = {"Top": 3, "Semitop": 4, "Buoni": 4, "Scommesse": 3}


def classify_fascia(quotation: float) -> str | None:
    for name, low, high in FASCE:
        if low <= quotation <= high:
            return name
    return None


# Recommended budget split per role (% of total credits), sourced from
# real 2026/27 auction data (50k+ purchases) and the dedicated defense-
# modifier guide:
# https://www.fantacalcio-online.com/it/consigli-fantacalcio/consigli-asta-fantacalcio-come-dividere-il-budget
# https://www.fantacalcio-online.com/it/regole/guida-modificatore-difesa
# Without the modifier the real median split is ~7/19/32/42; with it active
# a fourth/fifth defender stops being optional (a reliable *starter*, not a
# bonus punt) and guides converge on "at least 25%" for defenders, funded
# mostly by trimming midfield rather than attack.
ROLE_BUDGET_TARGETS = {"P": 7.0, "D": 19.0, "C": 32.0, "A": 42.0}
ROLE_BUDGET_TARGETS_DEFENSE_MODIFIER = {"P": 7.0, "D": 25.0, "C": 30.0, "A": 38.0}


def compute_role_budget(spent_by_role: dict[str, float], budget_total: int, defense_modifier: bool) -> list[dict]:
    """For each role, how much of the recommended budget share has been
    spent so far and how much is recommended to still be reserved for it —
    a live check against overspending one department at the expense of
    another during the auction."""
    targets = ROLE_BUDGET_TARGETS_DEFENSE_MODIFIER if defense_modifier else ROLE_BUDGET_TARGETS

    result = []
    for role, target_pct in targets.items():
        target_credits = budget_total * target_pct / 100
        spent = spent_by_role.get(role, 0.0)
        result.append(
            {
                "role": role,
                "target_pct": target_pct,
                "target_credits": target_credits,
                "spent": spent,
                "remaining_recommended": target_credits - spent,
                "pct_used": (spent / target_credits * 100) if target_credits > 0 else 0.0,
            }
        )
    return result


def suggest_players_by_fascia(
    available_players: list[dict],
    role: str,
    remaining_budget: float,
    counts: dict[str, int] | None = None,
) -> dict[str, list[dict]]:
    """Available players for `role` within the manager's remaining budget,
    grouped by price fascia (Top/Semitop/Buoni/Scommesse) so a manager can
    see options spread across the slots they still need to fill, not just
    the single most expensive handful. Best (most expensive) first within
    each fascia."""
    counts = counts or DEFAULT_FASCIA_COUNTS
    candidates = [
        p for p in available_players if p["role"] == role and p["quotation"] <= remaining_budget
    ]
    candidates.sort(key=lambda p: p["quotation"], reverse=True)

    grouped: dict[str, list[dict]] = {name: [] for name, _, _ in FASCE}
    for p in candidates:
        fascia = classify_fascia(p["quotation"])
        if fascia is not None and len(grouped[fascia]) < counts.get(fascia, 0):
            grouped[fascia].append(p)

    return grouped
