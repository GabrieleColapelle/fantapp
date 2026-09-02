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


def suggest_players(
    available_players: list[dict],
    role: str,
    remaining_budget: float,
    limit: int = 5,
) -> list[dict]:
    """Top-quotation available players for `role` that fit within the
    manager's remaining budget, best (most expensive/valuable) first."""
    candidates = [
        p for p in available_players if p["role"] == role and p["quotation"] <= remaining_budget
    ]
    candidates.sort(key=lambda p: p["quotation"], reverse=True)
    return candidates[:limit]
