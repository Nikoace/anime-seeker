from fastapi import APIRouter, Query, HTTPException
import httpx
from app.models import AnimeSearchResult, AnimeDetail, MusicEntry
from app.cache import bangumi_cache

router = APIRouter()
BANGUMI_BASE = "https://api.bgm.tv"
HEADERS = {"User-Agent": "anime-bt-aggregator/0.1 (https://github.com/yourname/anime-bt-aggregator)"}


@router.get("/search", response_model=list[AnimeSearchResult])
async def search_anime(q: str = Query(..., min_length=1)):
    key = f"search:{q}"
    if key in bangumi_cache:
        return bangumi_cache[key]

    url = f"{BANGUMI_BASE}/search/subject/{q}"
    params = {"type": 2, "responseGroup": "small", "max_results": 20}
    async with httpx.AsyncClient(headers=HEADERS, timeout=10) as client:
        resp = await client.get(url, params=params)
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Bangumi API error")
        raw = resp.json()

    results = [
        AnimeSearchResult(
            id=item["id"],
            name=item.get("name", ""),
            name_cn=item.get("name_cn") or item.get("name", ""),
            image=item.get("images", {}).get("common", "").replace("http://", "https://", 1),
            air_date=item.get("air_date"),
            eps=item.get("eps"),
            rank=item.get("rank"),
        )
        for item in raw.get("list", [])
    ]
    bangumi_cache[key] = results
    return results


@router.get("/{subject_id}", response_model=AnimeDetail)
async def get_anime_detail(subject_id: int):
    key = f"detail:{subject_id}"
    if key in bangumi_cache:
        return bangumi_cache[key]

    url = f"{BANGUMI_BASE}/v0/subjects/{subject_id}"
    async with httpx.AsyncClient(headers=HEADERS, timeout=10) as client:
        resp = await client.get(url)
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Anime not found")
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Bangumi API error")
        raw = resp.json()

    result = AnimeDetail(
        id=raw["id"],
        name=raw.get("name", ""),
        name_cn=raw.get("name_cn") or raw.get("name", ""),
        summary=raw.get("summary", ""),
        image=raw.get("images", {}).get("common", "").replace("http://", "https://", 1),
        tags=raw.get("tags", []),
        rating=raw.get("rating"),
        air_date=raw.get("date"),
        eps=raw.get("eps"),
    )
    bangumi_cache[key] = result
    return result


@router.get("/{subject_id}/music", response_model=list[MusicEntry])
async def get_anime_music(subject_id: int):
    key = f"music:{subject_id}"
    if key in bangumi_cache:
        return bangumi_cache[key]

    url = f"{BANGUMI_BASE}/v0/subjects/{subject_id}/subjects"
    async with httpx.AsyncClient(headers=HEADERS, timeout=10) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            return []
        raw = resp.json()

    music = [
        MusicEntry(
            id=item["id"],
            name=item.get("name", ""),
            name_cn=item.get("name_cn") or item.get("name", ""),
            image=item.get("images", {}).get("common", "").replace("http://", "https://", 1),
        )
        for item in raw
        if item.get("type") == 3
    ]
    bangumi_cache[key] = music
    return music
