from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine, sync_schema
from app.routers import auction, leagues, lineup, players, team_formations

Base.metadata.create_all(bind=engine)
sync_schema()

app = FastAPI(title="Fantapp API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(leagues.router)
app.include_router(players.router)
app.include_router(auction.router)
app.include_router(lineup.router)
app.include_router(team_formations.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
