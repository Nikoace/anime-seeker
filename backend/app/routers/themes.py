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

    # 逐个尝试候选名称，直到找到匹配
    raw_anime = []
    async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
        for name in candidates:
            resp = await client.get(
                f"{ANIMETHEMES_BASE}/anime",
                params={
                    "filter[name]": name,
                    "include": "animethemes.animethemeentries.videos,animethemes.song.artists",
                    "fields[anime]": "name",
                    "fields[animetheme]": "id,slug,type,sequence",
                    "fields[song]": "title",
                    "fields[artist]": "name",
                    "fields[video]": "link",
                },
            )
            if resp.status_code == 200:
                result = resp.json().get("anime", [])
                if result:
                    raw_anime = result
                    break

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
