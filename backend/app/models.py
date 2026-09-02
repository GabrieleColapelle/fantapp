from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

DEFAULT_ROSTER_CONFIG = {"P": 3, "D": 8, "C": 8, "A": 6}


class League(Base):
    __tablename__ = "leagues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    ruleset: Mapped[str] = mapped_column(String, default="classic")
    budget_total: Mapped[int] = mapped_column(Integer, default=500)
    roster_config: Mapped[dict] = mapped_column(JSON, default=lambda: dict(DEFAULT_ROSTER_CONFIG))

    managers: Mapped[list["Manager"]] = relationship(back_populates="league", cascade="all, delete-orphan")
    players: Mapped[list["Player"]] = relationship(back_populates="league", cascade="all, delete-orphan")
    picks: Mapped[list["AuctionPick"]] = relationship(back_populates="league", cascade="all, delete-orphan")
    fixtures: Mapped[list["Fixture"]] = relationship(back_populates="league", cascade="all, delete-orphan")
    lineups: Mapped[list["Lineup"]] = relationship(back_populates="league", cascade="all, delete-orphan")


class Manager(Base):
    __tablename__ = "managers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    is_me: Mapped[bool] = mapped_column(Boolean, default=False)

    league: Mapped["League"] = relationship(back_populates="managers")
    picks: Mapped[list["AuctionPick"]] = relationship(back_populates="manager", cascade="all, delete-orphan")


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    team: Mapped[str] = mapped_column(String, default="")
    quotation: Mapped[float] = mapped_column(Float, default=0)
    tier: Mapped[str] = mapped_column(String, default="")
    status: Mapped[str] = mapped_column(String, default="")
    avg_auction_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    starter_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    mantra_role: Mapped[str] = mapped_column(String, default="")
    is_midfielder_bug: Mapped[bool] = mapped_column(Boolean, default=False)
    penalty_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    free_kick_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)

    league: Mapped["League"] = relationship(back_populates="players")
    pick: Mapped["AuctionPick | None"] = relationship(back_populates="player", uselist=False)
    match_stats: Mapped[list["PlayerMatchStat"]] = relationship(
        back_populates="player", cascade="all, delete-orphan"
    )


class AuctionPick(Base):
    __tablename__ = "auction_picks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), nullable=False)
    manager_id: Mapped[int] = mapped_column(ForeignKey("managers.id"), nullable=False)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, unique=True)
    price_paid: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    league: Mapped["League"] = relationship(back_populates="picks")
    manager: Mapped["Manager"] = relationship(back_populates="picks")
    player: Mapped["Player"] = relationship(back_populates="pick")


class PlayerMatchStat(Base):
    __tablename__ = "player_match_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    matchday: Mapped[int] = mapped_column(Integer, nullable=False)
    played: Mapped[bool] = mapped_column(Boolean, default=True)
    vote: Mapped[float | None] = mapped_column(Float, nullable=True)
    opponent: Mapped[str] = mapped_column(String, default="")
    home: Mapped[bool] = mapped_column(Boolean, default=True)

    player: Mapped["Player"] = relationship(back_populates="match_stats")

    __table_args__ = (UniqueConstraint("player_id", "matchday", name="uq_player_matchday"),)


class Fixture(Base):
    __tablename__ = "fixtures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), nullable=False)
    matchday: Mapped[int] = mapped_column(Integer, nullable=False)
    team: Mapped[str] = mapped_column(String, nullable=False)
    opponent: Mapped[str] = mapped_column(String, nullable=False)
    home: Mapped[bool] = mapped_column(Boolean, default=True)

    league: Mapped["League"] = relationship(back_populates="fixtures")

    __table_args__ = (UniqueConstraint("league_id", "matchday", "team", name="uq_league_matchday_team"),)


class Lineup(Base):
    __tablename__ = "lineups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), nullable=False)
    manager_id: Mapped[int] = mapped_column(ForeignKey("managers.id"), nullable=False)
    matchday: Mapped[int] = mapped_column(Integer, nullable=False)
    formation: Mapped[str] = mapped_column(String, nullable=False)
    starters: Mapped[list[int]] = mapped_column(JSON, default=list)
    bench: Mapped[list[int]] = mapped_column(JSON, default=list)

    league: Mapped["League"] = relationship(back_populates="lineups")

    __table_args__ = (UniqueConstraint("league_id", "manager_id", "matchday", name="uq_league_manager_matchday"),)
