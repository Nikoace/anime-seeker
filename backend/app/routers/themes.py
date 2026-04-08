import asyncio
from fastapi import APIRouter
import httpx
from app.models import AnimeTheme
from app.cache import themes_cache, bangumi_cache

router = APIRouter()
ANIMETHEMES_BASE = "https://api.animethemes.moe"
HEADERS = {"User-Agent": "anime-bt-aggregator/0.1"}


def _extract_ascii_aliases(infobox: list) -> list[str]:
    """从 Bangumi infobox 别名中提取所有 ASCII 别名（英文/罗马字）"""
    for item in infobox:
        if item.get("key") == "别名":
            aliases = item.get("value", [])
            if isinstance(aliases, list):
                return [a.get("v", "") for a in aliases if a.get("v", "").isascii() and a.get("v", "")]
    return []


async def _get_bangumi_names(subject_id: int) -> tuple[str, list[str]]:
    """返回 (日文名, ASCII别名列表)"""
    key = f"detail:{subject_id}"
    if key in bangumi_cache:
        return bangumi_cache[key].name, []
    async with httpx.AsyncClient(headers=HEADERS, timeout=10) as client:
        resp = await client.get(f"https://api.bgm.tv/v0/subjects/{subject_id}")
        if resp.status_code == 200:
            raw = resp.json()
            return raw.get("name", ""), _extract_ascii_aliases(raw.get("infobox", []))
    return "", []


@router.get("/{bangumi_id}", response_model=list[AnimeTheme])
async def get_themes(bangumi_id: int):
    cache_key = f"themes:{bangumi_id}"
    if cache_key in themes_cache:
        return themes_cache[cache_key]

    jp_name, ascii_aliases = await _get_bangumi_names(bangumi_id)
    candidates = ascii_aliases + ([jp_name] if jp_name else [])
    if not candidates:
        return []

    # 并行搜索所有候选名称，取第一个有结果的
    PARAMS = {
        "include": "animethemes.animethemeentries.videos,animethemes.song.artists",
        "fields[anime]": "name",
        "fields[animetheme]": "id,slug,type,sequence",
        "fields[song]": "title",
        "fields[artist]": "name",
        "fields[video]": "link",
    }

    async def _search_one(client: httpx.AsyncClient, name: str) -> list:
        resp = await client.get(
            f"{ANIMETHEMES_BASE}/anime",
            params={"filter[name]": name, **PARAMS},
        )
        if resp.status_code == 200:
            return resp.json().get("anime", [])
        return []

    async with httpx.AsyncClient(headers=HEADERS, timeout=10) as client:
        search_results = await asyncio.gather(*[_search_one(client, name) for name in candidates])
    raw_anime = next((r for r in search_results if r), [])

    themes: list[AnimeTheme] = []
    for anime in raw_anime:
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
