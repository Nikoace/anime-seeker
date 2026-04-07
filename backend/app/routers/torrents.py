import asyncio
from fastapi import APIRouter
import httpx
from app.models import TorrentsResponse, SourceError
from app.scrapers.nyaa import fetch_nyaa
from app.scrapers.acgrip import fetch_acgrip
from app.scrapers.dmhy import fetch_dmhy
from app.scrapers.mikan import fetch_mikan
from app.cache import torrents_cache, bangumi_cache

router = APIRouter()
HEADERS = {"User-Agent": "anime-bt-aggregator/0.1"}


async def _get_anime_name(bangumi_id: int) -> str:
    key = f"detail:{bangumi_id}"
    if key in bangumi_cache:
        cached = bangumi_cache[key]
        return cached.name_cn or cached.name
    async with httpx.AsyncClient(headers=HEADERS, timeout=10) as client:
        resp = await client.get(f"https://api.bgm.tv/v0/subjects/{bangumi_id}")
        if resp.status_code == 200:
            data = resp.json()
            return data.get("name_cn") or data.get("name", "")
    return ""


@router.get("/{bangumi_id}", response_model=TorrentsResponse)
async def get_torrents(bangumi_id: int):
    cache_key = f"torrents:{bangumi_id}"
    if cache_key in torrents_cache:
        return torrents_cache[cache_key]

    query = await _get_anime_name(bangumi_id)
    if not query:
        return TorrentsResponse(torrents=[], errors=[SourceError(source="all", error="Anime not found")])

    results = await asyncio.gather(
        fetch_nyaa(query),
        fetch_acgrip(bangumi_id),
        fetch_dmhy(query),
        fetch_mikan(query),
    )

    all_torrents = []
    errors = []
    for torrents, error in results:
        all_torrents.extend(torrents)
        if error:
            errors.append(error)

    all_torrents.sort(key=lambda t: t.date or "", reverse=True)
    response = TorrentsResponse.deduplicated(all_torrents, errors)
    torrents_cache[cache_key] = response
    return response
