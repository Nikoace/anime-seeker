from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import anime, themes, torrents

app = FastAPI(title="Anime BT Aggregator", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(anime.router, prefix="/api/anime", tags=["anime"])
app.include_router(themes.router, prefix="/api/themes", tags=["themes"])
app.include_router(torrents.router, prefix="/api/torrents", tags=["torrents"])


@app.get("/health")
def health():
    return {"status": "ok"}
