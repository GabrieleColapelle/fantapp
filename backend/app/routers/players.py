from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.services.csv_import import parse_players_csv
from app.services.providers.fantacalcio_provider import ListoneFetchError, fetch_listone

router = APIRouter(prefix="/api/leagues/{league_id}/players", tags=["players"])


def _to_player_out(player: models.Player) -> schemas.PlayerOut:
    pick = player.pick
    return schemas.PlayerOut(
        id=player.id,
        name=player.name,
        role=player.role,
        team=player.team,
        quotation=player.quotation,
        tier=player.tier,
        status=player.status,
        is_taken=pick is not None,
        pick_id=pick.id if pick else None,
        manager_id=pick.manager_id if pick else None,
        price_paid=pick.price_paid if pick else None,
    )


def _get_league_or_404(league_id: int, db: Session) -> models.League:
    league = db.get(models.League, league_id)
    if not league:
        raise HTTPException(status_code=404, detail="Lega non trovata")
    return league


@router.get("", response_model=list[schemas.PlayerOut])
def list_players(
    league_id: int,
    role: str | None = None,
    team: str | None = None,
    available_only: bool = False,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    _get_league_or_404(league_id, db)
    query = db.query(models.Player).filter(models.Player.league_id == league_id)
    if role:
        query = query.filter(models.Player.role == role.upper())
    if team:
        query = query.filter(models.Player.team.ilike(f"%{team}%"))
    if search:
        query = query.filter(models.Player.name.ilike(f"%{search}%"))

    players = [_to_player_out(p) for p in query.order_by(models.Player.quotation.desc()).all()]
    if available_only:
        players = [p for p in players if not p.is_taken]
    return players


@router.post("", response_model=schemas.PlayerOut)
def add_player(league_id: int, payload: schemas.PlayerCreate, db: Session = Depends(get_db)):
    _get_league_or_404(league_id, db)
    player = models.Player(league_id=league_id, **payload.model_dump())
    db.add(player)
    db.commit()
    db.refresh(player)
    return _to_player_out(player)


@router.patch("/{player_id}/status", response_model=schemas.PlayerOut)
def update_player_status(
    league_id: int, player_id: int, payload: schemas.PlayerStatusUpdate, db: Session = Depends(get_db)
):
    player = db.get(models.Player, player_id)
    if not player or player.league_id != league_id:
        raise HTTPException(status_code=404, detail="Giocatore non trovato in questa lega")
    player.status = payload.status
    db.commit()
    db.refresh(player)
    return _to_player_out(player)


@router.post("/import-csv", response_model=schemas.CsvImportResult)
async def import_players_csv(league_id: int, file: UploadFile, db: Session = Depends(get_db)):
    _get_league_or_404(league_id, db)
    raw = await file.read()
    try:
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        content = raw.decode("latin-1")

    rows, errors = parse_players_csv(content)
    for row in rows:
        db.add(models.Player(league_id=league_id, **row))
    db.commit()

    return schemas.CsvImportResult(imported=len(rows), skipped=len(errors), errors=errors)


@router.post("/refresh-listone", response_model=schemas.ListoneRefreshResult)
def refresh_listone(league_id: int, db: Session = Depends(get_db)):
    _get_league_or_404(league_id, db)
    try:
        rows = fetch_listone()
    except ListoneFetchError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"{exc} — puoi comunque importare un CSV manualmente.",
        ) from exc

    existing_by_key = {
        (p.name.lower(), p.team.lower()): p
        for p in db.query(models.Player).filter(models.Player.league_id == league_id).all()
    }

    imported = 0
    updated = 0
    for row in rows:
        key = (row["name"].lower(), row["team"].lower())
        existing = existing_by_key.get(key)
        if existing:
            existing.role = row["role"]
            existing.quotation = row["quotation"]
            updated += 1
        else:
            db.add(models.Player(league_id=league_id, **row))
            imported += 1
    db.commit()

    return schemas.ListoneRefreshResult(imported=imported, updated=updated, errors=[])
