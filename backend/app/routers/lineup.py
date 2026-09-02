from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.services.lineup_logic import FORMATIONS, compute_player_score, recommend_lineup
from app.services.stats_import import parse_fixtures_csv, parse_match_stats_csv

router = APIRouter(prefix="/api/leagues/{league_id}/lineup", tags=["lineup"])


def _get_league_or_404(league_id: int, db: Session) -> models.League:
    league = db.get(models.League, league_id)
    if not league:
        raise HTTPException(status_code=404, detail="Lega non trovata")
    return league


def _get_manager_or_404(league_id: int, manager_id: int, db: Session) -> models.Manager:
    manager = db.get(models.Manager, manager_id)
    if not manager or manager.league_id != league_id:
        raise HTTPException(status_code=404, detail="Manager non trovato in questa lega")
    return manager


@router.post("/match-stats", response_model=schemas.CsvImportResult)
def add_match_stat(league_id: int, payload: schemas.MatchStatCreate, db: Session = Depends(get_db)):
    _get_league_or_404(league_id, db)
    player = db.get(models.Player, payload.player_id)
    if not player or player.league_id != league_id:
        raise HTTPException(status_code=404, detail="Giocatore non trovato in questa lega")

    existing = (
        db.query(models.PlayerMatchStat)
        .filter_by(player_id=payload.player_id, matchday=payload.matchday)
        .first()
    )
    if existing:
        for field, value in payload.model_dump(exclude={"player_id"}).items():
            setattr(existing, field, value)
    else:
        db.add(models.PlayerMatchStat(**payload.model_dump()))
    db.commit()
    return schemas.CsvImportResult(imported=1, skipped=0, errors=[])


@router.post("/match-stats/import-csv", response_model=schemas.CsvImportResult)
async def import_match_stats_csv(league_id: int, file: UploadFile, db: Session = Depends(get_db)):
    _get_league_or_404(league_id, db)
    raw = await file.read()
    try:
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        content = raw.decode("latin-1")

    players = db.query(models.Player).filter(models.Player.league_id == league_id).all()
    player_ids_by_name = {p.name.lower(): p.id for p in players}

    rows, errors = parse_match_stats_csv(content, player_ids_by_name)
    for row in rows:
        existing = (
            db.query(models.PlayerMatchStat)
            .filter_by(player_id=row["player_id"], matchday=row["matchday"])
            .first()
        )
        if existing:
            for field, value in row.items():
                setattr(existing, field, value)
        else:
            db.add(models.PlayerMatchStat(**row))
    db.commit()

    return schemas.CsvImportResult(imported=len(rows), skipped=len(errors), errors=errors)


@router.post("/fixtures", response_model=schemas.FixtureOut)
def add_fixture(league_id: int, payload: schemas.FixtureCreate, db: Session = Depends(get_db)):
    _get_league_or_404(league_id, db)
    existing = (
        db.query(models.Fixture)
        .filter_by(league_id=league_id, matchday=payload.matchday, team=payload.team)
        .first()
    )
    if existing:
        existing.opponent = payload.opponent
        existing.home = payload.home
        fixture = existing
    else:
        fixture = models.Fixture(league_id=league_id, **payload.model_dump())
        db.add(fixture)
    db.commit()
    db.refresh(fixture)
    return fixture


@router.post("/fixtures/import-csv", response_model=schemas.CsvImportResult)
async def import_fixtures_csv(league_id: int, file: UploadFile, db: Session = Depends(get_db)):
    _get_league_or_404(league_id, db)
    raw = await file.read()
    try:
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        content = raw.decode("latin-1")

    rows, errors = parse_fixtures_csv(content)
    for row in rows:
        existing = (
            db.query(models.Fixture)
            .filter_by(league_id=league_id, matchday=row["matchday"], team=row["team"])
            .first()
        )
        if existing:
            existing.opponent = row["opponent"]
            existing.home = row["home"]
        else:
            db.add(models.Fixture(league_id=league_id, **row))
    db.commit()

    return schemas.CsvImportResult(imported=len(rows), skipped=len(errors), errors=errors)


@router.get("/fixtures", response_model=list[schemas.FixtureOut])
def list_fixtures(league_id: int, matchday: int, db: Session = Depends(get_db)):
    _get_league_or_404(league_id, db)
    return (
        db.query(models.Fixture)
        .filter(models.Fixture.league_id == league_id, models.Fixture.matchday == matchday)
        .all()
    )


def _score_player(player: models.Player, matchday: int, fixtures_by_team: dict[str, models.Fixture]) -> schemas.ScoredPlayer:
    stats = [
        {
            "matchday": s.matchday,
            "played": s.played,
            "vote": s.vote,
            "opponent": s.opponent,
            "home": s.home,
        }
        for s in sorted(player.match_stats, key=lambda s: s.matchday)
        if s.matchday < matchday
    ]
    fixture = fixtures_by_team.get(player.team)
    opponent = fixture.opponent if fixture else None
    home = fixture.home if fixture else None

    result = compute_player_score(stats, opponent, home, player.status)
    return schemas.ScoredPlayer(
        player_id=player.id,
        name=player.name,
        role=player.role,
        team=player.team,
        score=result.score,
        excluded_reason=result.excluded_reason,
        flags=result.flags,
        opponent=opponent,
        home=home,
    )


@router.get("/recommend", response_model=schemas.LineupRecommendation)
def recommend(league_id: int, manager_id: int, matchday: int, formation: str, db: Session = Depends(get_db)):
    _get_league_or_404(league_id, db)
    _get_manager_or_404(league_id, manager_id, db)
    if formation not in FORMATIONS:
        raise HTTPException(status_code=400, detail=f"Modulo '{formation}' non valido")

    owned_players = (
        db.query(models.Player)
        .join(models.AuctionPick, models.AuctionPick.player_id == models.Player.id)
        .filter(models.AuctionPick.manager_id == manager_id, models.AuctionPick.league_id == league_id)
        .all()
    )

    fixtures = db.query(models.Fixture).filter_by(league_id=league_id, matchday=matchday).all()
    fixtures_by_team = {f.team: f for f in fixtures}

    scored = [_score_player(p, matchday, fixtures_by_team) for p in owned_players]
    result = recommend_lineup([s.model_dump() for s in scored], formation)

    return schemas.LineupRecommendation(
        formation=formation,
        starters=[schemas.ScoredPlayer(**p) for p in result["starters"]],
        bench=[schemas.ScoredPlayer(**p) for p in result["bench"]],
        alternatives=[schemas.LineupAlternative(**a) for a in result["alternatives"]],
        excluded=[schemas.ScoredPlayer(**p) for p in result["excluded"]],
    )


@router.post("/save", response_model=schemas.LineupOut)
def save_lineup(league_id: int, payload: schemas.LineupSave, db: Session = Depends(get_db)):
    _get_league_or_404(league_id, db)
    _get_manager_or_404(league_id, payload.manager_id, db)
    if payload.formation not in FORMATIONS:
        raise HTTPException(status_code=400, detail=f"Modulo '{payload.formation}' non valido")

    existing = (
        db.query(models.Lineup)
        .filter_by(league_id=league_id, manager_id=payload.manager_id, matchday=payload.matchday)
        .first()
    )
    if existing:
        existing.formation = payload.formation
        existing.starters = payload.starters
        existing.bench = payload.bench
        lineup = existing
    else:
        lineup = models.Lineup(league_id=league_id, **payload.model_dump())
        db.add(lineup)
    db.commit()
    db.refresh(lineup)
    return lineup


@router.get("/saved", response_model=schemas.LineupOut | None)
def get_saved_lineup(league_id: int, manager_id: int, matchday: int, db: Session = Depends(get_db)):
    _get_league_or_404(league_id, db)
    return (
        db.query(models.Lineup)
        .filter_by(league_id=league_id, manager_id=manager_id, matchday=matchday)
        .first()
    )
