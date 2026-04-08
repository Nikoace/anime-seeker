import feedparser
import httpx
from typing import Optional
from app.models import Torrent, SourceError
from app.scrapers.base import extract_btih, build_magnet

NYAA_RSS = "https://nyaa.si/?page=rss&q={query}&c=1_0&f=0"
HEADERS = {"User-Agent": "anime-bt-aggregator/0.1"}


def parse_nyaa_item(item: dict) -> Optional[Torrent]:
    btih = item.get("nyaa_infohash") or extract_btih(item.get("link", ""))
    if not btih:
        return None
    btih = btih.lower()
    title = item.get("title", "")
    link = item.get("link", "")
    magnet = link if link.startswith("magnet:") else build_magnet(btih, title)
    return Torrent(
        title=title,
        magnet=magnet,
        size=item.get("nyaa_size"),
        date=item.get("published"),
        source="nyaa",
        btih=btih,
    )


async def fetch_nyaa(query: str) -> tuple[list[Torrent], Optional[SourceError]]:
    url = NYAA_RSS.format(query=query)
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=5) as client:
            resp = await client.get(url)
            resp.raise_for_status()
        feed = feedparser.parse(resp.text)
        torrents = [t for item in feed.entries if (t := parse_nyaa_item(item)) is not None]
        return torrents, None
    except Exception as e:
        return [], SourceError(source="nyaa", error=str(e))
