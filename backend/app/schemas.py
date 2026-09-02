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
    managers: list[ManagerCreate]


class LeagueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    ruleset: str
    budget_total: int
    roster_config: dict[str, int]
    managers: list[ManagerOut]


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
    tier: str
    is_taken: bool
    manager_id: int | None = None
    price_paid: float | None = None


class CsvImportResult(BaseModel):
    imported: int
    skipped: int
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


class RoleGap(BaseModel):
    role: str
    slots: int
    filled: int
    remaining: int


class SuggestedPlayer(BaseModel):
    player_id: int
    name: str
    team: str
    role: str
    quotation: float
