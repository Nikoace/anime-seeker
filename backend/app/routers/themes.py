from fastapi import APIRouter
import httpx
from app.models import AnimeTheme
from app.cache import themes_cache, bangumi_cache

router = APIRouter()
ANIMETHEMES_BASE = "https://api.animethemes.moe"
HEADERS = {"User-Agent": "anime-bt-aggregator/0.1"}


async def _get_bangumi_name(subject_id: int) -> str:
    key = f"detail:{subject_id}"
    if key in bangumi_cache:
        return bangumi_cache[key].name
    async with httpx.AsyncClient(headers=HEADERS, timeout=10) as client:
        resp = await client.get(f"https://api.bgm.tv/v0/subjects/{subject_id}")
        if resp.status_code == 200:
            return resp.json().get("name", "")
    return ""


@router.get("/{bangumi_id}", response_model=list[AnimeTheme])
async def get_themes(bangumi_id: int):
    cache_key = f"themes:{bangumi_id}"
    if cache_key in themes_cache:
        return themes_cache[cache_key]

    anime_name = await _get_bangumi_name(bangumi_id)
    if not anime_name:
        return []

    params = {
        "filter[name]": anime_name,
        "include": "animethemes.animethemeentries.videos,animethemes.song.artists",
        "fields[anime]": "name",
        "fields[animetheme]": "id,slug,type,sequence",
        "fields[song]": "title",
        "fields[artist]": "name",
        "fields[video]": "link",
    }
    async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
        resp = await client.get(f"{ANIMETHEMES_BASE}/anime", params=params)
        if resp.status_code != 200:
            return []
        raw = resp.json()

    themes: list[AnimeTheme] = []
    for anime in raw.get("anime", []):
        for theme in anime.get("animethemes", []):
            video_url = None
            entries = theme.get("animethemeentries", [])
            if entries and entries[0].get("videos"):
                video_url = entries[0]["videos"][0].get("link")

            song = theme.get("song", {})
            artists = song.get("artists", [])
            artist_name = artists[0]["name"] if artists else None

            themes.append(AnimeTheme(
                id=theme["id"],
                slug=theme["slug"],
                type=theme.get("type", "OP"),
                sequence=theme.get("sequence"),
                song_title=song.get("title", "Unknown"),
                artist=artist_name,
                video_url=video_url,
            ))

    themes_cache[cache_key] = themes
    return themes
