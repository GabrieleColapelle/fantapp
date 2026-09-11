from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.services.providers.team_formations_provider import TeamFormationsFetchError, fetch_team_formations

router = APIRouter(prefix="/api/leagues/{league_id}/team-formations", tags=["team-formations"])


def _get_league_or_404(league_id: int, db: Session) -> models.League:
    league = db.get(models.League, league_id)
    if not league:
        raise HTTPException(status_code=404, detail="Lega non trovata")
    return league


@router.get("", response_model=list[schemas.TeamFormationOut])
def list_team_formations(league_id: int, db: Session = Depends(get_db)):
    _get_league_or_404(league_id, db)
    formations = (
        db.query(models.TeamFormation)
        .filter(models.TeamFormation.league_id == league_id)
        .order_by(models.TeamFormation.team)
        .all()
    )

    badge_by_team: dict[str, str] = {}
    for p in db.query(models.Player).filter(models.Player.league_id == league_id, models.Player.team_badge_url != "").all():
        badge_by_team.setdefault(p.team, p.team_badge_url)

    return [
        schemas.TeamFormationOut(
            team=f.team,
            image_url=f.image_url,
            coach=f.coach,
            formation_module=f.formation_module,
            starting_eleven=f.starting_eleven,
            ballottaggi=f.ballottaggi,
            penalty_takers=f.penalty_takers,
            free_kick_takers=f.free_kick_takers,
            team_badge_url=badge_by_team.get(f.team, ""),
        )
        for f in formations
    ]


@router.post("/refresh", response_model=schemas.TeamFormationsRefreshResult)
def refresh_team_formations(league_id: int, db: Session = Depends(get_db)):
    _get_league_or_404(league_id, db)
    try:
        rows = fetch_team_formations()
    except TeamFormationsFetchError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    existing_by_team = {
        f.team: f
        for f in db.query(models.TeamFormation).filter(models.TeamFormation.league_id == league_id).all()
    }
    for row in rows:
        existing = existing_by_team.get(row["team"])
        if existing:
            existing.image_url = row["image_url"]
            existing.coach = row["coach"]
            existing.formation_module = row["formation_module"]
            existing.starting_eleven = row["starting_eleven"]
            existing.ballottaggi = row["ballottaggi"]
            existing.penalty_takers = row["penalty_takers"]
            existing.free_kick_takers = row["free_kick_takers"]
        else:
            db.add(models.TeamFormation(league_id=league_id, **row))
    db.commit()

    return schemas.TeamFormationsRefreshResult(updated=len(rows), errors=[])
