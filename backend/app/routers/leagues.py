from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.models import DEFAULT_ROSTER_CONFIG

router = APIRouter(prefix="/api/leagues", tags=["leagues"])


@router.post("", response_model=schemas.LeagueOut)
def create_league(payload: schemas.LeagueCreate, db: Session = Depends(get_db)):
    league = models.League(
        name=payload.name,
        ruleset=payload.ruleset,
        budget_total=payload.budget_total,
        roster_config=payload.roster_config or dict(DEFAULT_ROSTER_CONFIG),
    )
    league.managers = [
        models.Manager(name=m.name, is_me=m.is_me) for m in payload.managers
    ]
    db.add(league)
    db.commit()
    db.refresh(league)
    return league


@router.get("", response_model=list[schemas.LeagueOut])
def list_leagues(db: Session = Depends(get_db)):
    return db.query(models.League).all()


@router.get("/{league_id}", response_model=schemas.LeagueOut)
def get_league(league_id: int, db: Session = Depends(get_db)):
    league = db.get(models.League, league_id)
    if not league:
        raise HTTPException(status_code=404, detail="Lega non trovata")
    return league
