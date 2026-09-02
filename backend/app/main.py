from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import auction, leagues, lineup, players

Base.metadata.create_all(bind=engine)

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


@app.get("/api/health")
def health():
    return {"status": "ok"}
