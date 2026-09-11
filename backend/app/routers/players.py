from datetime import date

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session, selectinload

from app import models, schemas
from app.database import get_db
from app.services.csv_import import parse_players_csv
from app.services.player_matching import (
    match_avg_prices,
    match_injuries,
    match_probable_lineups,
    match_season_stats,
    match_set_piece_takers,
)
from app.services.player_stats import recent_form_fantavoto
from app.services.providers.fantacalcio_online_provider import (
    AveragePriceFetchError,
    fetch_average_prices,
    select_price_column,
)
from app.services.providers.fantacalcio_provider import ListoneFetchError, fetch_listone
from app.services.providers.injuries_provider import (
    InjuriesFetchError,
    estimate_date_from_matchday,
    fetch_injuries,
    fetch_recovery_matchdays,
)
from app.services.providers.penalty_takers_provider import PenaltyTakersFetchError, fetch_set_piece_takers
from app.services.providers.probable_lineups_provider import LineupsFetchError, fetch_probable_lineups
from app.services.providers.season_stats_provider import SeasonStatsFetchError, fetch_season_stats
from app.services.providers.team_badges_provider import TeamBadgesFetchError, fetch_team_badges

router = APIRouter(prefix="/api/leagues/{league_id}/players", tags=["players"])


def _to_player_out(player: models.Player) -> schemas.PlayerOut:
    pick = player.pick
    match_stat_dicts = [{"matchday": s.matchday, "played": s.played, "vote": s.vote} for s in player.match_stats]
    return schemas.PlayerOut(
        id=player.id,
        name=player.name,
        role=player.role,
        team=player.team,
        quotation=player.quotation,
        avg_auction_price=player.avg_auction_price,
        starter_probability=player.starter_probability,
        mantra_role=player.mantra_role,
        is_midfielder_bug=player.is_midfielder_bug,
        penalty_rank=player.penalty_rank,
        free_kick_rank=player.free_kick_rank,
        last_season_matches=player.last_season_matches,
        last_season_avg_vote=player.last_season_avg_vote,
        last_season_avg_fantavoto=player.last_season_avg_fantavoto,
        injury_description=player.injury_description,
        injury_expected_return_date=player.injury_expected_return_date,
        team_badge_url=player.team_badge_url,
        recent_form_fantavoto=recent_form_fantavoto(match_stat_dicts),
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
    query = db.query(models.Player).options(selectinload(models.Player.match_stats)).filter(
        models.Player.league_id == league_id
    )
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
            existing.mantra_role = row["mantra_role"]
            existing.is_midfielder_bug = row["is_midfielder_bug"]
            updated += 1
        else:
            db.add(models.Player(league_id=league_id, **row))
            imported += 1
    db.commit()

    return schemas.ListoneRefreshResult(imported=imported, updated=updated, errors=[])


@router.post("/refresh-avg-prices", response_model=schemas.AvgPriceRefreshResult)
def refresh_avg_prices(league_id: int, db: Session = Depends(get_db)):
    league = _get_league_or_404(league_id, db)
    try:
        rows = fetch_average_prices()
    except AveragePriceFetchError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    column = select_price_column(participants=len(league.managers), budget=league.budget_total)

    league_players = db.query(models.Player).filter(models.Player.league_id == league_id).all()
    player_dicts = [{"id": p.id, "name": p.name, "team": p.team, "role": p.role} for p in league_players]
    players_by_id = {p.id: p for p in league_players}

    result = match_avg_prices(player_dicts, rows, column)
    for player_id, price in result.matched.items():
        players_by_id[player_id].avg_auction_price = price
    db.commit()

    return schemas.AvgPriceRefreshResult(updated=len(result.matched), unmatched=result.unmatched, errors=[])


@router.post("/refresh-lineups", response_model=schemas.LineupsRefreshResult)
def refresh_lineups(league_id: int, db: Session = Depends(get_db)):
    _get_league_or_404(league_id, db)
    try:
        lineups = fetch_probable_lineups()
    except LineupsFetchError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    league_players = db.query(models.Player).filter(models.Player.league_id == league_id).all()
    player_dicts = [{"id": p.id, "name": p.name, "team": p.team, "role": p.role} for p in league_players]
    players_by_id = {p.id: p for p in league_players}

    result = match_probable_lineups(player_dicts, lineups)
    for player_id, probability in result.starter_probability.items():
        players_by_id[player_id].starter_probability = probability
    for player_id, status in result.status.items():
        players_by_id[player_id].status = status
    db.commit()

    return schemas.LineupsRefreshResult(
        starters_updated=len(result.starter_probability),
        status_updated=len(result.status),
        unmatched=result.unmatched,
        errors=[],
    )


@router.post("/refresh-set-piece-takers", response_model=schemas.SetPieceTakersRefreshResult)
def refresh_set_piece_takers(league_id: int, db: Session = Depends(get_db)):
    _get_league_or_404(league_id, db)
    try:
        data = fetch_set_piece_takers()
    except PenaltyTakersFetchError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    league_players = db.query(models.Player).filter(models.Player.league_id == league_id).all()
    player_dicts = [{"id": p.id, "name": p.name, "team": p.team} for p in league_players]
    players_by_id = {p.id: p for p in league_players}

    # Reset ranks first: a player who lost the role (e.g. a new signing
    # took over) must stop showing a stale rank instead of keeping it
    # forever once matched once.
    for p in league_players:
        p.penalty_rank = None
        p.free_kick_rank = None

    result = match_set_piece_takers(player_dicts, data)
    for player_id, rank in result.penalty_rank.items():
        players_by_id[player_id].penalty_rank = rank
    for player_id, rank in result.free_kick_rank.items():
        players_by_id[player_id].free_kick_rank = rank
    db.commit()

    return schemas.SetPieceTakersRefreshResult(
        penalty_takers_updated=len(result.penalty_rank),
        free_kick_takers_updated=len(result.free_kick_rank),
        unmatched=result.unmatched,
        errors=[],
    )


def _last_completed_season() -> str:
    """The most recently finished Serie A season in "YYYY-YY" form. The
    season in progress runs July through June, so the last completed one
    started two calendar years ago if we're before July, one year ago
    otherwise."""
    today = date.today()
    current_start_year = today.year if today.month >= 7 else today.year - 1
    last_start_year = current_start_year - 1
    return f"{last_start_year}-{str(last_start_year + 1)[2:]}"


@router.post("/refresh-season-stats", response_model=schemas.SeasonStatsRefreshResult)
def refresh_season_stats(league_id: int, season: str | None = None, db: Session = Depends(get_db)):
    _get_league_or_404(league_id, db)
    season = season or _last_completed_season()
    try:
        rows = fetch_season_stats(season)
    except SeasonStatsFetchError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    league_players = db.query(models.Player).filter(models.Player.league_id == league_id).all()
    player_dicts = [{"id": p.id, "name": p.name, "team": p.team, "role": p.role} for p in league_players]
    players_by_id = {p.id: p for p in league_players}

    result = match_season_stats(player_dicts, rows)
    for player_id, data in result.matched.items():
        players_by_id[player_id].last_season_matches = data["matches_played"]
        players_by_id[player_id].last_season_avg_vote = data["avg_vote"]
        players_by_id[player_id].last_season_avg_fantavoto = data["avg_fantavoto"]
    db.commit()

    return schemas.SeasonStatsRefreshResult(
        season=season, updated=len(result.matched), unmatched=result.unmatched, errors=[]
    )


@router.post("/refresh-injuries", response_model=schemas.InjuriesRefreshResult)
def refresh_injuries(league_id: int, db: Session = Depends(get_db)):
    _get_league_or_404(league_id, db)
    try:
        rows = fetch_injuries()
    except InjuriesFetchError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    # Second source, used only to fill in a return-date estimate when the
    # first source's free text didn't parse into one — its own failure
    # shouldn't block the (more important) primary data from Fantacalcio.it.
    try:
        recovery_matchdays = fetch_recovery_matchdays()
    except InjuriesFetchError:
        recovery_matchdays = {}
    recovery_matchdays_folded = {name.strip().lower(): matchday for name, matchday in recovery_matchdays.items()}

    league_players = db.query(models.Player).filter(models.Player.league_id == league_id).all()
    player_dicts = [{"id": p.id, "name": p.name, "team": p.team, "role": p.role} for p in league_players]
    players_by_id = {p.id: p for p in league_players}

    # Reset first: a player who recovered since the last refresh must stop
    # showing a stale flag instead of keeping it forever once matched once.
    for p in league_players:
        p.injury_description = ""
        p.injury_expected_return_date = None

    result = match_injuries(player_dicts, rows)
    today = date.today()
    for player_id, data in result.matched.items():
        player = players_by_id[player_id]
        expected_return_date = data["expected_return_date"]
        if expected_return_date is None:
            matchday = recovery_matchdays_folded.get(player.name.strip().lower())
            if matchday is not None:
                expected_return_date = estimate_date_from_matchday(matchday, today)

        player.injury_description = data["description"]
        player.injury_expected_return_date = expected_return_date
    db.commit()

    return schemas.InjuriesRefreshResult(updated=len(result.matched), unmatched=result.unmatched, errors=[])


@router.post("/refresh-team-badges", response_model=schemas.TeamBadgesRefreshResult)
def refresh_team_badges(league_id: int, db: Session = Depends(get_db)):
    _get_league_or_404(league_id, db)
    try:
        badges = fetch_team_badges()
    except TeamBadgesFetchError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    league_players = db.query(models.Player).filter(models.Player.league_id == league_id).all()
    updated = 0
    for p in league_players:
        badge_url = badges.get(p.team)
        if badge_url:
            p.team_badge_url = badge_url
            updated += 1
    db.commit()

    return schemas.TeamBadgesRefreshResult(updated=updated, errors=[])
