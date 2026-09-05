from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ManagerCreate(BaseModel):
    name: str
    is_me: bool = False


class ManagerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    is_me: bool


class LeagueCreate(BaseModel):
    name: str
    ruleset: str = "classic"
    budget_total: int = 500
    roster_config: dict[str, int] | None = None
    defense_modifier: bool = False
    managers: list[ManagerCreate]


class LeagueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    ruleset: str
    budget_total: int
    roster_config: dict[str, int]
    defense_modifier: bool
    managers: list[ManagerOut]


class DefenseModifierUpdate(BaseModel):
    defense_modifier: bool


class PlayerCreate(BaseModel):
    name: str
    role: str
    team: str = ""
    quotation: float = 0
    tier: str = ""


class PlayerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    role: str
    team: str
    quotation: float
    avg_auction_price: float | None = None
    starter_probability: float | None = None
    mantra_role: str = ""
    is_midfielder_bug: bool = False
    penalty_rank: int | None = None
    free_kick_rank: int | None = None
    tier: str
    status: str
    is_taken: bool
    pick_id: int | None = None
    manager_id: int | None = None
    price_paid: float | None = None


class PlayerStatusUpdate(BaseModel):
    status: str


class CsvImportResult(BaseModel):
    imported: int
    skipped: int
    errors: list[str]


class ListoneRefreshResult(BaseModel):
    imported: int
    updated: int
    errors: list[str]


class AvgPriceRefreshResult(BaseModel):
    updated: int
    unmatched: int
    errors: list[str]


class LineupsRefreshResult(BaseModel):
    starters_updated: int
    status_updated: int
    unmatched: int
    errors: list[str]


class SetPieceTakersRefreshResult(BaseModel):
    penalty_takers_updated: int
    free_kick_takers_updated: int
    unmatched: int
    errors: list[str]


class MatchVotesRefreshResult(BaseModel):
    updated: int
    unmatched: int
    errors: list[str]


class TeamStrengthRefreshResult(BaseModel):
    updated: int
    errors: list[str]


class AuctionPickCreate(BaseModel):
    player_id: int
    manager_id: int
    price_paid: float


class DealQuality(BaseModel):
    label: str
    detail: str


class AuctionPickOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    player_id: int
    manager_id: int
    price_paid: float
    created_at: datetime
    deal_quality: DealQuality


class ManagerBudget(BaseModel):
    manager_id: int
    name: str
    is_me: bool
    budget_total: int
    spent: float
    remaining: float
    players_taken: int


class RoleBudget(BaseModel):
    role: str
    target_pct: float
    target_credits: float
    spent: float
    remaining_recommended: float
    pct_used: float


class RoleGap(BaseModel):
    role: str
    slots: int
    filled: int
    remaining: int


class ManagerRoleGaps(BaseModel):
    manager_id: int
    name: str
    is_me: bool
    gaps: list[RoleGap]


class SuggestedPlayer(BaseModel):
    player_id: int
    name: str
    team: str
    role: str
    quotation: float
    avg_auction_price: float | None = None
    starter_probability: float | None = None
    is_midfielder_bug: bool = False
    penalty_rank: int | None = None
    free_kick_rank: int | None = None


class FasciaSuggestions(BaseModel):
    fascia: str
    players: list[SuggestedPlayer]


class RoleSuggestions(BaseModel):
    role: str
    fasce: list[FasciaSuggestions]


class MatchStatCreate(BaseModel):
    player_id: int
    matchday: int
    played: bool = True
    vote: float | None = None
    opponent: str = ""
    home: bool = True


class FixtureCreate(BaseModel):
    matchday: int
    team: str
    opponent: str
    home: bool = True


class FixtureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    matchday: int
    team: str
    opponent: str
    home: bool


class ScoredPlayer(BaseModel):
    player_id: int
    name: str
    role: str
    team: str
    score: float | None
    excluded_reason: str | None = None
    flags: list[str]
    opponent: str | None = None
    home: bool | None = None
    breakdown: list[str] = []
    starter_probability: float | None = None


class LineupAlternative(BaseModel):
    role: str
    starter: str
    alternative: str


class LineupRecommendation(BaseModel):
    formation: str
    starters: list[ScoredPlayer]
    bench: list[ScoredPlayer]
    alternatives: list[LineupAlternative]
    excluded: list[ScoredPlayer]
    sources: list[str] = []


class GoalkeeperOption(BaseModel):
    player_id: int
    name: str
    team: str
    opponent: str | None = None
    home: bool | None = None
    score: float | None
    excluded_reason: str | None = None
    breakdown: list[str] = []
    opponent_description: str | None = None
    recommended: bool = False


class LineupSave(BaseModel):
    manager_id: int
    matchday: int
    formation: str
    starters: list[int]
    bench: list[int]


class LineupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    manager_id: int
    matchday: int
    formation: str
    starters: list[int]
    bench: list[int]
