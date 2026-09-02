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


def _get_league_or_404(league_id: int, db: Session) -> models.League:
    league = db.get(models.League, league_id)
    if not league:
        raise HTTPException(status_code=404, detail="Lega non trovata")
    return league


def _clear_other_is_me(league_id: int, keep_manager_id: int | None, db: Session) -> None:
    """Keeps the "is_me" invariant: at most one manager per league is "me"."""
    others = db.query(models.Manager).filter(models.Manager.league_id == league_id)
    if keep_manager_id is not None:
        others = others.filter(models.Manager.id != keep_manager_id)
    others.update({models.Manager.is_me: False})


@router.post("/{league_id}/managers", response_model=schemas.ManagerOut)
def add_manager(league_id: int, payload: schemas.ManagerCreate, db: Session = Depends(get_db)):
    _get_league_or_404(league_id, db)
    manager = models.Manager(league_id=league_id, name=payload.name, is_me=payload.is_me)
    db.add(manager)
    db.flush()
    if payload.is_me:
        _clear_other_is_me(league_id, manager.id, db)
    db.commit()
    db.refresh(manager)
    return manager


@router.patch("/{league_id}/managers/{manager_id}", response_model=schemas.ManagerOut)
def update_manager(
    league_id: int, manager_id: int, payload: schemas.ManagerCreate, db: Session = Depends(get_db)
):
    manager = db.get(models.Manager, manager_id)
    if not manager or manager.league_id != league_id:
        raise HTTPException(status_code=404, detail="Manager non trovato in questa lega")
    manager.name = payload.name
    manager.is_me = payload.is_me
    if payload.is_me:
        _clear_other_is_me(league_id, manager.id, db)
    db.commit()
    db.refresh(manager)
    return manager


@router.delete("/{league_id}/managers/{manager_id}", status_code=204)
def delete_manager(league_id: int, manager_id: int, db: Session = Depends(get_db)):
    manager = db.get(models.Manager, manager_id)
    if not manager or manager.league_id != league_id:
        raise HTTPException(status_code=404, detail="Manager non trovato in questa lega")
    if manager.picks:
        raise HTTPException(
            status_code=409,
            detail="Questo manager ha già giocatori assegnati: rimuovili prima di eliminarlo.",
        )
    db.delete(manager)
    db.commit()
