from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
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

    league: Mapped["League"] = relationship(back_populates="players")
    pick: Mapped["AuctionPick | None"] = relationship(back_populates="player", uselist=False)


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
