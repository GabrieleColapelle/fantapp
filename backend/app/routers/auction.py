from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.services.auction_logic import FASCE, classify_deal, role_gaps, suggest_players_by_fascia

router = APIRouter(prefix="/api/leagues/{league_id}/auction", tags=["auction"])


def _get_league_or_404(league_id: int, db: Session) -> models.League:
    league = db.get(models.League, league_id)
    if not league:
        raise HTTPException(status_code=404, detail="Lega non trovata")
    return league


@router.post("/picks", response_model=schemas.AuctionPickOut)
def create_pick(league_id: int, payload: schemas.AuctionPickCreate, db: Session = Depends(get_db)):
    _get_league_or_404(league_id, db)

    player = db.get(models.Player, payload.player_id)
    if not player or player.league_id != league_id:
        raise HTTPException(status_code=404, detail="Giocatore non trovato in questa lega")
    if player.pick is not None:
        raise HTTPException(status_code=409, detail="Giocatore già assegnato")

    manager = db.get(models.Manager, payload.manager_id)
    if not manager or manager.league_id != league_id:
        raise HTTPException(status_code=404, detail="Manager non trovato in questa lega")

    spent = sum(p.price_paid for p in manager.picks)
    remaining_budget = manager.league.budget_total - spent
    if payload.price_paid > remaining_budget:
        raise HTTPException(
            status_code=400,
            detail=f"Budget insufficiente: a {manager.name} restano {remaining_budget:g} crediti",
        )

    pick = models.AuctionPick(
        league_id=league_id,
        manager_id=payload.manager_id,
        player_id=payload.player_id,
        price_paid=payload.price_paid,
    )
    db.add(pick)
    db.commit()
    db.refresh(pick)

    deal = classify_deal(pick.price_paid, player.quotation)
    return schemas.AuctionPickOut(
        id=pick.id,
        player_id=pick.player_id,
        manager_id=pick.manager_id,
        price_paid=pick.price_paid,
        created_at=pick.created_at,
        deal_quality=schemas.DealQuality(label=deal.label, detail=deal.detail),
    )


@router.delete("/picks/{pick_id}", status_code=204)
def delete_pick(league_id: int, pick_id: int, db: Session = Depends(get_db)):
    pick = db.get(models.AuctionPick, pick_id)
    if not pick or pick.league_id != league_id:
        raise HTTPException(status_code=404, detail="Assegnazione non trovata")
    db.delete(pick)
    db.commit()


@router.get("/budgets", response_model=list[schemas.ManagerBudget])
def get_budgets(league_id: int, db: Session = Depends(get_db)):
    league = _get_league_or_404(league_id, db)
    result = []
    for manager in league.managers:
        spent = sum(p.price_paid for p in manager.picks)
        result.append(
            schemas.ManagerBudget(
                manager_id=manager.id,
                name=manager.name,
                is_me=manager.is_me,
                budget_total=league.budget_total,
                spent=spent,
                remaining=league.budget_total - spent,
                players_taken=len(manager.picks),
            )
        )
    return result


@router.get("/role-gaps", response_model=list[schemas.RoleGap])
def get_role_gaps(league_id: int, manager_id: int, db: Session = Depends(get_db)):
    league = _get_league_or_404(league_id, db)
    manager = db.get(models.Manager, manager_id)
    if not manager or manager.league_id != league_id:
        raise HTTPException(status_code=404, detail="Manager non trovato in questa lega")

    filled_by_role: dict[str, int] = {}
    for pick in manager.picks:
        filled_by_role[pick.player.role] = filled_by_role.get(pick.player.role, 0) + 1

    return role_gaps(league.roster_config, filled_by_role)


@router.get("/role-gaps/all", response_model=list[schemas.ManagerRoleGaps])
def get_all_role_gaps(league_id: int, db: Session = Depends(get_db)):
    league = _get_league_or_404(league_id, db)

    result = []
    for manager in league.managers:
        filled_by_role: dict[str, int] = {}
        for pick in manager.picks:
            filled_by_role[pick.player.role] = filled_by_role.get(pick.player.role, 0) + 1
        result.append(
            schemas.ManagerRoleGaps(
                manager_id=manager.id,
                name=manager.name,
                is_me=manager.is_me,
                gaps=role_gaps(league.roster_config, filled_by_role),
            )
        )
    return result


@router.get("/suggestions/all", response_model=list[schemas.RoleSuggestions])
def get_all_suggestions(league_id: int, manager_id: int, db: Session = Depends(get_db)):
    _get_league_or_404(league_id, db)
    manager = db.get(models.Manager, manager_id)
    if not manager or manager.league_id != league_id:
        raise HTTPException(status_code=404, detail="Manager non trovato in questa lega")

    spent = sum(p.price_paid for p in manager.picks)
    remaining_budget = manager.league.budget_total - spent

    available = db.query(models.Player).filter(models.Player.league_id == league_id).all()
    available_dicts = [
        {
            "player_id": p.id,
            "name": p.name,
            "team": p.team,
            "role": p.role,
            "quotation": p.quotation,
            "avg_auction_price": p.avg_auction_price,
            "starter_probability": p.starter_probability,
            "is_midfielder_bug": p.is_midfielder_bug,
        }
        for p in available
        if p.pick is None
    ]

    result = []
    for role in ("P", "D", "C", "A"):
        grouped = suggest_players_by_fascia(available_dicts, role, remaining_budget)
        result.append(
            schemas.RoleSuggestions(
                role=role,
                fasce=[
                    schemas.FasciaSuggestions(fascia=name, players=[schemas.SuggestedPlayer(**p) for p in grouped[name]])
                    for name, _, _ in FASCE
                ],
            )
        )
    return result
